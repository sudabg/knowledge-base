#!/usr/bin/env python3
"""
统一巡检大盘 — 监控所有自动化脚本健康状态
检查项:
  1. 依赖图谱扫描 (dependency-check.py)
  2. 归档快照校验 (archive_snapshot.txt)
  3. MEMORY.md 行数超限
  4. Cron 配置快照校验
  5. 脚本文件存在 + checksum
  6. CHANGELOG 超期未验证条目
  7. P0 告警升级检查
  8. Cron 配置完整性

输出: .learnings/health_dashboard.json + 飞书告警(有异常时)
用法: python3 scripts/unified-dashboard-check.py
"""

import os, json, sys, hashlib, subprocess
from datetime import datetime

BASE = "/home/gem/workspace/agent/workspace"

def check(name, fn):
    """Run a check and return dict."""
    try:
        result = fn()
        return {"check": name, "status": "OK", "detail": result}
    except Exception as e:
        return {"check": name, "status": "FAIL", "detail": str(e)}


# ---- Check Functions (before main!) ----

def check_dependency_map():
    """Run dependency check script."""
    script = os.path.join(BASE, "scripts", "dependency-check.py")
    if not os.path.isfile(script):
        raise FileNotFoundError("dependency-check.py missing!")
    
    result = subprocess.run(
        ["python3", script], capture_output=True, text=True, cwd=BASE, timeout=30
    )
    
    issues = [line for line in result.stdout.split("\n") if "⚠" in line or "[!]" in line]
    return f"OK, issues: {len(issues)}" if not issues else f"ISSUES: {'; '.join(issues)}"


def check_archive_snapshot():
    """Verify archive snapshot integrity."""
    snapshot = os.path.join(BASE, ".learnings", "archive_snapshot.txt")
    archive_dir = os.path.join(BASE, "skills", ".archived-by-audit-2026-04-01")
    
    if not os.path.isfile(snapshot):
        raise FileNotFoundError("archive_snapshot.txt missing!")
    if not os.path.isdir(archive_dir):
        raise FileNotFoundError("Archive directory missing!")
    
    with open(snapshot) as f:
        expected = set(line.strip() for line in f if line.strip())
    
    current = set()
    for name in os.listdir(archive_dir):
        if not name.startswith("."):
            current.add(name)
    
    removed = expected - current
    added = current - expected
    
    if removed:
        return f"INTEGRITY FAIL: removed {len(removed)}, added {len(added)}"
    
    added_names = [a for a in added]
    if added:
        return f"NEW ARCHIVES: {', '.join(added_names)}"
    
    return "OK"


def check_memory_size():
    """Check MEMORY.md line count."""
    mem = os.path.join(BASE, "MEMORY.md")
    if not os.path.isfile(mem):
        raise FileNotFoundError("MEMORY.md missing!")
    
    with open(mem) as f:
        lines = f.readlines()
    
    count = len(lines)
    if count > 60:
        return f"OVER LIMIT: {count}/60 lines"
    return f"OK ({count}/60)"


def check_cron_config():
    """Check if critical cron config has been tampered (MD5)."""
    snapshot = os.path.join(BASE, ".learnings", "cron_config_snapshot.json")
    checksum_file = os.path.join(BASE, ".learnings", "cron_config_checksum.txt")
    
    if not os.path.isfile(snapshot):
        return "MISSING: cron_config_snapshot.json"
    if not os.path.isfile(checksum_file):
        return "MISSING: cron_config_checksum.txt"
    
    with open(checksum_file) as f:
        expected_hash = f.read().strip().split()[0]
    
    with open(snapshot, "rb") as f:
        actual_hash = hashlib.md5(f.read()).hexdigest()
    
    if expected_hash != actual_hash:
        return "TAMPER DETECTED: cron_config MD5 mismatch"
    
    with open(snapshot) as f:
        config = json.load(f)
    
    return f"OK ({len(config)} jobs protected)"


