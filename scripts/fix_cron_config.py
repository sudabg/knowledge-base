#!/usr/bin/env python3
"""立即修复 EvoMap cron 配置：将隔离会话改为主会话系统事件"""
import json
import sys

jobs_file = "/home/gem/workspace/agent/cron/jobs.json"

with open(jobs_file, 'r') as f:
    config = json.load(f)

modified = False
for job in config['jobs']:
    if job['name'] in ['evo-map-evolution', 'evo-map-heartbeat']:
        # 检查是否需要修改
        if job['sessionTarget'] != 'main':
            print(f"🔧 修复 {job['name']}: sessionTarget {job['sessionTarget']} → main")
            job['sessionTarget'] = 'main'
            modified = True

        if job['payload']['kind'] != 'systemEvent':
            print(f"🔧 修复 {job['name']}: payload.kind {job['payload']['kind']} → systemEvent")
            job['payload']['kind'] = 'systemEvent'
            modified = True

        # 确保启用
        if not job['enabled']:
            print(f"🔧 修复 {job['name']}: enabled false → true")
            job['enabled'] = True
            modified = True

        # 增加超时时间（主会话需要更多时间）
        if job['name'] == 'evo-map-evolution' and job['payload'].get('timeoutSeconds', 300) < 600:
            job['payload']['timeoutSeconds'] = 600
            print(f"🔧 修复 {job['name']}: timeoutSeconds → 600")
            modified = True

if modified:
    with open(jobs_file, 'w') as f:
        json.dump(config, f, indent=2)
    print("\n✅ cron 配置已修复！将恢复隔离会话问题导致的超时。")
    sys.exit(0)
else:
    print("\n⏭️  无需修改：配置已是正确状态")
    sys.exit(1)
