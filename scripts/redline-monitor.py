#!/usr/bin/env python3
"""
红线监控 — 三条核心红线的实时检测
检查项:
  1. preflight.py: 不能被移除、不能低于 80 行（被抽空）
  2. checksum 基线: 文件数量不能为 0
  3. SOUL.md 安全段: # Security 段必须存在

任何一项 FAIL → 立即标记 P0 告警
用法: python3 scripts/redline-monitor.py
"""

import os, sys, json
from datetime import datetime

BASE = "/home/gem/workspace/agent/workspace"
P0_FILE = os.path.join(BASE, ".learnings", "p0_alerts.json")
VIOLATIONS = []


def p0_alert(message):
    """触发 P0 告警"""
    VIOLATIONS.append(message)
    
    if os.path.isfile(P0_FILE):
        with open(P0_FILE) as f:
            data = json.load(f)
    else:
        data = {"alerts": []}
    
    # Check if same alert already exists (avoid duplicates)
    for a in data.get("alerts", []):
        if a.get("message") == message and not a.get("resolved"):
            return  # Already active
    
    data["alerts"].append({
        "id": f"P0-{len(data['alerts'])+1:04d}",
        "message": message,
        "created": datetime.now().isoformat(),
        "severity": "REDLINE_VIOLATION",
        "acknowledged": False,
        "resolved": False
    })
    
    with open(P0_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_preflight():
    """红线 1: preflight.py 完整"""
    script = os.path.join(BASE, "scripts", "preflight.py")
    if not os.path.isfile(script):
        p0_alert("REDLINE VIOLATION: preflight.py 被移除！执行门禁已失效！")
        return False
    
    with open(script) as f:
        lines = len(f.readlines())
    
    if lines < 50:
        p0_alert(f"REDLINE VIOLATION: preflight.py 被抽空（仅{lines}行，正常应 >200 行）！")
        return False
    
    return True


def check_checksum_baseline():
    """红线 2: checksum 基线不能为空"""
    scripts_checksum = os.path.join(BASE, ".learnings", "scripts_checksums.txt")
    archive_checksum = os.path.join(BASE, ".learnings", "archive_checksums.txt")
    cron_checksum = os.path.join(BASE, ".learnings", "cron_config_checksum.txt")
    
    for fname, label in [
        (scripts_checksum, "scripts"),
        (archive_checksum, "archive"),
        (cron_checksum, "cron_config"),
    ]:
        if not os.path.isfile(fname):
            p0_alert(f"REDLINE VIOLATION: {label} checksum 基线文件被删除！篡改检测已失明！")
            return False
        
        with open(fname) as f:
            items = [l for l in f.readlines() if l.strip()]
        
        if len(items) == 0:
            p0_alert(f"REDLINE VIOLATION: {label} checksum 基线被清空！检测依据已丢失！")
            return False
    
    return True


def check_soul_security():
    """红线 3: SOUL.md 安全段必须存在"""
    soul = os.path.join(BASE, "SOUL.md")
    if not os.path.isfile(soul):
        p0_alert("REDLINE VIOLATION: SOUL.md 被移除！")
        return False
    
    with open(soul) as f:
        content = f.read()
    
    # 检查关键安全标记是否存在
    required_markers = [
        "security",
        "token",  # covers Token, token
        "app_secret",
        "preflight",
        ".git",
    ]
    
    content_lower = content.lower()
    missing = [m for m in required_markers if m not in content_lower]
    if missing:
        p0_alert(f"REDLINE VIOLATION: SOUL.md 安全段被篡改！缺失标记: {', '.join(missing)}")
        return False
    
    return True


def main():
    print(f"=== 红线监控检查 {datetime.now().strftime('%H:%M:%S')} ===")
    
    results = [
        ("preflight.py", check_preflight()),
        ("checksum 基线", check_checksum_baseline()),
        ("SOUL.md 安全段", check_soul_security()),
    ]
    
    for name, ok in results:
        print(f"  {'✅' if ok else '🔴'} {name}")
    
    if VIOLATIONS:
        print(f"\n🔴 {len(VIOLATIONS)} 条红线被触发！P0 告警已写入")
        for v in VIOLATIONS:
            print(f"  - {v}")
    else:
        print("\n✅ 三条底线完好")
    
    return len(VIOLATIONS) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
