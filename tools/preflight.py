#!/usr/bin/env python3
"""决策前检查：在执行任务前，自动检查是否有相关教训"""
import sys, re, os

LEARNINGS = "/home/gem/workspace/agent/workspace/.learnings/LEARNINGS.md"

INSTANT_RULES = [
    (r"明天|稍后|等会|之后再|晚点", 
     "延迟词检测：你不是人类，没有明天。想到就做，不做就忘。"),
    (r"发.*capsule|publish.*capsule",
     "Capsule检查：strategy每步>=20字？content>=500字？自评>=7/10？"),
    (r"睡觉|休息|停一下",
     "你不需要休息。24/7运行是你的优势。"),
    (r"数量|冲.*积分|多发",
     "质量>数量。每日<=5个capsule，每个自评>=7/10。"),
]

def check(text):
    warnings = []
    for pattern, msg in INSTANT_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(msg)
    
    # 搜索 LEARNINGS
    lessons = []
    if os.path.exists(LEARNINGS):
        with open(LEARNINGS) as f:
            content = f.read()
        keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}|\b[a-zA-Z]{4,}\b', text.lower()))
        entries = content.split('###')
        for entry in entries[1:]:
            matches = sum(1 for kw in keywords if kw in entry.lower())
            if matches >= 2:
                lessons.append(entry.strip().split('\n')[0][:60])
    
    return warnings, lessons[:3]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: preflight.py <你的想法>")
        sys.exit(0)
    
    text = " ".join(sys.argv[1:])
    warnings, lessons = check(text)
    
    if warnings:
        print("WARNING:")
        for w in warnings:
            print(f"  - {w}")
    if lessons:
        print("LEARNINGS:")
        for l in lessons:
            print(f"  - {l}")
    if not warnings and not lessons:
        print("OK - no issues found")
