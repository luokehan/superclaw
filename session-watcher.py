#!/usr/bin/env python3
"""
Session Watcher — 监控 SuperClaw agent session，任务中断时自动续跑

机制：
1. 每 15 秒检查最新 session 文件
2. 如果最后一条 assistant 消息是空的（agent turn 异常结束），且没有"✅ 任务完成"
3. 自动通过 openclaw agent 发送续跑消息
4. 最多续跑 MAX_ROUNDS 轮
5. 通过 Telegram 通知用户续跑状态

与 webhook 模式兼容：不使用 Telegram polling，只通过 openclaw CLI 和 Bot API 发消息。
"""

import json
import os
import sys
import time
import signal
import glob
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SESSIONS_DIR = "/root/.openclaw/agents/main/sessions"
SESSIONS_JSON = os.path.join(SESSIONS_DIR, "sessions.json")
LOG_FILE = "/root/.openclaw/logs/session-watcher.log"
PID_FILE = "/tmp/session-watcher.pid"

CONFIG_PATH = "/root/.openclaw/openclaw.json"
MAX_ROUNDS = 5
CHECK_INTERVAL = 15  # seconds
IDLE_THRESHOLD = 30  # seconds since last message before considering "stuck"
CONTINUATION_MSG = "上一轮执行被中断了。请继续完成未完成的部分。检查当前产出物状态，从断点继续。"

# Track continuation state
continuation_state = {
    "session_file": None,
    "last_line_count": 0,
    "rounds": 0,
    "last_check_time": 0,
    "cooldown_until": 0,
}


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def load_bot_token():
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
    except:
        return ""


def send_telegram(text, chat_id=None):
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
    except:
        pass


def get_active_session():
    """Get the current active session file path."""
    try:
        with open(SESSIONS_JSON) as f:
            data = json.load(f)
        session_info = data.get("agent:main:main", {})
        return session_info.get("sessionFile")
    except:
        return None


def check_session_state(session_file):
    """
    Check if the session needs continuation.
    Returns: "ok" | "needs_continuation" | "waiting_user" | "idle"
    """
    try:
        with open(session_file) as f:
            lines = f.readlines()
    except:
        return "ok", len([])

    if not lines:
        return "ok", 0

    line_count = len(lines)

    # Check last few messages
    last_messages = []
    for line in lines[-5:]:
        try:
            d = json.loads(line.strip())
            last_messages.append(d)
        except:
            pass

    if not last_messages:
        return "ok", line_count

    last = last_messages[-1]
    last_msg = last.get("message", {})
    last_role = last_msg.get("role", "")
    last_content = last_msg.get("content", "")
    last_ts = last.get("timestamp", "")

    # Parse timestamp
    try:
        msg_time = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - msg_time).total_seconds()
    except:
        age = 0

    # Check if task is done
    full_text = json.dumps(last_content) if isinstance(last_content, list) else str(last_content)
    done_markers = ["✅ 任务完成", "✅ 交付", "任务完成", "已交付"]
    if any(m in full_text for m in done_markers):
        return "ok", line_count

    # Check if waiting for user
    user_markers = ["可以开始吗", "请确认", "sessions_yield", "等待用户"]
    if any(m in full_text for m in user_markers):
        return "waiting_user", line_count

    # Check for empty assistant message (agent turn ended abnormally)
    if last_role == "assistant":
        if isinstance(last_content, list) and len(last_content) == 0:
            if age > IDLE_THRESHOLD:
                return "needs_continuation", line_count
        elif isinstance(last_content, str) and last_content.strip() == "":
            if age > IDLE_THRESHOLD:
                return "needs_continuation", line_count

    # Check if toolResult was last (agent may have crashed after receiving tool output)
    if last_role == "toolResult" and age > IDLE_THRESHOLD * 2:
        return "needs_continuation", line_count

    return "idle", line_count


def send_continuation(session_id):
    """Send a continuation message to the agent via openclaw CLI."""
    log(f"Sending continuation to session {session_id[:12]}...")
    try:
        result = subprocess.run(
            [
                "openclaw", "agent",
                "--agent", "main",
                "--message", CONTINUATION_MSG,
                "--session-id", session_id,
                "--deliver",
                "--timeout", "600",
            ],
            capture_output=True,
            text=True,
            timeout=660,
        )
        if result.returncode == 0:
            log(f"Continuation sent successfully")
            return True
        else:
            log(f"Continuation failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log("Continuation timed out (660s)")
        return False
    except Exception as e:
        log(f"Continuation error: {e}")
        return False


def main_loop():
    log("Session Watcher started")

    while True:
        try:
            now = time.time()

            # Cooldown check
            if now < continuation_state["cooldown_until"]:
                time.sleep(CHECK_INTERVAL)
                continue

            session_file = get_active_session()
            if not session_file or not os.path.exists(session_file):
                time.sleep(CHECK_INTERVAL)
                continue

            # Reset state if session changed
            if session_file != continuation_state["session_file"]:
                continuation_state["session_file"] = session_file
                continuation_state["rounds"] = 0
                continuation_state["last_line_count"] = 0
                continuation_state["max_notified"] = False

            state, line_count = check_session_state(session_file)

            # Only act if the session has new content since last check
            if line_count == continuation_state["last_line_count"] and state != "needs_continuation":
                time.sleep(CHECK_INTERVAL)
                continue

            continuation_state["last_line_count"] = line_count

            if state == "needs_continuation":
                if continuation_state["rounds"] >= MAX_ROUNDS:
                    if not continuation_state.get("max_notified"):
                        log(f"Max rounds ({MAX_ROUNDS}) reached, stopping auto-continuation")
                        send_telegram(f"⚠️ 任务自动续跑已达上限（{MAX_ROUNDS}轮），可能需要你手动干预。")
                        continuation_state["max_notified"] = True
                    continuation_state["cooldown_until"] = now + 3600
                    continue

                continuation_state["rounds"] += 1
                round_num = continuation_state["rounds"]

                log(f"Session needs continuation (round {round_num}/{MAX_ROUNDS})")
                send_telegram(f"🔄 检测到任务中断，自动续跑中...（第{round_num}轮）")

                # Extract session ID from file path
                session_id = os.path.basename(session_file).replace(".jsonl", "")
                success = send_continuation(session_id)

                if not success:
                    log("Continuation failed, entering cooldown")
                    continuation_state["cooldown_until"] = now + 120

            elif state == "ok":
                if continuation_state["rounds"] > 0:
                    log(f"Task completed after {continuation_state['rounds']} continuation(s)")
                    continuation_state["rounds"] = 0

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)


def main():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    def cleanup(sig, frame):
        log("Shutting down...")
        try:
            os.remove(PID_FILE)
        except:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    log(f"Session Watcher PID {os.getpid()}")
    main_loop()


if __name__ == "__main__":
    main()
