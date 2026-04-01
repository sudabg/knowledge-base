#!/usr/bin/env python3
"""
全量技能依赖扫描 - 自动版
扫描所有活跃技能 → 所有其他技能（含归档）的引用关系
输出：依赖图谱 JSON + 误归档告警
用法: python3 scripts/dependency-check.py
"""

import os, json, sys

BASE = "/home/gem/workspace/agent/workspace"
SKILLS_DIR = os.path.join(BASE, "skills")
ARCHIVE_DIR = os.path.join(SKILLS_DIR, ".archived-by-audit-2026-04-01")
OUTPUT = os.path.join(BASE, ".learnings", "skill_dependency_map.json")
SNAPSHOT = os.path.join(BASE, ".learnings", "archive_snapshot.txt")


def read_skill_files(directory):
    """Read all SKILL.md files in a directory."""
    skills = {}
    if not os.path.isdir(directory):
        return skills
    for name in sorted(os.listdir(directory)):
        if name.startswith("."):
            continue
        path = os.path.join(directory, name, "SKILL.md")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                skills[name] = f.read()
    return skills


def scan():
    active = read_skill_files(SKILLS_DIR)

    # Archive skills
    archived = {}
    if os.path.isdir(ARCHIVE_DIR):
        for name in sorted(os.listdir(ARCHIVE_DIR)):
            if name.startswith("."):
                continue
            path = os.path.join(ARCHIVE_DIR, name, "SKILL.md")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    archived[name] = f.read()

    all_skills = {**active, **archived}

    # Build dependency map
    deps = {}
    issues = []

    for skill_name, content in active.items():
        refs = []
        for other_name in all_skills:
            if other_name == skill_name:
                continue
            if other_name.lower() in content.lower():
                refs.append(other_name)
        deps[skill_name] = refs

    # Check: any archived skill referenced by active ones?
    for archived_name in archived:
        for active_name, refs in deps.items():
            if archived_name in refs:
                issues.append({
                    "type": "archived_referenced_by_active",
                    "archived": archived_name,
                    "referenced_by": active_name,
                    "severity": "HIGH",
                    "message": f"归档技能 '{archived_name}' 仍被活跃技能 '{active_name}' 引用"
                })

    # Check: any active skill that depends on another active skill which itself has no deps?
    # (Orphan check)
    for skill_name, refs in deps.items():
        active_refs = [r for r in refs if r in active]
        if not active_refs and skill_name not in ["healthcheck", "agent-browser", "blog-writer", "dev-rigor", "harness-engineering", "brainstorming", "capability-assessment"]:
            # These are standalone tools; others referencing nothing are suspicious
            pass

    return {
        "timestamp": "2026-04-01T23:04",
        "active_count": len(active),
        "archived_count": len(archived),
        "dependencies": deps,
        "issues": issues,
    }


# Run
result = scan()
print(f"活跃: {result['active_count']} | 归档: {result['archived_count']}")

if result["issues"]:
    print("⚠️ 潜在问题:")
    for issue in result["issues"]:
        print(f"  [{issue['severity']}] {issue['message']}")
else:
    print("✅ 无归档技能被活跃技能引用")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"图谱已保存: {OUTPUT}")

# Check archive snapshot consistency
if os.path.isfile(SNAPSHOT):
    with open(SNAPSHOT) as f:
        expected = set(line.strip() for line in f if line.strip())
    current = set()
    if os.path.isdir(ARCHIVE_DIR):
        for name in os.listdir(ARCHIVE_DIR):
            if not name.startswith("."):
                current.add(name)

    removed = expected - current
    added = current - expected

    if removed:
        print("⚠️ Archive 减少（可能有人恢复）:", removed)
    if added:
        print("⚠️ Archive 增加（新归档未记录）:", added)
    if not removed and not added:
        print("✅ Archive 快照一致")
