#!/usr/bin/env python3
"""
SuperClaw Evolution Engine — 三触发自进化系统

三种进化触发:
  FIX      — skill 被使用但效果差/出错 → LLM 分析修复
  DERIVED  — skill 有效但可优化 → LLM 生成增强版
  CAPTURED — 无 skill 匹配但任务成功 → LLM 捕获新模式

架构: 后台 daemon, 监听 session 变化 → 分析(LLM) → 进化 → 写入 skills/
"""

import json
import os
import sys
import time
import signal
import sqlite3
import hashlib
import re
import urllib.request
import urllib.error
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path("/root/openclaw-fusion")
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "evolution.db"
SKILLS_DIR = BASE_DIR / "skills"
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
SESSIONS_JSON = SESSIONS_DIR / "sessions.json"
AUTH_PROFILES = Path("/root/.openclaw/agents/main/agent/auth-profiles.json")
CONFIG_PATH = Path("/root/.openclaw/openclaw.json")
LOG_FILE = Path("/root/.openclaw/logs/evolution-engine.log")
PID_FILE = Path("/tmp/evolution-engine.pid")

CHECK_INTERVAL = 30
HEALTH_CHECK_EVERY = 10  # sessions between health checks
MIN_SELECTIONS_FOR_HEALTH = 3
ANALYSIS_MODEL = "gemini-3-flash-preview"
FALLBACK_MODEL = "grok-3-mini"

# ─── Logging ─────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ─── Telegram Notification ───────────────────────────────────────────────────
def load_bot_token() -> str:
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
        return cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
    except Exception:
        return ""


def send_telegram(text: str, chat_id: str = None):
    token = load_bot_token()
    if not token:
        return
    try:
        data = json.dumps({"chat_id": chat_id, "text": text[:4000]}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


# ─── LLM API (Gemini primary, Grok fallback) ────────────────────────────────
def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("No GEMINI_API_KEY")

    body = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3},
    }
    data = json.dumps(body).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ANALYSIS_MODEL}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read().decode())
    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(result)[:200]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(p.get("text", "") for p in parts)


