#!/usr/bin/env python3
"""审查模式学习器 — Reviewer 积累审查标准，形成项目特定的质量基线

Usage:
  python3 review-learner.py record --project "项目名" --issue "问题" --category "类别" --severity "high|medium|low"
  python3 review-learner.py baseline --project "项目名"    # 生成项目质量基线
  python3 review-learner.py checklist --project "项目名"   # 生成审查检查清单
  python3 review-learner.py stats --project "项目名"       # 统计审查模式
  python3 review-learner.py global-baseline                # 跨项目全局基线
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

EVOLUTION_DIR = Path(__file__).resolve().parent
REVIEW_DATA_DIR = EVOLUTION_DIR / "review-patterns"

CATEGORIES = {
    "code_quality": "代码质量",
    "completeness": "完整性",
    "format": "格式规范",
    "testing": "测试覆盖",
    "documentation": "文档",
    "performance": "性能",
    "security": "安全",
    "ux": "用户体验",
    "other": "其他",
}


def _project_file(project: str) -> Path:
    REVIEW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^\w\-]', '_', project)
    return REVIEW_DATA_DIR / f"{safe}-patterns.json"


def _load_patterns(project: str) -> list:
    path = _project_file(project)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_patterns(project: str, patterns: list):
    path = _project_file(project)
    path.write_text(json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8")


def record_issue(project: str, issue: str, category: str, severity: str) -> str:
    if category not in CATEGORIES:
        return f"无效类别，可选: {', '.join(CATEGORIES.keys())}"
    if severity not in ("high", "medium", "low"):
        return "严重级别可选: high, medium, low"

    patterns = _load_patterns(project)
    patterns.append({
        "issue": issue,
        "category": category,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
    })
    _save_patterns(project, patterns)
    return f"已记录。项目「{project}」共 {len(patterns)} 条审查记录。"


def generate_baseline(project: str) -> str:
    patterns = _load_patterns(project)
    if len(patterns) < 3:
        return f"项目「{project}」仅 {len(patterns)} 条记录，至少需要 3 条才能生成基线。"

    cat_counts = Counter(p["category"] for p in patterns)
    severity_counts = Counter(p["severity"] for p in patterns)
    total = len(patterns)

    lines = [f"# 项目「{project}」质量基线\n"]
    lines.append(f"> 基于 {total} 条审查记录生成\n")

    lines.append("## 问题分布\n")
    for cat, count in cat_counts.most_common():
        pct = count / total * 100
        label = CATEGORIES.get(cat, cat)
        lines.append(f"- {label}: {count} 次 ({pct:.0f}%)")

    lines.append(f"\n## 严重性分布\n")
    for sev, count in severity_counts.most_common():
        lines.append(f"- {sev}: {count} 次")

    # Top issues
    lines.append(f"\n## 高频问题 (Top 10)\n")
    issue_counts = Counter(p["issue"][:80] for p in patterns)
    for issue, count in issue_counts.most_common(10):
        if count >= 2:
            lines.append(f"- [{count}次] {issue}")

    # Category-specific rules
    lines.append(f"\n## 审查重点\n")
    lines.append("基于历史数据，以下领域需要重点关注：\n")
    for cat, count in cat_counts.most_common(3):
        label = CATEGORIES.get(cat, cat)
        cat_issues = [p["issue"] for p in patterns if p["category"] == cat]
        lines.append(f"### {label} (占比 {count/total*100:.0f}%)\n")
        seen = set()
        for issue in cat_issues[-5:]:
            short = issue[:80]
            if short not in seen:
                seen.add(short)
                lines.append(f"- {issue}")
        lines.append("")

    result = "\n".join(lines)

    # Save baseline
    baseline_path = REVIEW_DATA_DIR / f"{re.sub(r'[^\\w-]', '_', project)}-baseline.md"
    baseline_path.write_text(result, encoding="utf-8")
    return result


def generate_checklist(project: str) -> str:
    patterns = _load_patterns(project)
    if len(patterns) < 3:
        return f"记录不足（{len(patterns)} 条），至少需要 3 条。"

    cat_issues = {}
    for p in patterns:
        cat = CATEGORIES.get(p["category"], p["category"])
        if cat not in cat_issues:
            cat_issues[cat] = []
        cat_issues[cat].append(p)

    lines = [f"# 项目「{project}」审查检查清单\n"]
    lines.append(f"> 基于 {len(patterns)} 条历史审查记录自动生成\n")
    lines.append("> Reviewer 审查时逐项检查\n")

    for cat, issues in cat_issues.items():
        lines.append(f"\n## {cat}\n")
        seen = set()
        high_first = sorted(issues, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3))
        for p in high_first:
            short = p["issue"][:80]
            if short not in seen:
                seen.add(short)
                sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(p["severity"], "⚪")
                lines.append(f"- [ ] {sev_icon} {p['issue']}")

    result = "\n".join(lines)

    checklist_path = REVIEW_DATA_DIR / f"{re.sub(r'[^\\w-]', '_', project)}-checklist.md"
    checklist_path.write_text(result, encoding="utf-8")
    return result


def show_stats(project: str) -> str:
    patterns = _load_patterns(project)
    if not patterns:
        return "无审查记录。"

    total = len(patterns)
    cat_counts = Counter(p["category"] for p in patterns)
    sev_counts = Counter(p["severity"] for p in patterns)

    lines = [f"项目「{project}」审查统计：{total} 条记录"]
    lines.append("\n按类别:")
    for cat, count in cat_counts.most_common():
        lines.append(f"  {CATEGORIES.get(cat, cat)}: {count}")
    lines.append("\n按严重性:")
    for sev, count in sev_counts.most_common():
        lines.append(f"  {sev}: {count}")
    return "\n".join(lines)


def global_baseline() -> str:
    REVIEW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_patterns = []
    projects = []
    for f in REVIEW_DATA_DIR.glob("*-patterns.json"):
        project = f.stem.replace("-patterns", "")
        data = json.loads(f.read_text(encoding="utf-8"))
        all_patterns.extend(data)
        projects.append(f"{project} ({len(data)} 条)")

    if len(all_patterns) < 5:
        return f"全局记录不足（{len(all_patterns)} 条），至少需要 5 条。"

    lines = [f"# 全局审查质量基线\n"]
    lines.append(f"> 涵盖 {len(projects)} 个项目，共 {len(all_patterns)} 条记录\n")
    lines.append(f"项目: {', '.join(projects)}\n")

    cat_counts = Counter(p["category"] for p in all_patterns)
    lines.append("## 全局问题分布\n")
    for cat, count in cat_counts.most_common():
        label = CATEGORIES.get(cat, cat)
        pct = count / len(all_patterns) * 100
        lines.append(f"- {label}: {count} 次 ({pct:.0f}%)")

    lines.append("\n## 全局高频问题\n")
    issue_counts = Counter(p["issue"][:80] for p in all_patterns)
    for issue, count in issue_counts.most_common(15):
        if count >= 2:
            lines.append(f"- [{count}次] {issue}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Review Pattern Learner")
    sub = parser.add_subparsers(dest="cmd")

    p_record = sub.add_parser("record")
    p_record.add_argument("--project", required=True)
    p_record.add_argument("--issue", required=True)
    p_record.add_argument("--category", required=True, choices=list(CATEGORIES.keys()))
    p_record.add_argument("--severity", required=True, choices=["high", "medium", "low"])

    p_baseline = sub.add_parser("baseline")
    p_baseline.add_argument("--project", required=True)

    p_checklist = sub.add_parser("checklist")
    p_checklist.add_argument("--project", required=True)

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--project", required=True)

    sub.add_parser("global-baseline")

    args = parser.parse_args()

    if args.cmd == "record":
        print(record_issue(args.project, args.issue, args.category, args.severity))
    elif args.cmd == "baseline":
        print(generate_baseline(args.project))
    elif args.cmd == "checklist":
        print(generate_checklist(args.project))
    elif args.cmd == "stats":
        print(show_stats(args.project))
    elif args.cmd == "global-baseline":
        print(global_baseline())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
