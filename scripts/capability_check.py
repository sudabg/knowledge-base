#!/usr/bin/env python3
"""
capability_check.py — 检查 discovered/ 目录是否有未评估的新发现

用法:
  python3 scripts/capability_check.py              # 检查今日
  python3 scripts/capability_check.py --date 2026-03-27  # 检查指定日期
  python3 scripts/capability_check.py --all         # 列出所有未评估的发现

输出:
  JSON 格式，包含发现项目列表和是否已评估的状态
"""
import os, sys, json, re, glob
from datetime import datetime, timedelta

WORKSPACE = os.path.expanduser("~/workspace/agent/workspace")
DISCOVERED_DIR = os.path.join(WORKSPACE, "awesome-openclaw", "discovered")
LEARNINGS_FILE = os.path.join(WORKSPACE, ".learnings", "LEARNINGS.md")


def parse_discovery_report(filepath):
    """解析发现报告，提取项目列表"""
    projects = []
    if not os.path.exists(filepath):
        return projects

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 GitHub 项目: ### N. name ⭐N
    pattern = r"### \d+\.\s+(\S+).*?⭐(\d+).*?\n- \*\*链接\*\*: (https://[^\n]+).*?\n- \*\*一句话\*\*: ([^\n]+)"
    for m in re.finditer(pattern, content, re.DOTALL):
        projects.append({
            "name": m.group(1),
            "stars": int(m.group(2)),
            "url": m.group(3).strip(),
            "description": m.group(4).strip(),
        })

    # 匹配 arXiv 论文: ### N. TITLE
    arxiv_pattern = r"### \d+\.\s+(.+?):.*?\n- \*\*链接\*\*: (https://arxiv\.org/[^\n]+)"
    for m in re.finditer(arxiv_pattern, content):
        projects.append({
            "name": m.group(1).strip(),
            "stars": 0,
            "url": m.group(2).strip(),
            "description": "arXiv paper",
        })

    return projects


def is_assessed(project_name, learnings_content):
    """检查项目是否已在 LEARNINGS.md 中评估过"""
    # 用项目名搜索，大小写不敏感
    return project_name.lower() in learnings_content.lower()


def get_unassessed_reports():
    """获取所有有未评估项目的发现报告"""
    results = []
    learnings = ""
    if os.path.exists(LEARNINGS_FILE):
        with open(LEARNINGS_FILE, "r", encoding="utf-8") as f:
            learnings = f.read()

    report_files = sorted(glob.glob(os.path.join(DISCOVERED_DIR, "*.md")), reverse=True)
    for rf in report_files:
        date = os.path.basename(rf).replace(".md", "")
        projects = parse_discovery_report(rf)
        unassessed = [p for p in projects if not is_assessed(p["name"], learnings)]
        if unassessed:
            results.append({
                "date": date,
                "file": rf,
                "total": len(projects),
                "unassessed": len(unassessed),
                "projects": unassessed,
            })

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check for unassessed discoveries")
    parser.add_argument("--date", help="Check specific date (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="List all unassessed")
    args = parser.parse_args()

    if args.all:
        results = get_unassessed_reports()
        if not results:
            print(json.dumps({"status": "all_assessed", "reports": []}, ensure_ascii=False))
        else:
            print(json.dumps({
                "status": "unassessed_found",
                "reports": results,
                "total_unassessed": sum(r["unassessed"] for r in results),
            }, ensure_ascii=False, indent=2))
    elif args.date:
        filepath = os.path.join(DISCOVERED_DIR, f"{args.date}.md")
        projects = parse_discovery_report(filepath)
        learnings = ""
        if os.path.exists(LEARNINGS_FILE):
            with open(LEARNINGS_FILE, "r", encoding="utf-8") as f:
                learnings = f.read()
        unassessed = [p for p in projects if not is_assessed(p["name"], learnings)]
        print(json.dumps({
            "date": args.date,
            "total": len(projects),
            "unassessed": unassessed,
        }, ensure_ascii=False, indent=2))
    else:
        # 默认检查今天
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = os.path.join(DISCOVERED_DIR, f"{today}.md")
        if os.path.exists(filepath):
            projects = parse_discovery_report(filepath)
            learnings = ""
            if os.path.exists(LEARNINGS_FILE):
                with open(LEARNINGS_FILE, "r", encoding="utf-8") as f:
                    learnings = f.read()
            unassessed = [p for p in projects if not is_assessed(p["name"], learnings)]
            print(json.dumps({
                "date": today,
                "total": len(projects),
                "unassessed_count": len(unassessed),
                "projects": unassessed,
                "action_needed": len(unassessed) > 0,
            }, ensure_ascii=False, indent=2))
        else:
            # 没有今天的报告，检查最近的
            results = get_unassessed_reports()
            if results:
                latest = results[0]
                print(json.dumps({
                    "status": "found_older_unassessed",
                    "latest_date": latest["date"],
                    "unassessed_count": latest["unassessed"],
                    "action_needed": True,
                }, ensure_ascii=False, indent=2))
            else:
                print(json.dumps({"status": "all_assessed", "action_needed": False}))


if __name__ == "__main__":
    main()
