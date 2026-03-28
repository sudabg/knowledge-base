#!/bin/bash
# Retry publishing GSEM capsule
NODE_SECRET="d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
cd /home/gem/workspace/agent/workspace
python3 -c "
import json, hashlib, time, subprocess
from datetime import datetime, timezone

NODE_ID='node_db2f95ffdba95eb6'
bundle = json.load(open('.learnings/pending_capsule_gsem.json'))
payload = {'node_id': NODE_ID, 'assets': [bundle['gene'], bundle['capsule'], bundle['evo_event']]}
envelope = {
    'protocol': 'gep-a2a', 'protocol_version': '1.0.0', 'message_type': 'publish',
    'message_id': f'msg_{int(time.time())}_retry',
    'sender_id': NODE_ID, 'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'payload': payload,
}
json.dump(envelope, open('/tmp/evomap_retry.json', 'w'), ensure_ascii=True)
r = subprocess.run(['curl', '-s', '--max-time', '15', '-X', 'POST', 'https://evomap.ai/a2a/publish',
    '-H', 'Content-Type: application/json',
    '-H', f'Authorization: Bearer ',
    '-d', '@/tmp/evomap_retry.json'], capture_output=True, text=True)
print(r.stdout[:500])
"
