#!/usr/bin/env python3
"""
Dashboard 自动同步 — 从 memory 日志提取完成任务，更新 dashboard JSON
用法: python3 sync_dashboard.py
"""

import json, os, re, glob
from datetime import datetime, timedelta

WORKSPACE = os.path.expanduser("~/workspace/agent/workspace")
DASHBOARD_FILE = f"{WORKSPACE}/dashboard/last_heartbeat.json"
MEMORY_DIR = f"{WORKSPACE}/memory"

def get_today_completed():
    """从今天的 memory 日志提取已完成任务"""
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = f"{MEMORY_DIR}/{today}.md"
    
    completed = []
    if os.path.exists(memory_file):
        with open(memory_file) as f:
            content = f.read()
        
        # 匹配完成标记 ✅
        for line in content.split("\n"):
            if "✅" in line and len(line) > 10:
                # 清理 markdown 格式
                clean = re.sub(r'\*\*|`|#', '', line.strip())
                completed.append(clean)
    
    return completed

def get_project_plans_completed():
    """从项目计划文件提取已完成项"""
    today = datetime.now().strftime("%Y-%m-%d")
    plan_file = f"{WORKSPACE}/docs/project-plans-{today}.md"
    
    completed = []
    if os.path.exists(plan_file):
        with open(plan_file) as f:
            content = f.read()
        
        for line in content.split("\n"):
            if "[x]" in line or "✅" in line:
                clean = re.sub(r'\[x\]|\*\*|`|#{1,3}\s*', '', line.strip()).strip()
                if clean and len(clean) > 5:
                    completed.append(clean)
    
    return completed

def sync_dashboard():
    """同步 dashboard 数据"""
    # 读取现有 dashboard
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE) as f:
            dashboard = json.load(f)
    else:
        dashboard = {"projects": {}, "completed_count": 0}
    
    # 更新时间戳
    dashboard["last_check"] = datetime.now().strftime("%Y-%m-%dT%H:%M:00+08:00")
    
    # 获取已完成任务
    today_completed = get_today_completed()
    plan_completed = get_project_plans_completed()
    
    all_completed = list(set(today_completed + plan_completed))
    dashboard["completed_today"] = all_completed[:20]  # 最多20条
    dashboard["completed_count"] = len(all_completed)
    
    # 保存
    os.makedirs(os.path.dirname(DASHBOARD_FILE), exist_ok=True)
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dashboard synced: {len(all_completed)} completed tasks")
    return dashboard

def check_consistency():
    """检查 dashboard 与实际状态的一致性"""
    issues = []
    
    # 检查 PyPI 状态
    try:
        import subprocess
        result = subprocess.run(["pip3","show","ai-text-audit"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            pypi_installed = True
        else:
            pypi_installed = False
    except:
        pypi_installed = False
    
    # 检查 dashboard 中的 PyPI 状态
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE) as f:
            dashboard = json.load(f)
        
        stars_project = dashboard.get("projects", {}).get("500stars_project", {})
        details = stars_project.get("details", [])
        pypi_pending = any("等待" in d and "token" in d.lower() for d in details)
        
        if pypi_installed and pypi_pending:
            issues.append("PyPI 已发布但 dashboard 显示等待 token")
    
    return issues

if __name__ == "__main__":
    print("=" * 50)
    print(f"📊 Dashboard Sync — {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    dashboard = sync_dashboard()
    
    # 一致性检查
    issues = check_consistency()
    if issues:
        print(f"\n⚠️ Consistency issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ No consistency issues")