def _call_grok(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("No XAI_API_KEY")

    body = {
        "model": FALLBACK_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read().decode())
    return result["choices"][0]["message"]["content"]


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call LLM with Gemini primary, Grok fallback."""
    try:
        return _call_gemini(system_prompt, user_prompt, max_tokens)
    except Exception as e:
        log(f"Gemini failed ({e}), falling back to Grok")
    try:
        return _call_grok(system_prompt, user_prompt, max_tokens)
    except Exception as e:
        log(f"Grok also failed: {e}")
        raise


# ─── SQLite Skill Store ─────────────────────────────────────────────────────
class SkillStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS skill_records (
                skill_id       TEXT PRIMARY KEY,
                name           TEXT NOT NULL,
                description    TEXT DEFAULT '',
                path           TEXT NOT NULL,
                is_active      INTEGER DEFAULT 1,
                origin         TEXT DEFAULT 'imported',
                generation     INTEGER DEFAULT 0,
                change_summary TEXT DEFAULT '',
                content_diff   TEXT DEFAULT '',
                content_snapshot TEXT DEFAULT '',
                created_at     TEXT DEFAULT '',
                created_by     TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS skill_lineage (
                skill_id        TEXT NOT NULL,
                parent_skill_id TEXT NOT NULL,
                PRIMARY KEY (skill_id, parent_skill_id),
                FOREIGN KEY (skill_id) REFERENCES skill_records(skill_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS skill_metrics (
                skill_id       TEXT PRIMARY KEY,
                total_uses     INTEGER DEFAULT 0,
                total_success  INTEGER DEFAULT 0,
                total_failures INTEGER DEFAULT 0,
                last_used      TEXT DEFAULT '',
                FOREIGN KEY (skill_id) REFERENCES skill_records(skill_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS execution_analyses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id     TEXT UNIQUE NOT NULL,
                timestamp      TEXT NOT NULL,
                task_completed INTEGER DEFAULT 0,
                task_summary   TEXT DEFAULT '',
                skills_used    TEXT DEFAULT '[]',
                tool_issues    TEXT DEFAULT '[]',
                suggestions    TEXT DEFAULT '[]',
                analyzed_by    TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_skill_active ON skill_records(is_active);
            CREATE INDEX IF NOT EXISTS idx_skill_origin ON skill_records(origin);
            CREATE INDEX IF NOT EXISTS idx_skill_name ON skill_records(name);
        """)
        self.conn.commit()

    def is_session_analyzed(self, session_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM execution_analyses WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row is not None

    def save_analysis(self, session_id: str, analysis: dict):
        self.conn.execute("""
            INSERT OR REPLACE INTO execution_analyses
            (session_id, timestamp, task_completed, task_summary, skills_used, tool_issues, suggestions, analyzed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            datetime.now(timezone.utc).isoformat(),
            1 if analysis.get("task_completed") else 0,
            analysis.get("task_summary", ""),
            json.dumps(analysis.get("skills_used", []), ensure_ascii=False),
            json.dumps(analysis.get("tool_issues", []), ensure_ascii=False),
            json.dumps(analysis.get("suggestions", []), ensure_ascii=False),
            ANALYSIS_MODEL,
        ))
        self.conn.commit()

    def import_skill(self, name: str, path: str, description: str = "") -> str:
        skill_id = f"{self._sanitize(name)}__imp_{hashlib.md5(path.encode()).hexdigest()[:8]}"
        existing = self.conn.execute(
            "SELECT 1 FROM skill_records WHERE skill_id = ?", (skill_id,)
        ).fetchone()
        if existing:
            return skill_id
        self.conn.execute("""
            INSERT INTO skill_records (skill_id, name, description, path, origin, generation, created_at)
            VALUES (?, ?, ?, ?, 'imported', 0, ?)
        """, (skill_id, name, description, path, datetime.now(timezone.utc).isoformat()))
        self.conn.execute("""
            INSERT OR IGNORE INTO skill_metrics (skill_id) VALUES (?)
        """, (skill_id,))
        self.conn.commit()
        return skill_id

    def evolve_fix(self, parent_id: str, change_summary: str, content_diff: str, snapshot: str) -> str:
        parent = self.conn.execute(
            "SELECT * FROM skill_records WHERE skill_id = ?", (parent_id,)
        ).fetchone()
        if not parent:
            raise ValueError(f"Parent skill {parent_id} not found")

        gen = parent["generation"] + 1
        new_id = f"{self._sanitize(parent['name'])}__v{gen}_{hashlib.md5(change_summary.encode()).hexdigest()[:8]}"

        self.conn.execute("BEGIN")
        try:
            self.conn.execute("UPDATE skill_records SET is_active = 0 WHERE skill_id = ?", (parent_id,))
            self.conn.execute("""
                INSERT INTO skill_records
                (skill_id, name, description, path, is_active, origin, generation,
                 change_summary, content_diff, content_snapshot, created_at, created_by)
                VALUES (?, ?, ?, ?, 1, 'fixed', ?, ?, ?, ?, ?, ?)
            """, (
                new_id, parent["name"], parent["description"], parent["path"],
                gen, change_summary, content_diff, snapshot,
                datetime.now(timezone.utc).isoformat(), ANALYSIS_MODEL,
            ))
            self.conn.execute(
                "INSERT INTO skill_lineage (skill_id, parent_skill_id) VALUES (?, ?)",
                (new_id, parent_id)
            )
            self.conn.execute("INSERT OR IGNORE INTO skill_metrics (skill_id) VALUES (?)", (new_id,))
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return new_id

    def evolve_derived(self, parent_ids: list, name: str, path: str,
                       description: str, change_summary: str, snapshot: str) -> str:
        max_gen = 0
        for pid in parent_ids:
            p = self.conn.execute("SELECT generation FROM skill_records WHERE skill_id = ?", (pid,)).fetchone()
            if p:
                max_gen = max(max_gen, p["generation"])

        gen = max_gen + 1
        new_id = f"{self._sanitize(name)}__v{gen}_{hashlib.md5(change_summary.encode()).hexdigest()[:8]}"

        self.conn.execute("BEGIN")
        try:
            self.conn.execute("""
                INSERT INTO skill_records
                (skill_id, name, description, path, is_active, origin, generation,
                 change_summary, content_snapshot, created_at, created_by)
                VALUES (?, ?, ?, ?, 1, 'derived', ?, ?, ?, ?, ?)
            """, (
                new_id, name, description, path,
                gen, change_summary, snapshot,
                datetime.now(timezone.utc).isoformat(), ANALYSIS_MODEL,
            ))
            for pid in parent_ids:
                self.conn.execute(
                    "INSERT INTO skill_lineage (skill_id, parent_skill_id) VALUES (?, ?)",
                    (new_id, pid)
                )
            self.conn.execute("INSERT OR IGNORE INTO skill_metrics (skill_id) VALUES (?)", (new_id,))
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return new_id

    def evolve_captured(self, name: str, path: str, description: str,
                        change_summary: str, snapshot: str) -> str:
        new_id = f"{self._sanitize(name)}__cap_{hashlib.md5(snapshot.encode()).hexdigest()[:8]}"
        self.conn.execute("""
            INSERT OR REPLACE INTO skill_records
            (skill_id, name, description, path, is_active, origin, generation,
             change_summary, content_snapshot, created_at, created_by)
            VALUES (?, ?, ?, ?, 1, 'captured', 0, ?, ?, ?, ?)
        """, (
            new_id, name, description, path,
            change_summary, snapshot,
            datetime.now(timezone.utc).isoformat(), ANALYSIS_MODEL,
        ))
        self.conn.execute("INSERT OR IGNORE INTO skill_metrics (skill_id) VALUES (?)", (new_id,))
        self.conn.commit()
        return new_id

    def record_usage(self, skill_id: str, success: bool):
        self.conn.execute("""
            UPDATE skill_metrics SET
                total_uses = total_uses + 1,
                total_success = total_success + CASE WHEN ? THEN 1 ELSE 0 END,
                total_failures = total_failures + CASE WHEN ? THEN 0 ELSE 1 END,
                last_used = ?
            WHERE skill_id = ?
        """, (success, success, datetime.now(timezone.utc).isoformat(), skill_id))
        self.conn.commit()

    def get_active_skills(self) -> list:
        rows = self.conn.execute(
            "SELECT r.*, m.total_uses, m.total_success, m.total_failures "
            "FROM skill_records r LEFT JOIN skill_metrics m ON r.skill_id = m.skill_id "
            "WHERE r.is_active = 1"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_skills_needing_health_check(self) -> list:
        rows = self.conn.execute("""
            SELECT r.*, m.total_uses, m.total_success, m.total_failures
            FROM skill_records r
            JOIN skill_metrics m ON r.skill_id = m.skill_id
            WHERE r.is_active = 1 AND m.total_uses >= ?
        """, (MIN_SELECTIONS_FOR_HEALTH,)).fetchall()
        return [dict(r) for r in rows]

    def get_analysis_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM execution_analyses").fetchone()
        return row[0] if row else 0

    def find_skill_by_name(self, name: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM skill_records WHERE name = ? AND is_active = 1", (name,)
        ).fetchone()
        return dict(row) if row else None

    def find_skill_by_path(self, path: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM skill_records WHERE path = ? AND is_active = 1", (path,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _sanitize(name: str) -> str:
        s = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower().strip())
        return s[:50] or "skill"


# ─── Session Parser ──────────────────────────────────────────────────────────
def parse_session(session_file: Path) -> dict:
    """Parse a session JSONL into structured data for analysis."""
    messages = []
    tools_used = set()
    skills_mentioned = set()
    errors = []
    task_text = ""

    try:
        lines = session_file.read_text().splitlines()
    except Exception:
        return {}

    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = entry.get("message", {})
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user" and not task_text:
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        task_text = block["text"][:500]
                        break
            elif isinstance(content, str) and content.strip():
                task_text = content[:500]

        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")
                if btype in ("tool_use", "toolCall"):
                    tools_used.add(block.get("name", "unknown"))
                if btype == "text":
                    text = block.get("text", "")
                    skill_refs = re.findall(r'(?:SKILL\.md|skills?/)([\w-]+)', text)
                    skills_mentioned.update(skill_refs)
                    if any(kw in text.lower() for kw in ["error", "failed", "错误", "失败", "traceback"]):
                        errors.append(text[:200])
                if btype in ("tool_result", "toolResult"):
                    result_content = block.get("content", block.get("text", ""))
                    if isinstance(result_content, str) and any(
                        kw in result_content.lower() for kw in ["error", "traceback", "exception"]
                    ):
                        errors.append(result_content[:200])

        # Also check toolResult role messages (content is the result text)
        if role == "toolResult" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if any(kw in text.lower() for kw in ["error", "traceback", "exception", "failed"]):
                        errors.append(text[:200])

        messages.append({"role": role, "content_preview": str(content)[:300]})

    return {
        "task_text": task_text,
        "message_count": len(messages),
        "tools_used": list(tools_used),
        "skills_mentioned": list(skills_mentioned),
        "errors": errors[:10],
        "messages": messages[-20:],  # last 20 for LLM context
    }


def get_existing_skills_summary() -> str:
    """Build a brief summary of existing skills for LLM context."""
    skill_dirs = []
    if SKILLS_DIR.exists():
        for d in sorted(SKILLS_DIR.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                skill_md = (d / "SKILL.md").read_text()[:200]
                skill_dirs.append(f"- {d.name}: {skill_md.split(chr(10))[0]}")
    return "\n".join(skill_dirs[:50])


# ─── Execution Analyzer ─────────────────────────────────────────────────────
ANALYSIS_SYSTEM_PROMPT = """你是 SuperClaw 进化引擎的分析模块。你的任务是分析一次 agent 执行的 session 记录，产出结构化的进化建议。

你需要判断：
1. 任务是否完成？(task_completed: true/false)
2. 任务概述（一句话）
3. 哪些 skill 被使用了？效果如何？
4. 是否有工具使用问题？
5. 进化建议列表（suggestions），每个建议包含：
   - type: "FIX" | "DERIVED" | "CAPTURED"
   - target_skill: 目标 skill 名称（FIX/DERIVED 时填写）
   - direction: 具体描述要修改什么
   - name: 新 skill 名称（CAPTURED 时填写）
   - description: 新 skill 描述（CAPTURED 时填写）

进化触发规则：
- FIX: skill 被引用但执行出错，或 skill 内容过时导致失败
- DERIVED: skill 有效但发现了更好的模式，可以增强
- CAPTURED: 任务成功使用了某种有价值的模式/方法，但没有对应的 skill

请严格返回 JSON 格式（不要 markdown 代码块）：
{
  "task_completed": true/false,
  "task_summary": "一句话概述",
  "skills_used": [{"name": "skill-name", "effective": true/false, "note": "说明"}],
  "tool_issues": [{"tool": "tool-name", "issue": "问题描述"}],
  "suggestions": [
    {
      "type": "FIX|DERIVED|CAPTURED",
      "target_skill": "skill-name or null",
      "direction": "具体修改方向",
      "name": "new-skill-name or null",
      "description": "new skill description or null"
    }
  ]
}

注意：
- 如果任务很简单或者只是闲聊，suggestions 应该为空 []
- 只在真正有价值的模式出现时才建议 CAPTURED
- FIX 只在 skill 确实有问题时触发
- 不要过度进化，宁缺毋滥"""


def analyze_session(session_data: dict, skills_summary: str) -> Optional[dict]:
    """Analyze a session and return structured analysis."""
    if session_data.get("message_count", 0) < 4:
        return None  # too short

    user_prompt = f"""## 任务
{session_data.get('task_text', '未知')}

## 使用的工具
{', '.join(session_data.get('tools_used', [])) or '无'}

## 引用的 Skills
{', '.join(session_data.get('skills_mentioned', [])) or '无'}

## 错误信息
{chr(10).join(session_data.get('errors', [])) or '无'}

## 最近对话摘要（最后20条消息的 role）
{chr(10).join(f"- {m['role']}: {m['content_preview'][:100]}" for m in session_data.get('messages', []))}

## 当前已有 Skills 列表
{skills_summary or '暂无 skills'}"""

    try:
        response = call_llm(ANALYSIS_SYSTEM_PROMPT, user_prompt)
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r'^```\w*\n?', '', response)
            response = re.sub(r'\n?```$', '', response)
        analysis = json.loads(response)
        return analysis
    except (json.JSONDecodeError, RuntimeError) as e:
        log(f"Analysis failed: {e}")
        return None


# ─── Skill Evolver ───────────────────────────────────────────────────────────
EVOLUTION_SYSTEM_PROMPT = """你是 SuperClaw 进化引擎的技能编写模块。你的任务是根据分析结果编写或修改 SKILL.md 文件。

SKILL.md 的标准格式：
```
---
name: skill-name
description: 一句话描述
version: 1.0
evolved_from: parent-skill-name (如果是 FIX/DERIVED)
evolution_type: FIX|DERIVED|CAPTURED
---

# Skill 名称

## 适用场景
描述什么情况下使用这个 skill

## 步骤
1. 第一步
2. 第二步
...

## 工具和命令
具体的命令和工具用法

## 注意事项
- 常见陷阱
- 最佳实践

## 示例
具体的使用示例
```

要求：
- 内容具体、可执行，不要泛泛而谈
- 包含实际的命令、代码片段、API 用法
- 注意事项要从真实失败中总结
- 保持简洁，一个 skill 聚焦一个任务模式"""


def evolve_fix(store: SkillStore, suggestion: dict, session_data: dict) -> Optional[str]:
    """Execute a FIX evolution."""
    target_name = suggestion.get("target_skill", "")
    if not target_name:
        return None

    skill_record = store.find_skill_by_name(target_name)
    skill_path = None
    current_content = ""

    # Try to find skill on disk if not in DB
    if not skill_record:
        skill_dir = SKILLS_DIR / target_name
        if (skill_dir / "SKILL.md").exists():
            current_content = (skill_dir / "SKILL.md").read_text()
            skill_path = str(skill_dir / "SKILL.md")
            skill_id = store.import_skill(target_name, skill_path)
            skill_record = store.find_skill_by_name(target_name)
    else:
        skill_path = skill_record["path"]
        try:
            current_content = Path(skill_path).read_text()
        except Exception:
            current_content = ""

    if not skill_record or not skill_path:
        log(f"FIX: skill '{target_name}' not found, skipping")
        return None

    prompt = f"""## 任务: 修复 Skill

### 当前 Skill 内容
```
{current_content[:6000]}
```

### 问题描述
{suggestion.get('direction', '')}

### 相关错误
{chr(10).join(session_data.get('errors', [])[:5])}

请输出修复后的完整 SKILL.md 内容（不要包裹在代码块中，直接输出 SKILL.md 的内容）。"""

    try:
        new_content = call_llm(EVOLUTION_SYSTEM_PROMPT, prompt, max_tokens=8192)
        new_content = new_content.strip()
        if new_content.startswith("```"):
            new_content = re.sub(r'^```\w*\n?', '', new_content)
            new_content = re.sub(r'\n?```$', '', new_content)

        # Write to disk
        Path(skill_path).write_text(new_content)

        # Record in store
        new_id = store.evolve_fix(
            parent_id=skill_record["skill_id"],
            change_summary=suggestion.get("direction", "FIX evolution"),
            content_diff=f"--- a/SKILL.md\n+++ b/SKILL.md\n(full rewrite)",
            snapshot=json.dumps({"SKILL.md": new_content}, ensure_ascii=False),
        )
        log(f"FIX evolved: {target_name} → {new_id}")
        return new_id
    except Exception as e:
        log(f"FIX evolution failed for {target_name}: {e}")
        return None


def evolve_derived(store: SkillStore, suggestion: dict, session_data: dict) -> Optional[str]:
    """Execute a DERIVED evolution."""
    target_name = suggestion.get("target_skill", "")
    if not target_name:
        return None

    parent_record = store.find_skill_by_name(target_name)
    parent_content = ""

    if not parent_record:
        skill_dir = SKILLS_DIR / target_name
        if (skill_dir / "SKILL.md").exists():
            parent_content = (skill_dir / "SKILL.md").read_text()
            store.import_skill(target_name, str(skill_dir / "SKILL.md"))
            parent_record = store.find_skill_by_name(target_name)
    else:
        try:
            parent_content = Path(parent_record["path"]).read_text()
        except Exception:
            parent_content = ""

    if not parent_record:
        log(f"DERIVED: parent skill '{target_name}' not found, skipping")
        return None

    derived_name = f"{target_name}-enhanced"
    prompt = f"""## 任务: 从现有 Skill 派生增强版

### 父 Skill 内容
```
{parent_content[:6000]}
```

### 增强方向
{suggestion.get('direction', '')}

### 执行上下文
任务: {session_data.get('task_text', '')}
使用的工具: {', '.join(session_data.get('tools_used', []))}

请输出增强后的完整 SKILL.md 内容（不要包裹在代码块中）。
在 frontmatter 中设置 name: {derived_name}"""

    try:
        new_content = call_llm(EVOLUTION_SYSTEM_PROMPT, prompt, max_tokens=8192)
        new_content = new_content.strip()
        if new_content.startswith("```"):
            new_content = re.sub(r'^```\w*\n?', '', new_content)
            new_content = re.sub(r'\n?```$', '', new_content)

        # Create new skill directory
        new_dir = SKILLS_DIR / derived_name
        new_dir.mkdir(parents=True, exist_ok=True)
        skill_path = new_dir / "SKILL.md"
        skill_path.write_text(new_content)

        new_id = store.evolve_derived(
            parent_ids=[parent_record["skill_id"]],
            name=derived_name,
            path=str(skill_path),
            description=suggestion.get("description", f"Enhanced version of {target_name}"),
            change_summary=suggestion.get("direction", "DERIVED evolution"),
            snapshot=json.dumps({"SKILL.md": new_content}, ensure_ascii=False),
        )
        log(f"DERIVED evolved: {target_name} → {derived_name} ({new_id})")
        return new_id
    except Exception as e:
        log(f"DERIVED evolution failed for {target_name}: {e}")
        return None


def evolve_captured(store: SkillStore, suggestion: dict, session_data: dict) -> Optional[str]:
    """Execute a CAPTURED evolution — create brand new skill from execution pattern."""
    name = suggestion.get("name", "")
    if not name:
        return None

    name = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower().strip())[:50]
    if not name:
        return None

    # Check if already exists
    existing_dir = SKILLS_DIR / name
    if existing_dir.exists() and (existing_dir / "SKILL.md").exists():
        log(f"CAPTURED: skill '{name}' already exists, skipping")
        return None

    prompt = f"""## 任务: 从执行历史捕获新 Skill

### 执行上下文
任务: {session_data.get('task_text', '')}
使用的工具: {', '.join(session_data.get('tools_used', []))}

### 需要捕获的模式
{suggestion.get('direction', '')}

### Skill 信息
名称: {name}
描述: {suggestion.get('description', '')}

请输出完整的 SKILL.md 内容（不要包裹在代码块中）。
这个 skill 应该是一个完整的、可复用的操作指南，包含具体的步骤、命令和注意事项。"""

    try:
        new_content = call_llm(EVOLUTION_SYSTEM_PROMPT, prompt, max_tokens=8192)
        new_content = new_content.strip()
        if new_content.startswith("```"):
            new_content = re.sub(r'^```\w*\n?', '', new_content)
            new_content = re.sub(r'\n?```$', '', new_content)

        # Create skill directory
        new_dir = SKILLS_DIR / name
        new_dir.mkdir(parents=True, exist_ok=True)
        skill_path = new_dir / "SKILL.md"
        skill_path.write_text(new_content)

        new_id = store.evolve_captured(
            name=name,
            path=str(skill_path),
            description=suggestion.get("description", ""),
            change_summary=suggestion.get("direction", "CAPTURED from execution"),
            snapshot=json.dumps({"SKILL.md": new_content}, ensure_ascii=False),
        )
        log(f"CAPTURED new skill: {name} ({new_id})")
        return new_id
    except Exception as e:
        log(f"CAPTURED evolution failed for {name}: {e}")
        return None


# ─── Health Check ────────────────────────────────────────────────────────────
HEALTH_CHECK_PROMPT = """你是 SuperClaw 进化引擎的健康检查模块。

以下是一个 skill 的使用指标：
- 名称: {name}
- 使用次数: {uses}
- 成功次数: {success}
- 失败次数: {failures}
- 失败率: {failure_rate:.0%}
- 来源: {origin}

当前 Skill 内容:
```
{content}
```

请判断这个 skill 是否需要进化，返回 JSON（不要代码块）:
{{
  "needs_evolution": true/false,
  "evolution_type": "FIX" 或 "DERIVED" 或 null,
  "reason": "原因说明",
  "direction": "如果需要进化，具体方向"
}}

规则:
- 失败率 > 40% 且使用次数 >= 3: 考虑 FIX
- 成功率 < 60% 但不是完全失败: 考虑 DERIVED
- 内容过时或不完整: 考虑 FIX
- 如果指标看起来正常，返回 needs_evolution: false"""


def run_health_check(store: SkillStore):
    """Check skill health metrics and trigger evolution if needed."""
    skills = store.get_skills_needing_health_check()
    if not skills:
        return

    log(f"Health check: scanning {len(skills)} skills with enough usage data")
    evolved = []

    for skill in skills:
        uses = skill.get("total_uses", 0)
        failures = skill.get("total_failures", 0)
        success = skill.get("total_success", 0)
        if uses == 0:
            continue

        failure_rate = failures / uses
        if failure_rate < 0.3:
            continue  # healthy enough

        # Read current content
        try:
            content = Path(skill["path"]).read_text()[:4000]
        except Exception:
            content = "(unable to read)"

        prompt = HEALTH_CHECK_PROMPT.format(
            name=skill["name"],
            uses=uses,
            success=success,
            failures=failures,
            failure_rate=failure_rate,
            origin=skill["origin"],
            content=content,
        )

        try:
            response = call_llm("你是技能健康检查分析器。", prompt)
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r'^```\w*\n?', '', response)
                response = re.sub(r'\n?```$', '', response)
            result = json.loads(response)

            if result.get("needs_evolution"):
                evo_type = result.get("evolution_type", "FIX")
                suggestion = {
                    "type": evo_type,
                    "target_skill": skill["name"],
                    "direction": result.get("direction", "Health check triggered fix"),
                }
                session_data = {"task_text": "Health check", "tools_used": [], "errors": []}

                if evo_type == "FIX":
                    new_id = evolve_fix(store, suggestion, session_data)
                elif evo_type == "DERIVED":
                    new_id = evolve_derived(store, suggestion, session_data)
                else:
                    new_id = None

                if new_id:
                    evolved.append(f"{evo_type}: {skill['name']} → {new_id}")

        except Exception as e:
            log(f"Health check failed for {skill['name']}: {e}")

    if evolved:
        msg = f"🔧 健康检查完成，{len(evolved)} 个 skill 已进化:\n" + "\n".join(evolved)
        log(msg)
        send_telegram(msg)


# ─── Import Existing Skills ─────────────────────────────────────────────────
def import_existing_skills(store: SkillStore):
    """Scan skills/ directory and import any not yet tracked."""
    if not SKILLS_DIR.exists():
        return 0

    count = 0
    for d in SKILLS_DIR.iterdir():
        if not d.is_dir():
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        existing = store.find_skill_by_path(str(skill_md))
        if existing:
            continue
        try:
            content = skill_md.read_text()[:500]
            desc_match = re.search(r'description:\s*(.+)', content)
            desc = desc_match.group(1).strip() if desc_match else ""
            store.import_skill(d.name, str(skill_md), desc)
            count += 1
        except Exception:
            pass
    return count


# ─── Main Loop ───────────────────────────────────────────────────────────────
def get_active_session_id() -> Optional[str]:
    try:
        data = json.loads(SESSIONS_JSON.read_text())
        info = data.get("agent:main:main", {})
        return info.get("sessionId")
    except Exception:
        return None


def get_session_file(session_id: str) -> Optional[Path]:
    candidates = [
        SESSIONS_DIR / f"{session_id}.jsonl",
        SESSIONS_DIR / f"{session_id}.jsonl.reset.*",
    ]
    main = SESSIONS_DIR / f"{session_id}.jsonl"
    if main.exists():
        return main
    # Check for reset files
    for f in SESSIONS_DIR.glob(f"{session_id}.jsonl.reset.*"):
        return f
    return None


def analyze_and_evolve(store: SkillStore, session_id: str, session_file: Path) -> bool:
    """Analyze a completed session and trigger evolution. Returns True if analyzed."""
    if store.is_session_analyzed(session_id):
        return False

    session_data = parse_session(session_file)
    if not session_data or session_data.get("message_count", 0) < 4:
        log(f"Session {session_id[:12]} too short ({session_data.get('message_count', 0)} msgs), skipping")
        return False

    log(f"Analyzing session {session_id[:12]}...")
    skills_summary = get_existing_skills_summary()
    analysis = analyze_session(session_data, skills_summary)

    if not analysis:
        log(f"Analysis returned None for session {session_id[:12]}")
        return False

    store.save_analysis(session_id, analysis)
    suggestions = analysis.get("suggestions", [])

    # Record skill usage
    for skill_info in analysis.get("skills_used", []):
        skill_name = skill_info.get("name", "")
        record = store.find_skill_by_name(skill_name)
        if record:
            store.record_usage(record["skill_id"], skill_info.get("effective", False))

    # Execute evolution suggestions
    evolved = []
    for sug in suggestions:
        stype = sug.get("type", "").upper()
        new_id = None
        if stype == "FIX":
            new_id = evolve_fix(store, sug, session_data)
        elif stype == "DERIVED":
            new_id = evolve_derived(store, sug, session_data)
        elif stype == "CAPTURED":
            new_id = evolve_captured(store, sug, session_data)
        if new_id:
            evolved.append(f"{stype}: {sug.get('target_skill') or sug.get('name')} → {new_id}")

    # Notify
    status = "✅" if analysis.get("task_completed") else "❌"
    summary = analysis.get("task_summary", "")
    msg = f"🧬 进化分析 {status}\n任务: {summary}"
    if evolved:
        msg += f"\n\n进化 ({len(evolved)}):\n" + "\n".join(f"  • {e}" for e in evolved)
    else:
        msg += "\n无需进化"
    log(msg)
    send_telegram(msg)
    return True


def scan_unanalyzed_sessions(store: SkillStore) -> list:
    """Find completed sessions (.reset files) that haven't been analyzed."""
    unanalyzed = []
    for f in SESSIONS_DIR.glob("*.jsonl.reset.*"):
        session_id = f.name.split(".jsonl")[0]
        if not store.is_session_analyzed(session_id):
            unanalyzed.append((session_id, f))
    return unanalyzed


def main_loop():
    store = SkillStore()

    # Import existing skills on startup
    imported = import_existing_skills(store)
    log(f"Imported {imported} existing skills into evolution DB")

    # Analyze any previously unanalyzed sessions on startup
    unanalyzed = scan_unanalyzed_sessions(store)
    if unanalyzed:
        log(f"Found {len(unanalyzed)} unanalyzed completed sessions, processing...")
        for sid, sf in unanalyzed:
            try:
                analyze_and_evolve(store, sid, sf)
            except Exception as e:
                log(f"Error analyzing backlog session {sid[:12]}: {e}")
            time.sleep(5)  # rate limit

    last_session_id = get_active_session_id()
    sessions_since_health_check = 0

    while True:
        try:
            time.sleep(CHECK_INTERVAL)

            current_id = get_active_session_id()
            if not current_id:
                continue

            # Detect session change (previous session ended → now has .reset file)
            if current_id != last_session_id and last_session_id is not None:
                prev_file = get_session_file(last_session_id)
                if prev_file and prev_file.exists():
                    try:
                        if analyze_and_evolve(store, last_session_id, prev_file):
                            sessions_since_health_check += 1
                            if sessions_since_health_check >= HEALTH_CHECK_EVERY:
                                sessions_since_health_check = 0
                                run_health_check(store)
                    except Exception as e:
                        log(f"Error analyzing session {last_session_id[:12]}: {e}")

            last_session_id = current_id

        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error in main loop: {e}\n{traceback.format_exc()}")
            time.sleep(60)


def main():
    PID_FILE.write_text(str(os.getpid()))

    def cleanup(sig, frame):
        log("Evolution Engine shutting down")
        try:
            PID_FILE.unlink()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    log(f"🧬 Evolution Engine started (PID {os.getpid()})")
    log(f"  DB: {DB_PATH}")
    log(f"  Skills: {SKILLS_DIR}")
    log(f"  Sessions: {SESSIONS_DIR}")
    log(f"  Model: {ANALYSIS_MODEL}")
    send_telegram("🧬 SuperClaw 进化引擎已启动")

    main_loop()


if __name__ == "__main__":
    main()
