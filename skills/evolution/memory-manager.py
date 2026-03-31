#!/usr/bin/env python3
"""Agent 经验记忆管理器 — 读写每个 Agent 的 memory.md

Usage:
  python3 memory-manager.py read <agent_name>
  python3 memory-manager.py write <agent_name> --lesson "经验教训"
  python3 memory-manager.py write <agent_name> --lesson "经验教训" --category "review_feedback|task_pattern|tool_usage|error_fix|workflow"
  python3 memory-manager.py summarize <agent_name>  # 超过50条时自动压缩
  python3 memory-manager.py stats <agent_name>
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parents[1] / "evolution" / "memories"
MAX_ENTRIES = 50

CATEGORIES = {
    "review_feedback": "审查反馈",
    "task_pattern": "任务模式",
    "tool_usage": "工具用法",
    "error_fix": "错误修复",
    "workflow": "流程优化",
}


def get_memory_path(agent_name: str) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\-]', '_', agent_name)
    return MEMORY_DIR / f"{safe_name}-memory.md"


def read_memory(agent_name: str) -> str:
    path = get_memory_path(agent_name)
    if not path.exists():
        return f"# {agent_name} 经验记忆\n\n暂无记录。\n"
    return path.read_text(encoding="utf-8")


def count_entries(content: str) -> int:
    return content.count("\n### ")


def write_lesson(agent_name: str, lesson: str, category: str = "workflow") -> str:
    path = get_memory_path(agent_name)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cat_label = CATEGORIES.get(category, category)

    if not path.exists():
        content = f"# {agent_name} 经验记忆\n\n"
        content += "> 此文件由系统自动维护。Agent 每次唤醒时读取，任务完成后写入。\n\n"
    else:
        content = path.read_text(encoding="utf-8")

    entry = f"\n### [{cat_label}] {now}\n\n{lesson}\n"
    content += entry

    path.write_text(content, encoding="utf-8")

    n = count_entries(content)
    if n > MAX_ENTRIES:
        return f"已写入。当前 {n} 条记录，超过 {MAX_ENTRIES} 条上限，建议执行 summarize 压缩。"
    return f"已写入。当前 {n} 条记录。"


def summarize_memory(agent_name: str) -> str:
    """将历史记忆按类别压缩为摘要（本地规则，不调用 LLM）"""
    path = get_memory_path(agent_name)
    if not path.exists():
        return "无记忆文件。"

    content = path.read_text(encoding="utf-8")
    entries = re.split(r'\n### ', content)
    if len(entries) <= MAX_ENTRIES:
        return f"当前 {len(entries)-1} 条，未超过上限，无需压缩。"

    header = entries[0]
    categorized = {}
    for entry in entries[1:]:
        cat_match = re.match(r'\[(.+?)\]', entry)
        cat = cat_match.group(1) if cat_match else "其他"
        if cat not in categorized:
            categorized[cat] = []
        lines = entry.split('\n')
        body = '\n'.join(lines[1:]).strip()
        if body:
            categorized[cat].append(body)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = f"# {agent_name} 经验记忆\n\n"
    summary += f"> 最近一次压缩: {now} (从 {len(entries)-1} 条压缩)\n\n"

    for cat, lessons in categorized.items():
        summary += f"## {cat}\n\n"
        seen = set()
        for lesson in lessons[-20:]:
            short = lesson[:100]
            if short not in seen:
                seen.add(short)
                summary += f"- {lesson}\n"
        summary += "\n"

    backup_path = path.with_suffix('.md.bak')
    path.rename(backup_path)
    path.write_text(summary, encoding="utf-8")
    return f"已压缩。备份保存在 {backup_path}"


def stats(agent_name: str) -> str:
    path = get_memory_path(agent_name)
    if not path.exists():
        return "无记忆文件。"
    content = path.read_text(encoding="utf-8")
    total = count_entries(content)
    cats = re.findall(r'\[(.+?)\]', content)
    cat_counts = {}
    for c in cats:
        cat_counts[c] = cat_counts.get(c, 0) + 1
    lines = [f"总记录: {total}"]
    for c, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {c}: {n}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Agent Memory Manager")
    sub = parser.add_subparsers(dest="cmd")

    p_read = sub.add_parser("read")
    p_read.add_argument("agent_name")

    p_write = sub.add_parser("write")
    p_write.add_argument("agent_name")
    p_write.add_argument("--lesson", required=True)
    p_write.add_argument("--category", default="workflow",
                         choices=list(CATEGORIES.keys()))

    p_sum = sub.add_parser("summarize")
    p_sum.add_argument("agent_name")

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("agent_name")

    args = parser.parse_args()

    if args.cmd == "read":
        print(read_memory(args.agent_name))
    elif args.cmd == "write":
        print(write_lesson(args.agent_name, args.lesson, args.category))
    elif args.cmd == "summarize":
        print(summarize_memory(args.agent_name))
    elif args.cmd == "stats":
        print(stats(args.agent_name))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
