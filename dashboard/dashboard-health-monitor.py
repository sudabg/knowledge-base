#!/usr/bin/env python3
"""
dashboard-health-monitor.py — 看板健康度自愈监控

检查项:
1. Dashboard HTTP 服务是否响应 (port 8888)
2. sync_completed_tasks.py 最近是否正常执行
3. project-plans 文件是否存在且非空
4. memory 日志是否在写入
5. EvoMap 心跳是否超时 (>30min)

用法:
  python3 dashboard-health-monitor.py          # 单次检查
  python3 dashboard-health-monitor.py --fix    # 检查 + 自动修复
  python3 dashboard-health-monitor.py --json   # JSON 输出
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/home/gem/workspace/agent/workspace")
LOG_FILE = WORKSPACE / "dashboard" / "health-monitor.log"
STATE_FILE = WORKSPACE / "dashboard" / "health-state.json"
PORT = 8888

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_http(port=PORT, timeout=5):
    """检查 Dashboard HTTP 服务"""
    try:
        req = urllib.request.urlopen(f"http://localhost:{port}/api/status", timeout=timeout)
        data = json.loads(req.read())
        return {"ok": True, "status": data.get("status", "unknown"), "port": port}
    except urllib.error.URLError:
        return {"ok": False, "error": f"port {port} 无响应"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_plan_file():
    """检查今日 project-plans 文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    plan = WORKSPACE / "docs" / f"project-plans-{today}.md"
    if not plan.exists():
        # 查找最近的 plan 文件
        docs_dir = WORKSPACE / "docs"
        plans = sorted(docs_dir.glob("project-plans-*.md"), reverse=True)
        if plans:
            age_days = (datetime.now() - datetime.fromtimestamp(plans[0].stat().st_mtime)).days
            return {"ok": age_days <= 1, "file": plans[0].name, "age_days": age_days,
                    "warning": f"今日 plan 缺失，最近: {plans[0].name}"}
        return {"ok": False, "error": "无任何 project-plans 文件"}
    size = plan.stat().st_size
    return {"ok": size > 100, "file": plan.name, "size_bytes": size}

def check_memory_log():
    """检查 memory 日志是否在写入"""
    today = datetime.now().strftime("%Y-%m-%d")
    mem = WORKSPACE / "memory" / f"{today}.md"
    if not mem.exists():
        return {"ok": False, "error": f"memory/{today}.md 不存在"}
    mtime = datetime.fromtimestamp(mem.stat().st_mtime)
    age_min = (datetime.now() - mtime).total_seconds() / 60
    return {"ok": age_min < 120, "file": mem.name, "last_write_min": round(age_min)}

def check_sync_script():
    """检查 sync 脚本最近执行情况"""
    sync_log = WORKSPACE / "dashboard" / "dashboard.log"
    if not sync_log.exists():
        return {"ok": False, "error": "dashboard.log 不存在"}
    mtime = datetime.fromtimestamp(sync_log.stat().st_mtime)
    age_min = (datetime.now() - mtime).total_seconds() / 60
    content = sync_log.read_text()[-500:] if sync_log.stat().st_size > 500 else sync_log.read_text()
    has_error = "error" in content.lower() or "traceback" in content.lower()
    return {"ok": age_min < 60 and not has_error, "last_run_min": round(age_min),
            "has_error": has_error}

def check_evo_heartbeat():
    """检查 EvoMap 心跳是否超时"""
    hb_file = WORKSPACE / "dashboard" / "last_heartbeat.json"
    if not hb_file.exists():
        return {"ok": True, "warning": "无心跳记录文件"}
    try:
        data = json.loads(hb_file.read_text())
        ts = data.get("timestamp", 0)
        age_min = (time.time() - ts) / 60 if ts else 999
        return {"ok": age_min < 30, "last_heartbeat_min": round(age_min),
                "status": data.get("status", "unknown")}
    except Exception as e:
        return {"ok": True, "warning": f"解析失败: {e}"}

def check_disk_space():
    """检查磁盘空间"""
    stat = os.statvfs(str(WORKSPACE))
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
    pct_used = ((total_gb - free_gb) / total_gb) * 100
    return {"ok": free_gb > 1, "free_gb": round(free_gb, 1),
            "total_gb": round(total_gb, 1), "pct_used": round(pct_used)}

def fix_http():
    """尝试重启 Dashboard HTTP 服务"""
    log("尝试重启 Dashboard 服务...", "FIX")
    try:
        # 先杀掉旧进程
        subprocess.run(["pkill", "-f", "dashboard/app.py"], capture_output=True)
        time.sleep(1)
        # 后台启动
        subprocess.Popen(
            ["python3", str(WORKSPACE / "dashboard" / "app.py")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(WORKSPACE / "dashboard")
        )
        time.sleep(3)
        result = check_http()
        if result["ok"]:
            log("Dashboard 服务已重启成功", "FIX")
            return True
        else:
            log("Dashboard 重启后仍无响应", "ERROR")
            return False
    except Exception as e:
        log(f"重启失败: {e}", "ERROR")
        return False

def run_all_checks(fix=False):
    """执行所有检查"""
    checks = {
        "http_service": check_http(),
        "plan_file": check_plan_file(),
        "memory_log": check_memory_log(),
        "sync_script": check_sync_script(),
        "evo_heartbeat": check_evo_heartbeat(),
        "disk_space": check_disk_space(),
    }

    issues = []
    for name, result in checks.items():
        if not result.get("ok"):
            issues.append(name)

    # 自动修复
    if fix and issues:
        if "http_service" in issues:
            if fix_http():
                checks["http_service"] = check_http()
                if checks["http_service"]["ok"]:
                    issues.remove("http_service")

    # 保存状态
    state = {
        "timestamp": datetime.now().isoformat(),
        "healthy": len(issues) == 0,
        "issues": issues,
        "checks": checks
    }
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    return state

def main():
    fix = "--fix" in sys.argv
    as_json = "--json" in sys.argv

    state = run_all_checks(fix=fix)

    if as_json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        status = "✅ 健康" if state["healthy"] else f"⚠️ 异常 ({', '.join(state['issues'])})"
        print(f"\n{'='*50}")
        print(f"  Dashboard 健康检查 — {status}")
        print(f"{'='*50}")
        for name, result in state["checks"].items():
            icon = "✅" if result.get("ok") else "❌"
            detail = result.get("error") or result.get("warning") or ""
            extra = ""
            if "last_write_min" in result:
                extra = f" (最后写入: {result['last_write_min']}min)"
            elif "last_run_min" in result:
                extra = f" (最后执行: {result['last_run_min']}min)"
            elif "free_gb" in result:
                extra = f" (剩余: {result['free_gb']}GB)"
            elif "last_heartbeat_min" in result:
                extra = f" (心跳: {result['last_heartbeat_min']}min ago)"
            print(f"  {icon} {name}: {detail}{extra}")
        print(f"{'='*50}\n")

    return 0 if state["healthy"] else 1

if __name__ == "__main__":
    sys.exit(main())
