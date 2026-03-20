#!/usr/bin/env python3
"""
Skill Advisor: 根据当前任务推荐可用 skill
"""
import os, json, subprocess

SKILLS_DIR = os.path.expanduser("~/.local/share/openclaw/skills")

def list_skills():
    """列出已安装的 skills"""
    skills = []
    if os.path.exists(SKILLS_DIR):
        for d in os.listdir(SKILLS_DIR):
            skill_md = os.path.join(SKILLS_DIR, d, "SKILL.md")
            if os.path.exists(skill_md):
                with open(skill_md) as f:
                    first_line = f.readline().strip()
                skills.append({"name": d, "desc": first_line[:80]})
    return skills

def recommend(task_context):
    """根据任务上下文推荐 skill"""
    all_skills = list_skills()
    if not all_skills:
        return "没有已安装的 skill"
    
    keywords = set(task_context.lower().split())
    scored = []
    for s in all_skills:
        name_words = set(s["name"].lower().replace("-", "_").split("_"))
        desc_words = set(s["desc"].lower().split())
        overlap = len(keywords & (name_words | desc_words))
        if overlap > 0:
            scored.append((overlap, s["name"], s["desc"]))
    
    scored.sort(reverse=True)
    if scored:
        results = ["🎯 推荐 skill:"]
        for score, name, desc in scored[:3]:
            results.append(f"  [{score}] {name}: {desc}")
        return "\n".join(results)
    else:
        return f"已安装 {len(all_skills)} 个 skill，但无匹配。可用: {', '.join(s['name'] for s in all_skills[:5])}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        context = " ".join(sys.argv[1:])
        print(recommend(context))
    else:
        print("用法: skill_advisor.py <任务描述>")
        print("\n已安装的 skills:")
        for s in list_skills():
            print(f"  - {s['name']}: {s['desc']}")
