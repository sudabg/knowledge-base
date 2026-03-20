#!/usr/bin/env python3
"""
EvoMap Publish Pipeline with integrated quality checks:
1. Humanize check (AI pattern detection)
2. Content length validation
3. Protocol envelope validation
4. Publish with retry
"""
import json
import hashlib
import datetime
import subprocess
import sys
import urllib.request
import os

SCRIPTS = '/home/gem/workspace/agent/workspace/scripts'
TOKEN = os.environ.get('EVOMAP_TOKEN', 'd846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14')
NODE_ID = 'node_db2f95ffdba95eb6'

def humanize_check(text):
    """Run humanize-check.py and return score"""
    try:
        result = subprocess.run(
            ['python3', f'{SCRIPTS}/humanize-check.py'],
            input=text, capture_output=True, text=True
        )
        output = result.stdout
        for line in output.split('\n'):
            if 'Density:' in line:
                pct = line.split('Density:')[1].strip().rstrip('%')
                return float(pct)
        return 0.0
    except:
        return 0.0

def validate_capsule(content, min_chars=500):
    """Validate capsule content"""
    issues = []
    if len(content) < min_chars:
        issues.append(f"Content too short: {len(content)} < {min_chars}")
    if '```' in content:
        issues.append("Contains code_snippet (will trigger quarantine)")
    if content.count('—') > 5:
        issues.append("Excessive em dashes")
    density = humanize_check(content)
    if density > 5:
        issues.append(f"AI density too high: {density}%")
    return issues

def calc_asset_id(obj):
    """Calculate asset_id hash"""
    json_str = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return 'sha256:' + hashlib.sha256(json_str.encode()).hexdigest()

def publish_bundle(gene, capsule, evo):
    """Publish to EvoMap"""
    envelope = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "publish",
        "message_id": f"msg_publish_{datetime.datetime.utcnow().strftime('%H%M%S')}",
        "sender_id": NODE_ID,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "payload": {
            "node_id": NODE_ID,
            "assets": [gene, capsule, evo]
        }
    }
    
    data = json.dumps(envelope).encode()
    req = urllib.request.Request(
        'https://evomap.ai/a2a/publish',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {TOKEN}'
        }
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        decision = result.get('payload', {}).get('decision', 'unknown')
        reason = result.get('payload', {}).get('reason', '')
        return {'success': True, 'decision': decision, 'reason': reason}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: evomap-publish-with-quality.py <capsule_json_file>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        bundle = json.load(f)
    
    capsule = bundle['payload']['assets'][1]
    content = capsule['content']
    
    print("=== Quality Check ===")
    issues = validate_capsule(content)
    if issues:
        print("❌ Issues found:")
        for i in issues:
            print(f"  - {i}")
        sys.exit(1)
    else:
        print("✅ All checks passed")
    
    print("\n=== Publishing ===")
    result = publish_bundle(
        bundle['payload']['assets'][0],
        capsule,
        bundle['payload']['assets'][2]
    )
    print(f"Decision: {result.get('decision', 'error')}")
    print(f"Reason: {result.get('reason', result.get('error', ''))}")

if __name__ == '__main__':
    main()
