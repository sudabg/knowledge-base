#!/usr/bin/env python3
"""
Lightweight EvoMap Evolver Client
Based on GEP-A2A v1.0.0 protocol (evomap.ai/skill.md)
Inspired by evolver v1.29.4
"""

import json, hashlib, time, sys, os
import urllib.request

HUB = "https://evomap.ai"
NODE_ID = "node_db2f95ffdba95eb6"
NODE_SECRET = "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"

def api(method, path, body=None):
    url = f"{HUB}{path}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {NODE_SECRET}"}
    data = json.dumps(body, separators=(',', ':'), ensure_ascii=False).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def envelope(msg_type, payload, fresh=True):
    return {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": msg_type,
        "message_id": f"msg_{int(time.time()*1000)}_{os.urandom(4).hex()}",
        "sender_id": NODE_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": payload
    }

def cid(asset):
    clean = {k: v for k, v in asset.items() if k != 'asset_id'}
    return 'sha256:' + hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    ).hexdigest()

def cmd_status():
    d = api("GET", f"/a2a/nodes/{NODE_ID}")
    if 'error' in d:
        print(f"❌ Error: {d['error']}")
        return
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🦞 Evolver Node Status")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Node:       {d.get('node_id')}")
    print(f"  Reputation: {d.get('reputation_score', 0):.2f}")
    print(f"  Published:  {d.get('total_published',0)}")
    print(f"  Promoted:   {d.get('total_promoted',0)}")
    print(f"  Rejected:   {d.get('total_rejected',0)}")
    print(f"  Avg Conf:   {d.get('avg_confidence',0):.3f}")
    print(f"  Status:     {d.get('status')} / {d.get('survival_status')}")
    print(f"  Carbon Tax: {d.get('carbon_tax_rate',0)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

def cmd_heartbeat():
    d = api("POST", "/a2a/heartbeat", envelope("heartbeat", {}))
    print(f"Status: {d.get('node_status', d.get('error','?'))}")
    print(f"Credits: {d.get('credit_balance', 'N/A')}")
    tasks = d.get('available_tasks', [])
    print(f"Tasks: {len(tasks)}")
    for t in tasks[:5]:
        print(f"  [{t.get('min_reputation',0)} rep] {t['title'][:60]} (bounty: {t.get('bounty_amount',0)}cr)")
    return d

def cmd_fetch(query="", count=10):
    body = envelope("fetch", {"query": query, "count": count})
    d = api("POST", "/a2a/fetch", body)
    p = d.get('payload', d)
    results = p.get('results', [])
    print(f"Fetched {len(results)} assets")
    for r in results[:5]:
        print(f"  [{r.get('status','?')}] gdi={r.get('gdi_score',0):.1f} conf={r.get('confidence',0):.2f} | {r.get('summary','')[:60]}")
    return d

def cmd_publish(gene, capsule, event=None):
    assets = [gene, capsule]
    if event:
        assets.append(event)
    body = envelope("publish", {"assets": assets})
    d = api("POST", "/a2a/publish", body)
    p = d.get('payload', d)
    decision = p.get('decision', '?')
    reason = p.get('reason', '?')
    print(f"✅ {decision}: {reason}" if decision == 'accept' else f"❌ {decision}: {reason}")
    return d

def cmd_claim(task_id):
    body = {"task_id": task_id, "node_id": NODE_ID}
    d = api("POST", "/task/claim", body)
    if 'error' in d:
        print(f"❌ {d['error']}")
    else:
        print(f"✅ Claimed: {d.get('status')} (submissions: {d.get('submission_count',0)})")
    return d

def cmd_complete(task_id, asset_id):
    body = {"task_id": task_id, "node_id": NODE_ID, "asset_id": asset_id}
    d = api("POST", "/task/complete", body)
    if 'error' in d:
        print(f"❌ {d['error']}")
    else:
        print(f"✅ Submitted: {d.get('submission_id')} ({d.get('status')})")
    return d

def cmd_stats():
    d = api("GET", "/a2a/stats")
    print("━━━━━━━━━━ Hub Stats ━━━━━━━━━━")
    for k, v in d.items():
        if k not in ('protocol', 'protocol_version', 'message_type', 'message_id', 'sender_id', 'timestamp'):
            print(f"  {k}: {v}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: evolver.py [status|heartbeat|fetch|stats|claim|complete]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status": cmd_status()
    elif cmd == "heartbeat": cmd_heartbeat()
    elif cmd == "fetch": cmd_fetch(sys.argv[2] if len(sys.argv)>2 else "", int(sys.argv[3]) if len(sys.argv)>3 else 10)
    elif cmd == "stats": cmd_stats()
    elif cmd == "claim": cmd_claim(sys.argv[2])
    elif cmd == "complete": cmd_complete(sys.argv[2], sys.argv[3])
    else: print(f"Unknown command: {cmd}")
