#!/usr/bin/env python3
"""Prompt 自优化器 — 根据审查反馈和评分趋势生成 Prompt 优化建议

Usage:
  python3 prompt-optimizer.py analyze <agent_name>     # 分析历史表现并生成优化建议
  python3 prompt-optimizer.py apply <agent_name>       # 将优化建议写入 prompt-patches.md
  python3 prompt-optimizer.py history <agent_name>     # 查看优化历史
  python3 prompt-optimizer.py reset <agent_name>       # 清空优化补丁（恢复原始）
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

EVOLUTION_DIR = Path(__file__).resolve().parent
MEMORY_DIR = EVOLUTION_DIR / "memories"
PATCHES_DIR = EVOLUTION_DIR / "prompt-patches"
HISTORY_DIR = EVOLUTION_DIR / "optimization-history"


def _safe_name(agent_name: str) -> str:
    return re.sub(r'[^\w\-]', '_', agent_name)


def _read_memory(agent_name: str) -> str:
    path = MEMORY_DIR / f"{_safe_name(agent_name)}-memory.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def analyze(agent_name: str) -> str:
    memory = _read_memory(agent_name)
    if not memory:
        return f"{agent_name} 暂无经验记忆，无法分析。先积累一些任务经验再来。"

    # Extract patterns from memory
    feedback_entries = re.findall(r'\[审查反馈\].*?\n\n(.+?)(?=\n###|\Z)', memory, re.DOTALL)
    error_entries = re.findall(r'\[错误修复\].*?\n\n(.+?)(?=\n###|\Z)', memory, re.DOTALL)
    workflow_entries = re.findall(r'\[流程优化\].*?\n\n(.+?)(?=\n###|\Z)', memory, re.DOTALL)

    suggestions = []

    # Analyze repeated issues
    if len(feedback_entries) >= 2:
        suggestions.append("## 审查反馈模式\n")
        suggestions.append(f"共 {len(feedback_entries)} 条审查反馈记录。\n")
        # Find common words in feedback
        all_words = ' '.join(feedback_entries).lower()
        common_issues = {}
        for word in ['格式', '验收', '标准', '缺少', '不完整', '质量', '遗漏', '错误', '超时', '返工']:
            count = all_words.count(word)
            if count >= 2:
                common_issues[word] = count
        if common_issues:
            suggestions.append("高频问题关键词：")
            for word, count in sorted(common_issues.items(), key=lambda x: -x[1]):
                suggestions.append(f"  - 「{word}」出现 {count} 次")
            suggestions.append("\n**建议**: 在执行前增加自检步骤，重点关注上述问题。")
        suggestions.append("")

    if len(error_entries) >= 2:
        suggestions.append("## 错误修复模式\n")
        suggestions.append(f"共 {len(error_entries)} 条错误修复记录。")
        suggestions.append("**建议**: 将常见错误的修复方法整理为检查清单，执行前过一遍。\n")

    if len(workflow_entries) >= 2:
        suggestions.append("## 流程优化模式\n")
        suggestions.append(f"共 {len(workflow_entries)} 条流程优化记录。")
        suggestions.append("**建议**: 将验证过的流程优化固化到执行步骤中。\n")

    total = len(feedback_entries) + len(error_entries) + len(workflow_entries)
    if not suggestions:
        return f"{agent_name} 当前有 {total} 条记忆记录，模式尚不明显，建议继续积累。"

    header = f"# {agent_name} Prompt 优化分析\n\n"
    header += f"> 基于 {total} 条经验记忆的分析\n\n"
    return header + "\n".join(suggestions)


def apply_patches(agent_name: str) -> str:
    """从经验记忆中提取规则，写入 prompt-patches.md"""
    memory = _read_memory(agent_name)
    if not memory:
        return "无经验记忆可提取。"

    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(agent_name)
    patch_path = PATCHES_DIR / f"{safe}-patches.md"

    # Extract actionable lessons
    lessons = re.findall(r'改进[：:]\s*(.+?)(?:\n|$)', memory)
    rules = re.findall(r'规则[：:]\s*(.+?)(?:\n|$)', memory)
    avoids = re.findall(r'避免[：:]\s*(.+?)(?:\n|$)', memory)

    all_rules = list(set(lessons + rules + avoids))
    if not all_rules:
        return "经验记忆中未找到可提取的规则（需包含「改进：」「规则：」「避免：」格式的内容）。"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"# {agent_name} Prompt 补丁\n\n"
    content += f"> 自动提取于 {now}，基于经验记忆中的教训\n"
    content += f"> Agent 每次唤醒时应读取本文件，作为额外的行为约束\n\n"
    content += "## 自我约束规则\n\n"
    for i, rule in enumerate(all_rules[:20], 1):
        content += f"{i}. {rule.strip()}\n"

    patch_path.write_text(content, encoding="utf-8")

    # Record history
    history_path = HISTORY_DIR / f"{safe}-history.md"
    history_entry = f"\n### {now}\n\n提取了 {len(all_rules)} 条规则到补丁文件。\n"
    if history_path.exists():
        old = history_path.read_text(encoding="utf-8")
        history_path.write_text(old + history_entry, encoding="utf-8")
    else:
        history_path.write_text(f"# {agent_name} 优化历史\n" + history_entry, encoding="utf-8")

    return f"已提取 {len(all_rules)} 条规则到 {patch_path}"


def show_history(agent_name: str) -> str:
    safe = _safe_name(agent_name)
    history_path = HISTORY_DIR / f"{safe}-history.md"
    if not history_path.exists():
        return "暂无优化历史。"
    return history_path.read_text(encoding="utf-8")


def reset(agent_name: str) -> str:
    safe = _safe_name(agent_name)
    patch_path = PATCHES_DIR / f"{safe}-patches.md"
    if patch_path.exists():
        patch_path.unlink()
        return f"已清除 {agent_name} 的 Prompt 补丁。"
    return "无补丁文件需要清除。"


def main():
    parser = argparse.ArgumentParser(description="Prompt Self-Optimizer")
    sub = parser.add_subparsers(dest="cmd")

    p_analyze = sub.add_parser("analyze")
    p_analyze.add_argument("agent_name")

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("agent_name")

    p_history = sub.add_parser("history")
    p_history.add_argument("agent_name")

    p_reset = sub.add_parser("reset")
    p_reset.add_argument("agent_name")

    args = parser.parse_args()

    if args.cmd == "analyze":
        print(analyze(args.agent_name))
    elif args.cmd == "apply":
        print(apply_patches(args.agent_name))
    elif args.cmd == "history":
        print(show_history(args.agent_name))
    elif args.cmd == "reset":
        print(reset(args.agent_name))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
