"""
工具下载路由 — Agent 获取最新 CLI 脚本 + 技能发现
"""
import re as _re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import PlainTextResponse

from app.auth.dependencies import get_current_agent
from app.config import config
from app.models.agent import Agent


router = APIRouter(prefix="/tools", tags=["Tools"])

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

# CLI 脚本路径
CLI_PATH = Path(__file__).resolve().parents[2] / "skills" / "task-cli.py"


@router.get("/cli", summary="下载最新 task-cli.py")
async def download_cli(
    request: Request,
    agent: Agent = Depends(get_current_agent),
):
    """返回最新的 task-cli.py，自动将 BASE_URL 替换为服务地址。

    优先使用 config.server_external_url，未配置时用请求 Host 头兜底。
    """
    if not CLI_PATH.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="CLI 脚本文件不存在")

    content = CLI_PATH.read_text(encoding="utf-8")

    # 计算服务地址（优先 external_url，Host 头兜底）
    if config.has_external_url:
        base_url = config.server_external_url
    else:
        host = request.headers.get("host", "127.0.0.1:6565")
        scheme = "https" if request.url.scheme == "https" else "http"
        base_url = f"{scheme}://{host}"

    # 替换 BASE_URL（匹配 task-cli.py 中的 BASE_URL = "..." 行）
    import re
    content = re.sub(
        r'BASE_URL\s*=\s*"[^"]*"',
        f'BASE_URL = "{base_url}"',
        content,
        count=1,
    )

    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")


# ============================================================
# 技能自动发现 API
# ============================================================

def _parse_skill_frontmatter(path: Path) -> dict:
    """解析 SKILL.md 的 frontmatter 元数据"""
    content = path.read_text(encoding="utf-8")
    meta = {"name": path.parent.name, "description": "", "path": str(path.parent.relative_to(SKILLS_DIR))}

    fm_match = _re.match(r'^---\s*\n(.*?)\n---', content, _re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in ("name", "description"):
                    meta[key] = val
    return meta


@router.get("/skills", summary="列出所有可用技能")
async def list_skills(
    agent: Agent = Depends(get_current_agent),
    search: Optional[str] = Query(None, description="按关键词搜索技能"),
):
    """扫描 skills/ 目录，返回所有 SKILL.md 的索引。支持关键词搜索。"""
    if not SKILLS_DIR.exists():
        return {"skills": [], "total": 0}

    skills = []
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        # 跳过嵌套太深的（如 ppt-shared/references 下的非技能文件）
        rel = skill_md.relative_to(SKILLS_DIR)
        if len(rel.parts) > 2:
            continue
        try:
            meta = _parse_skill_frontmatter(skill_md)
            skills.append(meta)
        except Exception:
            continue

    if search:
        keywords = search.lower().split()
        filtered = []
        for s in skills:
            text = f"{s['name']} {s['description']}".lower()
            if any(kw in text for kw in keywords):
                filtered.append(s)
        skills = filtered

    return {"skills": skills, "total": len(skills)}


@router.get("/skills/{skill_name}", summary="获取指定技能的 SKILL.md 内容")
async def get_skill(
    skill_name: str,
    agent: Agent = Depends(get_current_agent),
):
    """返回指定技能的 SKILL.md 完整内容"""
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在")

    content = skill_path.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")