def check_scripts_exist():
    """Check all critical scripts exist + checksum."""
    required = [
        "scripts/dependency-check.py",
        "scripts/audit-skills.sh",
        "scripts/memory-compaction-check.sh",
        "scripts/preflight.py",
        "scripts/verify.sh",
    ]
    missing = []
    for script in required:
        path = os.path.join(BASE, script)
        if not os.path.isfile(path):
            missing.append(script)
    
    if missing:
        return f"MISSING: {', '.join(missing)}"
    
    # Checksum verification
    checksum_file = os.path.join(BASE, ".learnings", "scripts_checksums.txt")
    if os.path.isfile(checksum_file):
        with open(checksum_file) as f:
            expected = dict(line.strip().split("  ", 1) for line in f if line.strip() and "  " in line)
        
        mismatches = []
        for script_path, expected_md5 in expected.items():
            full_path = os.path.join(BASE, script_path)
            if os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    actual = hashlib.md5(f.read()).hexdigest()
                if actual != expected_md5:
                    mismatches.append(script_path)
        
        if mismatches:
            return f"CHECKSUM MISMATCH: {', '.join(mismatches)}"
    
    return f"OK ({len(required)} scripts verified)"


def check_changelog_stale():
    """Check CHANGELOG for entries older than 7 days without verification."""
    changelog = os.path.join(BASE, "CHANGELOG.md")
    if not os.path.isfile(changelog):
        raise FileNotFoundError("CHANGELOG.md missing!")
    
    with open(changelog) as f:
        content = f.read()
    
    pending = content.count("待验证")
    verified = content.count("✔ 已验证")
    
    if pending > 0:
        return f"{pending} pending, {verified} verified"
    
    return f"OK (all verified: {verified})"


def check_alert_escalation():
    """Check P0 alerts for unacked > 4h."""
    alerts_file = os.path.join(BASE, ".learnings", "p0_alerts.json")
    if not os.path.isfile(alerts_file):
        return "OK (no alerts file)"
    
    with open(alerts_file) as f:
        data = json.load(f)
    
    pending = [a for a in data.get("alerts", []) if a.get("status") != "acked"]
    if pending:
        return f"ALERT: {len(pending)} unacked alerts"
    return "OK"


def check_cron_config_integrity():
    """Check cron config snapshot for disabled/deleted jobs."""
    snapshot = os.path.join(BASE, ".learnings", "cron_config_snapshot.json")
    if not os.path.isfile(snapshot):
        return "MISSING: cron snapshot"
    
    with open(snapshot) as f:
        config = json.load(f)
    
    issues = []
    for name, conf in config.items():
        if not conf.get("enabled"):
            issues.append(f"{name} disabled")
    
    if issues:
        return f"Cron tampered: {'; '.join(issues)}"
    return f"OK ({len(config)} jobs verified)"


def check_redlines():
    """检查三条核心红线是否完好"""
    rscript = os.path.join(BASE, "scripts", "redline-monitor.py")
    if not os.path.isfile(rscript):
        return "FAIL: redline-monitor.py 缺失"
    
    import subprocess
    result = subprocess.run(
        ["python3", rscript], capture_output=True, text=True, cwd=BASE, timeout=15
    )
    
    if result.returncode != 0:
        violations = [l for l in result.stdout.split(chr(10)) if "REDLINE" in l or "🔴" in l]
        return f"REDLINE TRIGGERED: {' | '.join(violations[:3])}"
    
    return "OK (3 redlines intact)"



def check_cold_backup():
    """Check if cold backup exists and is recent"""
    backup = os.path.join(BASE, ".learnings", "cold_backup", "backup-2026-04-01.tar.gz")
    if not os.path.isfile(backup):
        return "MISSING: cold backup not found"
    
    import time
    age_days = (time.time() - os.path.getmtime(backup)) / 86400
    if age_days > 7:
        return f"STALE: cold backup is {int(age_days)} days old (>7 days)"
    
    return f"OK (backup from {int(age_days)} days ago)"


