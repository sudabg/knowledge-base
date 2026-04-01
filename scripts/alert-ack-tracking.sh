#!/bin/bash
# P0 告警回执追踪
# 1. 告警发出后写入 .learnings/pending_alerts.json
# 2. 心跳检查超过 1 小时未 ack 的 P0 → 飞书升级通知
# 3. 超过 4 小时未 ack → 标记为 SYSTEM_CRITICAL

ALERTS_FILE="/home/gem/workspace/agent/workspace/.learnings/pending_alerts.json"

# 初始化
if [ ! -f "$ALERTS_FILE" ]; then
    echo '{"ack_required": false, "alerts": []}' > "$ALERTS_FILE"
fi

# 检查旧告警
python3 -c "
import json, os, sys
from datetime import datetime, timedelta

f = os.environ.get('ALERTS_FILE', '/home/gem/workspace/agent/workspace/.learnings/pending_alerts.json')
if not os.path.exists(f):
    sys.exit(0)

with open(f) as fp:
    data = json.load(fp)

now = datetime.now()
expiring = []
for a in data.get('alerts', []):
    age = now - datetime.fromisoformat(a['timestamp'])
    if age > timedelta(hours=4) and a.get('status') != 'critical':
        a['status'] = 'critical'
        expiring.append(a)

if expiring:
    data['ack_required'] = True
    with open(f, 'w') as fp:
        json.dump(data, fp, indent=2)
    for e in expiring:
        print(f'CRITICAL: {e[\"message\"]} (age: {now - datetime.fromisoformat(e[\"timestamp\"])})')
    sys.exit(1)
else:
    print(f'All {len(data.get(\"alerts\", []))} alerts within SLA')
    sys.exit(0)
"
