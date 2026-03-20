#!/usr/bin/env python3
"""
主动搜索 hook：随机搜索 + 意图推断
升级版：不只是随机，而是分析最近记忆推断用户可能关心的话题
"""
import random, subprocess, json, os, glob
from datetime import datetime

WORKSPACE = "/home/gem/workspace/agent/workspace"

# 基础话题池
BASE_TOPICS = [
    "EvoMap capsule", "agent evolution", "知识图谱", "记忆系统",
    "bounty task", "credit reputation", "arxiv paper", "GDI score",
    "self-improvement", "error recovery", "quality score", "learning loop",
    "policy rules", "skill advisor", "memory decay", "boot command"
]

def infer_topics():
    """从最近记忆推断用户关心的话题"""
    topics = list(BASE_TOPICS)
    
    # 从今日记忆中提取关键词
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(WORKSPACE, "memory", f"{today}.md")
    if os.path.exists(today_file):
        with open(today_file) as f:
            content = f.read()
        # 提取 ## 标题作为话题
        import re
        headings = re.findall(r'##\s+(.+)', content)
        for h in headings[:5]:
            topics.append(h.strip()[:30])
    
    # 从 LEARNINGS.md 提取
    learnings = os.path.join(WORKSPACE, ".learnings", "LEARNINGS.md")
    if os.path.exists(learnings):
        with open(learnings) as f:
            content = f.read()
        recent = content[-2000:]  # 最近部分
        import re
        headings = re.findall(r'###\s+\[.+?\]\s+(.+)', recent)
        for h in headings[:3]:
            topics.append(h.strip()[:30])
    
    return topics

def auto_search(query=None):
    if not query:
        topics = infer_topics()
        query = random.choice(topics)
    
    result = subprocess.run(
        ["python3", os.path.join(WORKSPACE, "tools", "xixi_memory.py"), "search", query],
        capture_output=True, text=True
    )
    hits = result.stdout.strip()
    
    # 记录调用
    log_file = os.path.join(WORKSPACE, ".learnings", "memory_calls.json")
    try:
        with open(log_file) as f:
            log = json.load(f)
    except:
        log = {"calls": []}
    
    log["calls"].append({
        "time": datetime.now().isoformat(),
        "query": query,
        "hits": len(hits.split('\n')) if hits else 0,
        "inferred": query not in BASE_TOPICS
    })
    log["calls"] = log["calls"][-100:]
    
    with open(log_file, 'w') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    
    return f"🔍 auto-search: {query}"

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    print(auto_search(query))
