"""
OpenMOSS 任务调度中间件 — 主入口
"""
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import config
from app.auth.dependencies import get_current_agent
from app.routers import (
    admin,
    admin_agents,
    admin_config,
    admin_dashboard,
    admin_logs,
    admin_reviews,
    admin_scores,
    admin_tasks,
    agents,
    feed,
    logs,
    prompts,
    review_records,
    rules,
    scores,
    setup,
    sub_tasks,
    tasks,
    tools,
)
from app.middleware.request_logger import RequestLoggerMiddleware


def _cleanup_old_request_logs():
    """启动时清理过期的请求日志"""
    from datetime import datetime, timedelta
    from app.database import SessionLocal
    from app.models.request_log import RequestLog

    days = config.feed_retention_days
    cutoff = datetime.now() - timedelta(days=days)

    db = SessionLocal()
    try:
        deleted = db.query(RequestLog).filter(RequestLog.timestamp < cutoff).delete()
        db.commit()
        if deleted > 0:
            print(f"[RequestLog] 已清理 {deleted} 条超过 {days} 天的请求日志")
    except Exception as e:
        print(f"[RequestLog] 清理失败: {e}")
    finally:
        db.close()


def _init_agent_trigger():
    """初始化 Agent 事件驱动唤醒（延迟 15 秒等 Gateway 就绪）"""
    import threading
    def _delayed_init():
        import time
        time.sleep(15)
        from app.services import agent_trigger
        agent_trigger.init()
    threading.Thread(target=_delayed_init, daemon=True).start()


def _start_watchdog():
    """启动看门狗守护线程（内联巡检逻辑，避免导入冲突）"""
    import threading

    def _watchdog_loop():
        import time
        import uuid as _uuid
        from datetime import datetime, timedelta
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        TIMEOUT_WARNING = 60
        TIMEOUT_CRITICAL = 120
        STUCK_THRESHOLD = 120
        REWORK_MAX = 3

        time.sleep(30)
        print("[Watchdog] 看门狗线程启动 (间隔=300s)")

        db_path = config.database_path
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        WSession = sessionmaker(bind=engine)

        while True:
            try:
                db = WSession()
                now = datetime.now()
                actions = []

                # 超时检测
                rows = db.execute(text(
                    "SELECT id, name, assigned_agent, updated_at FROM sub_task WHERE status = 'in_progress'"
                )).fetchall()
                for sid, name, agent, updated_at in rows:
                    if not updated_at:
                        continue
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at)
                    minutes = (now - updated_at).total_seconds() / 60
                    if minutes >= TIMEOUT_CRITICAL:
                        db.execute(text(
                            "UPDATE sub_task SET status = 'blocked', current_session_id = NULL, updated_at = :now WHERE id = :id"
                        ), {"id": sid, "now": now})
                        db.execute(text(
                            "INSERT INTO patrol_record (id, type, severity, sub_task_id, agent_id, description, action_taken, status, created_at) "
                            "VALUES (:id, 'timeout', 'critical', :sid, :agent, :desc, 'auto_blocked', 'open', :now)"
                        ), {"id": str(_uuid.uuid4()), "sid": sid, "agent": agent,
                            "desc": f"子任务「{name}」超时 {int(minutes)}min → auto blocked", "now": now})
                        actions.append(f"CRITICAL: 「{name}」超时 {int(minutes)}min → blocked")
                    elif minutes >= TIMEOUT_WARNING:
                        existing = db.execute(text(
                            "SELECT id FROM patrol_record WHERE sub_task_id = :sid AND type = 'timeout' AND status = 'open'"
                        ), {"sid": sid}).fetchone()
                        if not existing:
                            db.execute(text(
                                "INSERT INTO patrol_record (id, type, severity, sub_task_id, agent_id, description, action_taken, status, created_at) "
                                "VALUES (:id, 'timeout', 'warning', :sid, :agent, :desc, '', 'open', :now)"
                            ), {"id": str(_uuid.uuid4()), "sid": sid, "agent": agent,
                                "desc": f"子任务「{name}」执行中 {int(minutes)}min", "now": now})
                            actions.append(f"WARNING: 「{name}」执行中 {int(minutes)}min")

                # 卡住检测
                rows = db.execute(text(
                    "SELECT id, name, status, assigned_agent, updated_at FROM sub_task "
                    "WHERE status NOT IN ('done', 'cancelled', 'in_progress', 'blocked')"
                )).fetchall()
                for sid, name, status, agent, updated_at in rows:
                    if not updated_at:
                        continue
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at)
                    minutes = (now - updated_at).total_seconds() / 60
                    if minutes >= STUCK_THRESHOLD:
                        existing = db.execute(text(
                            "SELECT id FROM patrol_record WHERE sub_task_id = :sid AND type = 'stuck' AND status = 'open'"
                        ), {"sid": sid}).fetchone()
                        if not existing:
                            db.execute(text(
                                "INSERT INTO patrol_record (id, type, severity, sub_task_id, agent_id, description, action_taken, status, created_at) "
                                "VALUES (:id, 'stuck', 'warning', :sid, :agent, :desc, '', 'open', :now)"
                            ), {"id": str(_uuid.uuid4()), "sid": sid, "agent": agent,
                                "desc": f"子任务「{name}」({status}) 卡住 {int(minutes)}min", "now": now})
                            actions.append(f"WARNING: 「{name}」({status}) 卡住 {int(minutes)}min")

                # 返工溢出
                rows = db.execute(text(
                    "SELECT id, name, assigned_agent, rework_count FROM sub_task "
                    "WHERE rework_count >= :max AND status NOT IN ('done', 'cancelled')"
                ), {"max": REWORK_MAX}).fetchall()
                for sid, name, agent, rework_count in rows:
                    existing = db.execute(text(
                        "SELECT id FROM patrol_record WHERE sub_task_id = :sid AND type = 'rework_overflow' AND status = 'open'"
                    ), {"sid": sid}).fetchone()
                    if not existing:
                        db.execute(text(
                            "INSERT INTO patrol_record (id, type, severity, sub_task_id, agent_id, description, action_taken, status, created_at) "
                            "VALUES (:id, 'rework_overflow', 'warning', :sid, :agent, :desc, '', 'open', :now)"
                        ), {"id": str(_uuid.uuid4()), "sid": sid, "agent": agent,
                            "desc": f"子任务「{name}」返工 {rework_count} 次", "now": now})
                        actions.append(f"WARNING: 「{name}」返工 {rework_count} 次")

                # 闭环
                open_records = db.execute(text(
                    "SELECT pr.id, pr.sub_task_id, st.status FROM patrol_record pr "
                    "JOIN sub_task st ON pr.sub_task_id = st.id WHERE pr.status = 'open'"
                )).fetchall()
                for record_id, sid, current_status in open_records:
                    if current_status in ('done', 'cancelled'):
                        db.execute(text(
                            "UPDATE patrol_record SET status = 'resolved', resolved_at = :now WHERE id = :id"
                        ), {"id": record_id, "now": now})

                db.commit()
                db.close()

                if actions:
                    for a in actions:
                        print(f"[Watchdog] {a}")
                else:
                    print("[Watchdog] 巡检正常")
            except Exception as e:
                print(f"[Watchdog] 巡检异常: {e}")
            time.sleep(300)

    t = threading.Thread(target=_watchdog_loop, daemon=True, name="watchdog")
    t.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    init_db()

    # 清理过期请求日志
    _cleanup_old_request_logs()

    # 启动看门狗守护线程
    _start_watchdog()
    # 启动 Agent 事件驱动唤醒
    _init_agent_trigger()

    print(f"[{config.project_name}] 服务启动 → http://{config.server_host}:{config.server_port}")
    print(f"[{config.project_name}] 数据库: {config.database_path}")
    print(f"[{config.project_name}] 工作目录: {config.workspace_root}")
    print(f"[{config.project_name}] 注册令牌: {config.registration_token}")
    yield
    print(f"[{config.project_name}] 服务关闭")


