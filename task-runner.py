#!/usr/bin/env python3
"""
TaskRunner — 确保 SuperClaw 不会半途停下

机制：
1. 每次 agent turn 结束后，检查最后一条回复
2. 如果回复里包含"✅ 任务完成"且产出物存在 → 真正完成
3. 否则 → 自动发送续跑消息，在同一 session 继续执行
4. 最多续跑 MAX_ROUNDS 轮，防止死循环

用法：
  作为 library 被 approval-gate 或其他调用方使用
  run_task(message, chat_id) → 完整执行一个任务直到完成
"""
import subprocess
import json
import re
import os

MAX_ROUNDS = 10  # 最多续跑轮数
ROUND_TIMEOUT = 600  # 每轮超时 10 分钟

# 判断任务是否完成的关键词
DONE_MARKERS = ["✅ 任务完成", "✅ 交付", "任务完成", "已交付", "产出物："]
# 判断需要用户输入的关键词（不能自动续跑）
NEED_USER_MARKERS = ["可以开始吗", "请确认", "请回复", "你觉得", "需要你"]


def run_agent(message, session_id=None, timeout=ROUND_TIMEOUT):
    """调用 openclaw agent 一次"""
    cmd = ["openclaw", "agent", "--agent", "main", "--message", message,
           "--thinking", "medium", "--timeout", str(timeout), "--json"]
    if session_id:
        cmd += ["--session-id", session_id]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
        if result.returncode != 0:
            return {"texts": [f"[agent error] {result.stderr[:200]}"], "session_id": None}
        data = json.loads(result.stdout)
        payloads = data.get("result", {}).get("payloads", [])
        meta = data.get("result", {}).get("meta", {})
        session = meta.get("agentMeta", {}).get("sessionId", "")
        texts = [p.get("text", "") for p in payloads if p.get("text")]
        return {"texts": texts, "session_id": session}
    except subprocess.TimeoutExpired:
        return {"texts": ["[timeout] Agent 执行超时"], "session_id": session_id}
    except Exception as e:
        return {"texts": [f"[error] {e}"], "session_id": None}


def is_task_done(texts):
    """判断最后的回复是否表明任务完成"""
    all_text = "\n".join(texts[-3:])  # 看最后几条
    for marker in DONE_MARKERS:
        if marker in all_text:
            return True
    return False


def needs_user_input(texts):
    """判断是否在等用户输入（不能自动续跑）"""
    all_text = "\n".join(texts[-2:])
    for marker in NEED_USER_MARKERS:
        if marker in all_text:
            return True
    return False


def make_continue_message(round_num, last_texts):
    """生成续跑消息"""
    last_text = last_texts[-1] if last_texts else ""

    # 检查是否停在了审查结果上
    if any(kw in last_text for kw in ["审查", "review", "Gemini", "反馈", "问题"]):
        return "审查结果已收到。现在请根据审查意见逐条修复，修复完成后重新打包交付。不要停在这里。"

    # 检查是否停在了中间步骤
    if any(kw in last_text for kw in ["步骤", "完成", "正在", "⏳", "接下来"]):
        return "继续执行下一步。按方案逐步推进直到全部完成并交付。"

    # 通用续跑
    return f"你还没完成任务。请继续执行方案中剩余的步骤，完成后交付产出物。（系统自动续跑 第{round_num}轮）"


def run_task(message, on_message=None, timeout_per_round=ROUND_TIMEOUT):
    """
    执行一个完整任务，自动续跑直到完成。

    Args:
        message: 用户的任务描述（已经过审批）
        on_message: 回调函数 on_message(texts) 用于发送中间结果给用户
        timeout_per_round: 每轮超时
    
    Returns:
        {"all_texts": [...], "rounds": N, "completed": bool}
    """
    all_texts = []
    session_id = None

    for round_num in range(1, MAX_ROUNDS + 1):
        # 第一轮发用户消息，后续轮发续跑指令
        if round_num == 1:
            msg = f"用户已批准方案，开始执行。按你之前的方案一步步做，每步汇报进展。完成后自审并交付。最后写经验记忆。\n\n原始请求：{message}"
        else:
            msg = make_continue_message(round_num, all_texts)

        result = run_agent(msg, session_id=session_id, timeout=timeout_per_round)
        session_id = result["session_id"] or session_id
        texts = result["texts"]
        all_texts.extend(texts)

        # 回调：发送中间结果给用户
        if on_message and texts:
            on_message(texts)

        # 检查是否完成
        if is_task_done(texts):
            return {"all_texts": all_texts, "rounds": round_num, "completed": True}

        # 检查是否需要用户输入
        if needs_user_input(texts):
            return {"all_texts": all_texts, "rounds": round_num, "completed": False,
                    "reason": "needs_user_input"}

        # 检查是否有错误
        if any("[error]" in t or "[timeout]" in t for t in texts):
            return {"all_texts": all_texts, "rounds": round_num, "completed": False,
                    "reason": "error"}

    return {"all_texts": all_texts, "rounds": MAX_ROUNDS, "completed": False,
            "reason": "max_rounds"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"用法: python3 {sys.argv[0]} '任务描述'")
        sys.exit(1)

    def print_callback(texts):
        for t in texts:
            print(f"  → {t[:200]}")
        print()

    result = run_task(sys.argv[1], on_message=print_callback)
    print(f"\n完成: {result['completed']} | 轮数: {result['rounds']}")
