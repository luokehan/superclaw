"""
Agent 事件驱动唤醒 — 任务状态变更时立即触发对应 Agent
通过 openclaw cron run 唤醒，避免空转等待 cron 轮询
"""
import subprocess
import threading
import logging

logger = logging.getLogger("agent_trigger")

def _log(msg):
    print(f"[AgentTrigger] {msg}")
    logger.info(msg)

# Cron Job ID 映射（启动时从 openclaw cron list 获取）
CRON_JOBS = {}


def _load_cron_jobs():
    """从 openclaw cron list 解析 Job ID"""
    global CRON_JOBS
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            jobs = data.get("jobs", data) if isinstance(data, dict) else data
            if isinstance(jobs, list):
                for job in jobs:
                    agent_id = job.get("agentId", "")
                    job_id = job.get("id", "")
                    if agent_id and job_id:
                        CRON_JOBS[agent_id] = job_id
                        _log(f"Mapped agent {agent_id} -> cron job {job_id}")
    except Exception as e:
        _log(f"Failed to load cron jobs: {e}")
        # Fallback: try plain text parsing
        try:
            result = subprocess.run(
                ["openclaw", "cron", "list"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 8:
                    job_id = parts[0]
                    # Find agent id column
                    for i, p in enumerate(parts):
                        if p in ("main", "executor", "reviewer", "patrol"):
                            CRON_JOBS[p] = job_id
                            break
        except Exception:
            pass


def _trigger_agent(agent_id: str, reason: str):
    """后台线程触发 Agent 唤醒"""
    job_id = CRON_JOBS.get(agent_id)
    if not job_id:
        _log(f"No cron job found for agent {agent_id}, skipping trigger")
        return

    try:
        result = subprocess.run(
            ["openclaw", "cron", "run", job_id],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            _log(f"Triggered {agent_id} (job {job_id[:8]}): {reason}")
        else:
            _log(f"Failed to trigger {agent_id}: {result.stderr[:200]}")
    except Exception as e:
        _log(f"Error triggering {agent_id}: {e}")


def trigger_agent_async(agent_id: str, reason: str):
    """异步触发 Agent（不阻塞 API 响应）"""
    t = threading.Thread(target=_trigger_agent, args=(agent_id, reason), daemon=True)
    t.start()


# === 事件钩子 ===

def on_subtask_assigned(sub_task_id: str):
    """子任务被分配给执行者 → 唤醒执行者"""
    trigger_agent_async("executor", f"New subtask assigned: {sub_task_id}")


def on_subtask_submitted(sub_task_id: str):
    """子任务提交审查 → 唤醒审查官"""
    trigger_agent_async("reviewer", f"Subtask submitted for review: {sub_task_id}")


def on_subtask_done(sub_task_id: str):
    """子任务审查通过 → 唤醒规划者检查是否全部完成"""
    trigger_agent_async("main", f"Subtask completed: {sub_task_id}")


def on_subtask_rework(sub_task_id: str):
    """子任务被驳回返工 → 唤醒执行者"""
    trigger_agent_async("executor", f"Subtask needs rework: {sub_task_id}")


def on_subtask_blocked(sub_task_id: str):
    """子任务被标记阻塞 → 唤醒规划者处理"""
    trigger_agent_async("main", f"Subtask blocked: {sub_task_id}")


def init():
    """初始化：加载 cron job 映射"""
    _load_cron_jobs()
    _log(f"Initialized with {len(CRON_JOBS)} cron jobs: {list(CRON_JOBS.keys())}")