app = FastAPI(
    title=f"{config.project_name} 任务调度中间件",
    description="基于 OpenClaw 的自组织自协作自进化多 Agent 作业平台",
    version="1.0.0",
    lifespan=lifespan,
)

# 请求日志中间件（记录 Agent API 调用）
app.add_middleware(RequestLoggerMiddleware)

# CORS 跨域支持（前后端分离部署时需要，必须在最外层）
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 全局异常处理
# ============================================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """业务逻辑错误 → 400"""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """未处理异常 → 500，日志记录堆栈，客户端只看到通用提示"""
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "服务内部错误，请联系管理员"},
    )


@app.get("/api/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": config.project_name, "version": "1.0.0"}


@app.get("/api/config/notification", tags=["Config"])
async def get_notification_config(agent=Depends(get_current_agent)):
    """Agent 获取通知渠道配置（往哪里发通知）"""
    notification = config.notification_config
    return {
        "enabled": notification.get("enabled", False),
        "channels": notification.get("channels", []),
        "events": notification.get("events", []),
    }


# 注册路由（统一 /api 前缀）
API_PREFIX = "/api"
app.include_router(agents.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(admin_agents.router, prefix=API_PREFIX)
app.include_router(admin_config.router, prefix=API_PREFIX)
app.include_router(admin_dashboard.router, prefix=API_PREFIX)
app.include_router(admin_logs.router, prefix=API_PREFIX)
app.include_router(admin_reviews.router, prefix=API_PREFIX)
app.include_router(admin_scores.router, prefix=API_PREFIX)
app.include_router(admin_tasks.router, prefix=API_PREFIX)
app.include_router(tasks.router, prefix=API_PREFIX)
app.include_router(sub_tasks.router, prefix=API_PREFIX)
app.include_router(rules.router, prefix=API_PREFIX)
app.include_router(review_records.router, prefix=API_PREFIX)
app.include_router(scores.router, prefix=API_PREFIX)
app.include_router(logs.router, prefix=API_PREFIX)
app.include_router(feed.router, prefix=API_PREFIX)
app.include_router(prompts.router, prefix=API_PREFIX)
app.include_router(tools.router, prefix=API_PREFIX)
app.include_router(setup.router, prefix=API_PREFIX)


# ============================================================
# WebUI 静态文件服务（当 static/ 目录存在时自动启用）
# ============================================================

_webui_dist = os.path.join(os.path.dirname(__file__), "..", "static")

if os.path.isdir(_webui_dist):
    # 挂载静态资源（JS/CSS/图片等）
    _assets_dir = os.path.join(_webui_dist, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="webui-assets")

    # 所有未匹配路径 → 返回 index.html（SPA 前端路由）
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = os.path.join(_webui_dist, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return JSONResponse(status_code=404, content={"detail": "WebUI not found"})

    print(f"[WebUI] 已挂载前端: {os.path.abspath(_webui_dist)}")

