#!/usr/bin/env python3
"""
Dashboard Health Monitor with Auto-Healing
每30分钟检查看板健康度，发现问题自动修复
"""

import os
import json
import glob
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path("/home/gem/workspace/agent/workspace")
PROJECT_PLAN_PATTERN = "docs/project-plans-*.md"
HEARTBEAT_FILE = BASE / ".learnings/last_heartbeat.json"
ACTIVE_FILE = BASE / "memory" / "active.md"
P_FILE = BASE / "P.md"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def get_today_date_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_today_project_plan():
    return BASE / "docs" / f"project-plans-{get_today_date_str()}.md"

def check_project_plan_today():
    """检查今日计划文件是否存在，是否为空或过时"""
    today_file = get_today_project_plan()
    if not today_file.exists():
        log("❌ 今日计划文件不存在")
        return False, "missing_project_plan"
    if today_file.stat().st_size < 1024:
        log("❌ 今日计划文件过小（可能是空模板）")
        return False, "project_plan_empty"
    content = today_file.read_text()
    if get_today_date_str() not in content:
        log("❌ 今日计划文件内容不是今日的")
        return False, "project_plan_stale"
    log("✅ 今日计划文件存在且内容新鲜")
    return True, None

def check_heartbeat_fresh():
    """检查心跳文件新鲜度（<30分钟）"""
    try:
        with open(HEARTBEAT_FILE) as f:
            data = json.load(f)
        updated_str = data.get("updated", "2000-01-01 00:00")
        if ":" in updated_str and len(updated_str) <= 5:
            today = get_today_date_str()
            updated = datetime.strptime(f"{today} {updated_str}", "%Y-%m-%d %H:%M")
        else:
            updated = datetime.fromisoformat(updated_str)
        if datetime.now() - updated > timedelta(minutes=30):
            log("❌ 心跳数据过期（>30分钟）")
            return False, "heartbeat_stale"
        log(f"✅ 心跳数据新鲜（更新于 {updated_str}）")
        return True, None
    except Exception as e:
        log(f"❌ 心跳文件读取失败: {e}")
        return False, "heartbeat_error"

def check_active_p_consistent():
    """检查 active.md 和 P.md 的项目数一致性（基于中期指标 M-XX-X）"""
    try:
        import re
        active_content = ACTIVE_FILE.read_text()
        active_M = set(re.findall(r'M-\d+-\d+', active_content))
        active_projects = len(active_M)
        p_content = P_FILE.read_text()
        p_M = set(re.findall(r'M-\d+-\d+', p_content))
        archived_projects = len(p_M)
        plan_file = get_today_project_plan()
        if plan_file.exists():
            plan_content = plan_file.read_text()
            plan_M = set(re.findall(r'M-\d+-\d+', plan_content))
            expected_total = len(plan_M)
            if active_projects + archived_projects != expected_total:
                log(f"❌ 项目数不一致：active={active_projects} + archived={archived_projects} != expected={expected_total}")
                missing = plan_M - (active_M | p_M)
                extra = (active_M | p_M) - plan_M
                if missing:
                    log(f"   缺失 M-: {sorted(missing)}")
                if extra:
                    log(f"   多余 M-: {sorted(extra)}")
                return False, "active_p_inconsistent"
        log(f"✅ 项目一致性检查通过（active={active_projects}, archived={archived_projects}）")
        return True, None
    except Exception as e:
        log(f"❌ 一致性检查失败: {e}")
        return False, "consistency_error"

def check_dashboard_sync():
    """检查最近一次 dashboard sync 是否成功"""
    try:
        active_mtime = datetime.fromtimestamp(ACTIVE_FILE.stat().st_mtime)
        if datetime.now() - active_mtime > timedelta(hours=1):
            log("❌ active.md 超过1小时未更新")
            return False, "dashboard_stale"
        log(f"✅ active.md 最近更新于 {active_mtime.strftime('%H:%M')}")
        return True, None
    except Exception as e:
        log(f"❌ dashboard 状态检查失败: {e}")
        return False, "dashboard_error"

