#!/usr/bin/env python3
"""
P0 告警追踪器
- 新 P0 告警写入 .learnings/p0_alerts.json
- 心跳检查未签收（未确认）超过 1 小时的 P0 告警 → 飞书升级通知
- 用户确认后才标记 resolved
用法: python3 scripts/p0-alert-tracker.py check
"""

import json, os, sys
from datetime import datetime, timedelta

BASE = "/home/gem/workspace/agent/workspace"
ALERTS_FILE = os.path.join(BASE, ".learnings", "p0_alerts.json")

def load_alerts():
    if os.path.isfile(ALERTS_FILE):
        with open(ALERTS_FILE) as f:
            return json.load(f)
    return {"alerts": []}

def new_alert(message):
    """Add a new P0 alert."""
    data = load_alerts()
    data["alerts"].append({
        "id": f"P0-{len(data['alerts'])+1:04d}",
        "message": message,
        "created": datetime.now().isoformat(),
        "notified": False,
        "acknowledged": False,
        "resolved": False
    })
    with open(ALERTS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data["alerts"][-1]

def check_escalation():
    """Check for unacknowledged P0 alerts > 1 hour old."""
    data = load_alerts()
    now = datetime.now()
    escalated = []
    
    for alert in data["alerts"]:
        if alert.get("resolved") or alert.get("acknowledged"):
            continue
        created = datetime.fromisoformat(alert["created"])
        age = now - created
        if age > timedelta(hours=1) and not alert.get("notified"):
            alert["notified"] = True
            escalated.append(alert)
    
    if escalated:
        with open(ALERTS_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    return escalated

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "check"
    
    if action == "check":
        escalated = check_escalation()
        if escalated:
            print(f"⚠️ {len(escalated)} P0 alerts pending escalation:")
            for a in escalated:
                print(f"  [{a['id']}] {a['message']} (age: {datetime.now() - datetime.fromisoformat(a['created'])})")
        else:
            print("✅ No P0 alerts pending")
    elif action == "list":
        data = load_alerts()
        for a in data["alerts"]:
            status = "✅" if a["resolved"] else "🔴" if not a["acknowledged"] else "🟡"
            print(f"  {status} [{a['id']}] {a['message']} (created: {a['created']})")
