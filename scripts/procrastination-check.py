#!/usr/bin/env python3
"""
防拖延校验脚本
检查 memory/long-term-goals.md 和其他文件中的延期任务
发现超过卡点日期的任务 → 标记为违规
用法: python3 scripts/procrastination-check.py
"""

import os, re, json
from datetime import datetime, timedelta

BASE = "/home/gem/workspace/agent/workspace"
GOALS_FILE = os.path.join(BASE, "memory", "long-term-goals.md")
LOG_FILE = os.path.join(BASE, ".learnings", "procrastination_log.json")

def check():
    violations = []
    
    # 检查 long-term-goals.md 中的延期任务
    if os.path.isfile(GOALS_FILE):
        with open(GOALS_FILE) as f:
            content = f.read()
        
        # 查找所有日期标记
        date_patterns = re.findall(r'(\d{4}-\d{2}-\d{2})', content)
        now = datetime.now()
        
        for date_str in date_patterns:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if date < now - timedelta(days=3):
                    violations.append({
                        "type": "overdue_task",
                        "date": date_str,
                        "message": f"任务标记日期 {date_str} 已超过 3 天"
                    })
            except ValueError:
                pass
    
    return violations

violations = check()

if violations:
    print(f"⚠️ 发现 {len(violations)} 个延期任务:")
    for v in violations:
        print(f"  - [{v['type']}] {v['message']}")
    
    # 记录日志
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE) as f:
            log = json.load(f)
    else:
        log = {"history": []}
    
    log["history"].extend(violations)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
else:
    print("✅ 无延期任务")