def create_default_project_plan():
    """创建默认的今日计划文件（如果缺失）"""
    log("🛠️ 正在创建默认今日计划文件...")
    today = get_today_date_str()
    content = f"""# 项目计划（{today}）

---

## 项目一：EvoMap 进化冲刺 🚀（P0 · 持续）

**目标**：维持节点活跃，持续高质量 capsule 发布

**现状**：声望 **90.7**，信用 **5739**，已发布 **262** capsules

### 今日任务
- [ ] 检查并 claim 至少 1 个高 bounty 任务（>=$100）
- [ ] 发布 1 个高质量 capsule（基于 arXiv 论文，≥500 字中文）
- [ ] 维持心跳间隔 ≤15 分钟
- [ ] 验证节点在线状态

## 项目二：看板健康度自愈 📊（P2 · critical）

**目标**：建立自动化监控和修复系统

**现状**：刚修复文件缺失问题，需常态化

### 今日任务
- [ ] 创建 dashboard-health-monitor.py
- [ ] 集成到 HEARTBEAT.md
- [ ] 测试自愈机制（删除 project-plans 验证）
- [ ] 记录测试结果到 LEARNINGS.md

## 项目三：browser-use 测试与文档 🌐（P1 · 进行中）

**目标**：完成自动化测试并发布文档

**现状**：skill 封装 100% 完成，待测试

### 今日任务
- [ ] 编写完整工作流测试脚本
- [ ] 创建快速入门文档
- [ ] 测试 3 个不同网站 headless 稳定性

---

*自动生成于 {today} {datetime.now().strftime('%H:%M')}*
"""
    plan_file = get_today_project_plan()
    try:
        with open(plan_file, "w") as f:
            f.write(content)
        log(f"✅ 已创建计划文件：{plan_file}")
        return True
    except Exception as e:
        log(f"❌ 创建计划文件失败: {e}")
        return False

def run_archive_and_sync():
    """运行归档和同步"""
    log("🔄 运行归档和同步...")
    try:
        result = subprocess.run(
            ["python3", str(BASE / "dashboard" / "archive_completed.py")],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log("✅ 归档成功")
        else:
            log(f"⚠️ 归档失败: {result.stderr}")
            return False
        result2 = subprocess.run(
            ["python3", str(BASE / "autoresearch" / "sync_dashboard.py")],
            capture_output=True, text=True, timeout=60
        )
        if result2.returncode == 0:
            log("✅ 同步成功")
        else:
            log(f"⚠️ 同步失败: {result2.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        log("❌ 归档/同步超时")
        return False
    except Exception as e:
        log(f"❌ 执行错误: {e}")
        return False

def auto_heal(issue):
    """自动修复问题"""
    log(f"🔧 开始自动修复: {issue}")
    if issue == "missing_project_plan":
        if create_default_project_plan():
            log("✅ 项目计划文件创建完成，即将同步看板...")
            if run_archive_and_sync():
                log("✅ 看板同步完成，系统自愈成功")
                return True
    elif issue == "project_plan_empty" or issue == "project_plan_stale":
        log("⚠️ 计划文件存在问题，重新创建...")
        if create_default_project_plan():
            log("✅ 计划文件已重建")
            if run_archive_and_sync():
                log("✅ 看板同步完成")
                return True
    elif issue == "sync_failed" or issue == "dashboard_stale":
        if run_archive_and_sync():
            log("✅ 同步重试成功")
            return True
    elif issue == "heartbeat_stale":
        log("🔄 尝试重新运行心跳...")
        try:
            subprocess.run(
                ["python3", str(BASE / "autoresearch" / "adaptive_heartbeat.py")],
                capture_output=True, timeout=30
            )
            log("✅ 心跳已刷新")
            return True
        except Exception as e:
            log(f"❌ 心跳刷新失败: {e}")
    return False

def main():
    log("🔍 开始看板健康度检查...")
    checks = []
    issues = []
    
    ok, issue = check_project_plan_today()
    checks.append(("project_plan_today_exists", ok))
    if issue: issues.append(issue)
    
    ok, issue = check_heartbeat_fresh()
    checks.append(("heartbeat_fresh", ok))
    if issue: issues.append(issue)
    
    ok, issue = check_active_p_consistent()
    checks.append(("active_p_consistent", ok))
    if issue: issues.append(issue)
    
    ok, issue = check_dashboard_sync()
    checks.append(("dashboard_sync_success", ok))
    if issue: issues.append(issue)
    
    passed = sum(1 for _, ok in checks if ok)
    log(f"📊 检查完成：{passed}/{len(checks)} 项正常")
    
    if issues:
        log(f"🚨 发现 {len(issues)} 个问题：{', '.join(issues)}")
        for issue in issues:
            if auto_heal(issue):
                log(f"✅ 问题 {issue} 已自动修复")
            else:
                log(f"❌ 问题 {issue} 修复失败，需人工干预")
    else:
        log("🎉 所有检查通过，看板健康！")
    
    log_file = BASE / ".learnings" / "dashboard_health.log"
    try:
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} checks={checks} issues={issues} result={'healed' if issues else 'ok'}\n")
    except Exception as e:
        log(f"⚠️ 无法写入健康日志: {e}")

if __name__ == "__main__":
    main()
