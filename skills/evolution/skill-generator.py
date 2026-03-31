#!/usr/bin/env python3
"""Executor 技能自生成器 — 遇到新任务类型时自动生成 SKILL.md

Usage:
  python3 skill-generator.py create --name "新技能名" --description "技能描述" --tools "用到的工具" --steps "执行步骤" --tips "注意事项"
  python3 skill-generator.py list
  python3 skill-generator.py check --task-type "任务类型关键词"  # 检查是否已有匹配技能
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = SKILLS_DIR / "auto-generated"


def list_skills() -> str:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    skills = []
    for d in sorted(GENERATED_DIR.iterdir()):
        if d.is_dir():
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                desc_match = re.search(r'description:\s*(.+)', content)
                desc = desc_match.group(1) if desc_match else ""
                skills.append(f"- {d.name}: {desc}")
    if not skills:
        return "暂无自动生成的技能。"
    return "## 自动生成的技能\n\n" + "\n".join(skills)


def check_existing(task_type: str) -> str:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    keywords = set(task_type.lower().split())
    matches = []

    for d in GENERATED_DIR.iterdir():
        if not d.is_dir():
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding="utf-8").lower()
        score = sum(1 for kw in keywords if kw in content)
        if score > 0:
            matches.append((score, d.name))

    # Also check non-auto-generated skills
    for d in SKILLS_DIR.iterdir():
        if not d.is_dir() or d.name == "auto-generated" or d.name == "evolution":
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding="utf-8").lower()
        score = sum(1 for kw in keywords if kw in content)
        if score > 0:
            matches.append((score, d.name))

    if not matches:
        return f"未找到匹配「{task_type}」的技能。可以用 create 命令生成新技能。"

    matches.sort(key=lambda x: -x[0])
    lines = [f"找到 {len(matches)} 个相关技能:"]
    for score, name in matches[:5]:
        lines.append(f"  - {name} (相关度: {score})")
    return "\n".join(lines)


def create_skill(name: str, description: str, tools: str, steps: str, tips: str) -> str:
    safe_name = re.sub(r'[^\w\-]', '-', name.lower().strip())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')

    skill_dir = GENERATED_DIR / f"auto-{safe_name}"
    skill_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
name: auto-{safe_name}
description: {description}
auto_generated: true
created_at: {now}
---

# {name}

{description}

## 适用场景

当任务涉及以下内容时使用本技能：
- {name}

## 所需工具

{tools}

## 执行步骤

{steps}

## 注意事项

{tips}

---
> 此技能由 Executor 在任务执行过程中自动生成（{now}）。
> 如有改进，直接编辑本文件。
"""

    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")
    return f"技能已生成: {skill_path}"


def main():
    parser = argparse.ArgumentParser(description="Skill Self-Generator")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list")

    p_check = sub.add_parser("check")
    p_check.add_argument("--task-type", required=True)

    p_create = sub.add_parser("create")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--description", required=True)
    p_create.add_argument("--tools", default="无特殊工具要求")
    p_create.add_argument("--steps", default="按需执行")
    p_create.add_argument("--tips", default="无")

    args = parser.parse_args()

    if args.cmd == "list":
        print(list_skills())
    elif args.cmd == "check":
        print(check_existing(args.task_type))
    elif args.cmd == "create":
        print(create_skill(args.name, args.description, args.tools, args.steps, args.tips))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
