#!/usr/bin/env python3
"""
任务追踪器：从每日任务记录中提取任务执行模式。
用于检测重复任务，触发自动技能创建。
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
MEMORY_DIR = WORKSPACE / "memory"
TRACKER_FILE = WORKSPACE / ".learnings" / "task_patterns.json"

# 关键词权重
KEYWORD_WEIGHTS = {
    "发布": 2, "创建": 1.5, "更新": 1, "搜索": 1,
    "分析": 1, "写": 1, "读": 0.5, "删除": 1.5,
    "EvoMap": 1.5, "capsule": 2, "博客": 1.5,
    "飞书": 1, "GitHub": 1, "知识库": 1.5,
}

def extract_tasks_from_daily(file_path):
    """从每日日志提取任务执行记录。"""
    tasks = []
    if not file_path.exists():
        return tasks

    content = file_path.read_text(encoding="utf-8")

    # 匹配任务执行模式：时间 + 任务描述
    # 示例：03:00 - 发布 EvoMap capsule
    # 示例：**任务名称** 或 ## 任务名称
    patterns = [
        r'\d{2}:\d{2}\s*[-—]\s*(.+)',
        r'\*\*(.+?)\*\*',
        r'##\s*(.+)',
        r'###\s*(.+)',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            task_text = match.group(1).strip()
            if len(task_text) > 5:  # 过滤太短的匹配
                tasks.append(task_text)

    return tasks

def extract_keywords(task_text):
    """提取任务关键词。"""
    keywords = []
    for kw, weight in KEYWORD_WEIGHTS.items():
        if kw in task_text:
            keywords.append(kw)
    # 添加动词模式
    verbs = re.findall(r'发布|创建|更新|搜索|分析|写|读|删除|生成|检查|执行|运行|部署', task_text)
    keywords.extend(verbs)
    return list(set(keywords))

def calculate_similarity(task1_keywords, task2_keywords):
    """计算两个任务的关键词相似度。"""
    if not task1_keywords or not task2_keywords:
        return 0
    common = set(task1_keywords) & set(task2_keywords)
    total = set(task1_keywords) | set(task2_keywords)
    return len(common) / len(total) if total else 0

def detect_repeated_patterns(days=7):
    """检测最近N天的重复任务模式。"""
    all_tasks = []
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        file_path = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        tasks = extract_tasks_from_daily(file_path)
        for task in tasks:
            keywords = extract_keywords(task)
            all_tasks.append({
                "text": task,
                "keywords": keywords,
                "date": date.strftime("%Y-%m-%d"),
            })

    # 聚类相似任务
    clusters = []
    used = set()

    for i, task1 in enumerate(all_tasks):
        if i in used:
            continue
        cluster = [task1]
        used.add(i)

        for j, task2 in enumerate(all_tasks):
            if j in used or j <= i:
                continue
            sim = calculate_similarity(task1["keywords"], task2["keywords"])
            if sim >= 0.6:  # 相似度阈值
                cluster.append(task2)
                used.add(j)

        if len(cluster) >= 3:  # 重复 ≥3 次
            clusters.append(cluster)

    return clusters

def save_patterns(clusters):
    """保存检测到的模式到文件。"""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)

    patterns = []
    for cluster in clusters:
        pattern = {
            "tasks": [t["text"] for t in cluster],
            "keywords": list(set(kw for t in cluster for kw in t["keywords"])),
            "occurrences": len(cluster),
            "dates": list(set(t["date"] for t in cluster)),
            "detected_at": datetime.now().isoformat(),
        }
        patterns.append(pattern)

    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)

    return patterns

def main():
    """主函数：检测重复模式并输出。"""
    print(f"检测最近 7 天的任务模式...")
    clusters = detect_repeated_patterns(days=7)

    if not clusters:
        print("未检测到重复任务模式。")
        return

    print(f"检测到 {len(clusters)} 个重复模式：")
    for i, cluster in enumerate(clusters, 1):
        keywords = list(set(kw for t in cluster for kw in t["keywords"]))
        print(f"\n  模式 {i}: {', '.join(keywords)}")
        print(f"  重复次数: {len(cluster)}")
        print(f"  示例任务:")
        for task in cluster[:3]:
            print(f"    - {task['text']}")

    # 保存模式
    patterns = save_patterns(clusters)
    print(f"\n模式已保存到: {TRACKER_FILE}")
    print("这些模式可用于自动创建技能。")

if __name__ == "__main__":
    main()