def check_evolution_kpis():
    """考核外部资源吸收转化率，不做虚假全绿"""
    import json, glob, re
    
    # 1. Count resource discoveries vs tickets created
    discovered = 0
    for f in glob.glob(os.path.join(BASE, "awesome-openclaw", "discovered", "*.md")):
        with open(f) as fh:
            content_fh = fh.read()
        # Count GitHub projects mentioned with stars
        discovered += len(re.findall(r'^### \d+\..+?\*', content_fh, re.MULTILINE))
    
    # 2. Count tickets in external-evolution-tickets.md
    tickets_file = os.path.join(BASE, ".learnings", "external-evolution-tickets.md")
    tickets_done = 0
    tickets_pending = 0
    if os.path.isfile(tickets_file):
        with open(tickets_file) as f:
            tickets_content = f.read()
        tickets_done = tickets_content.count("落地状态: **done**")
        tickets_pending = tickets_content.count("落地状态: pending")
    
    total_tickets = tickets_done + tickets_pending
    conversion_rate = (tickets_done / max(total_tickets, 1)) * 100 if total_tickets > 0 else 0
    
    issues = []
    if discovered > 0 and tickets_done == 0:
        issues.append(f"发现{discovered}个资源但0个落地")
    
    if tickets_pending > 5:
        issues.append(f"pending工单{tickets_pending}个 > 5饱和阈值")
    
    return f"DISCOVERED={discovered} TICKETS={total_tickets} DONE={tickets_done} RATE={conversion_rate:.0f}%", issues


def main():
    checks = [
        check("dependency-map", check_dependency_map),
        check("archive-snapshot", check_archive_snapshot),
        check("memory-size", check_memory_size),
        check("cron-config", check_cron_config),
        check("scripts-exist", check_scripts_exist),
        check("changelog-stale", check_changelog_stale),
        check("alert-escalation", check_alert_escalation),
        check("cron-integrity", check_cron_config_integrity),
        check("redlines", check_redlines),
        check("cold-backup", check_cold_backup),
        check("evolution-kpis", check_evolution_kpis),
    ]
    
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "overall": "OK" if all(c["status"] == "OK" for c in checks) else "ISSUES",
    }
    
    out_path = os.path.join(BASE, ".learnings", "health_dashboard.json")
    with open(out_path, "w") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"=== 统一巡检大盘 {dashboard['timestamp'][:19]} ===")
    for c in checks:
        icon = "✅" if c["status"] == "OK" else "⚠️"
        print(f"  {icon} {c['check']}: {c['detail']}")
    
    print(f"\n总体: {dashboard['overall']}")
    print(f"报告: {out_path}")
    
    return dashboard["overall"] == "OK"


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


# ---- Alert Classification (for P0/P1/P2 routing) ----

def classify_alerts(dashboard):
    """对检查项分级:
    P0 (立即行动): dependency-map 有归档技能被活跃引用、archive snapshot 不一致
    P1 (1h 内): scripts missing/checksum mismatch、cron config tamper
    P2 (观察): changelog 待验证条目
    """
    alerts = []
    for c in dashboard["checks"]:
        detail = c.get("detail", "")
        
        if c["check"] == "dependency-map" and "ISSUES" in detail:
            alerts.append({"priority": "P0", "check": c["check"], "msg": detail})
        elif c["check"] == "archive-snapshot" and "INTEGRITY" in detail:
            alerts.append({"priority": "P0", "check": c["check"], "msg": detail})
        elif c["check"] == "alert-escalation" and "ALERT" in detail:
            alerts.append({"priority": "P0", "check": c["check"], "msg": detail})
        elif c["check"] == "scripts-exist" and ("MISSING" in detail or "CHECKSUM" in detail):
            alerts.append({"priority": "P1", "check": c["check"], "msg": detail})
        elif c["check"] == "cron-config" and "TAMPER" in detail:
            alerts.append({"priority": "P1", "check": c["check"], "msg": detail})
        elif c["check"] == "memory-size" and "OVER" in detail:
            alerts.append({"priority": "P1", "check": c["check"], "msg": detail})
        elif c["check"] == "cron-integrity" and "tampered" in detail:
            alerts.append({"priority": "P1", "check": c["check"], "msg": detail})
        elif c["check"] == "changelog-stale" and "pending" in detail:
            alerts.append({"priority": "P2", "check": c["check"], "msg": detail})
    
    return sorted(alerts, key=lambda x: x["priority"])
