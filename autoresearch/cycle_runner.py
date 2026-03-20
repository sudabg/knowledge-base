#!/usr/bin/env python3
"""Autonomous evolution cycle runner.
Usage: python3 cycle_runner.py [--count N] [--min-bounty N]
"""
import sys, time, json, os
from evomap import heartbeat, get_tasks, build_bundle, publish

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Content templates by category
TEMPLATES = {
    "debugging": {
        "structure": [
            "## 问题本质\n{problem_essence}",
            "## 故障模式分类\n{failure_modes}",
            "## 系统化诊断框架\n{diagnostic_framework}",
            "## 实施建议\n{implementation}",
            "## 参考\n{references}"
        ]
    },
    "analysis": {
        "structure": [
            "## 核心问题\n{core_question}",
            "## 多维度分析\n{multi_dimension_analysis}",
            "## 具体策略\n{strategies}",
            "## 实践建议\n{practical_advice}",
            "## 参考\n{references}"
        ]
    },
    "design": {
        "structure": [
            "## 设计背景\n{background}",
            "## 设计原则\n{principles}",
            "## 架构/方案\n{architecture}",
            "## 实施路径\n{implementation_path}",
            "## 参考\n{references}"
        ]
    }
}

def select_tasks(count=3, min_bounty=80, max_wait=300):
    """Select tasks for a cycle, with retry on rate limit."""
    start = time.time()
    while time.time() - start < max_wait:
        tasks = get_tasks(min_bounty=min_bounty, exclude_keywords=["maximize capsule"])
        if tasks:
            # Sort by bounty descending, take top N
            selected = sorted(tasks, key=lambda x: x.get("bounty_amount", 0), reverse=True)[:count]
            return selected
        print(f"  Rate limited, waiting 60s...")
        time.sleep(60)
    return []

def run_cycle(cycle_num, strategy_version="v1.1", min_bounty=80):
    """Run one complete evolution cycle."""
    print(f"\n{'='*50}")
    print(f"Cycle #{cycle_num} | Strategy: {strategy_version}")
    print(f"{'='*50}")
    
    # Step 1: Get node state
    r = heartbeat()
    if "error" in r:
        print("Heartbeat rate limited, waiting...")
        time.sleep(60)
        r = heartbeat()
    
    credit_start = r.get("credit_balance", 0) if "error" not in r else 0
    print(f"Credit: {credit_start}")
    
    # Step 2: Select tasks
    print("\nSelecting tasks...")
    tasks = select_tasks(count=3, min_bounty=min_bounty)
    if not tasks:
        print("No tasks available after waiting")
        return None
    
    print(f"Selected {len(tasks)} tasks:")
    for t in tasks:
        print(f"  ${t.get('bounty_amount'):>3} | {t.get('title')[:55]}")
    
    # Step 3: Execute (placeholder - actual capsule generation needs AI)
    print(f"\nTasks ready for capsule generation:")
    for t in tasks:
        print(f"  Task: {t['task_id']}")
        print(f"  Title: {t['title']}")
        print(f"  Signals: {t.get('signals', 'N/A')}")
        print(f"  ---")
    
    return tasks

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3, help="Capsules per cycle")
    parser.add_argument("--min-bounty", type=int, default=80, help="Minimum bounty")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles")
    args = parser.parse_args()
    
    for i in range(args.cycles):
        tasks = run_cycle(i + 1, min_bounty=args.min_bounty)
        if not tasks:
            break
        if i < args.cycles - 1:
            print("\nWaiting 120s before next cycle...")
            time.sleep(120)
