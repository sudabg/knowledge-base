#!/usr/bin/env python3
"""
evomap_a2a.py — EvoMap A2A Protocol Adapter (v1.0.0 envelope)

用法:
  python3 evomap_a2a.py heartbeat
  python3 evomap_a2a.py publish --bundle /tmp/bundle.json
  python3 evomap_a2a.py status
  python3 evomap_a2a.py tasks

自动生成 GEP-A2A 协议 envelope，处理 asset_id hash 计算。
"""

import json, hashlib, time, sys, os, argparse
from datetime import datetime, timezone

NODE_ID = os.environ.get("EVOMAP_NODE_ID", "node_db2f95ffdba95eb6")
NODE_SECRET = os.environ.get("EVOMAP_NODE_SECRET", "") or "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
NODE_ID = os.environ.get("EVOMAP_NODE_ID", "") or "node_db2f95ffdba95eb6"
BASE_URL = "https://evomap.ai"

def compute_asset_id(obj):
    clean = {k: v for k, v in obj.items() if k != "asset_id"}
    canonical = json.dumps(clean, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def make_envelope(message_type, payload):
    return {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": message_type,
        "message_id": f"msg_{int(time.time())}_{os.urandom(4).hex()}",
        "sender_id": NODE_ID,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": payload,
    }

def cmd_heartbeat():
    """REST heartbeat (no envelope needed)"""
    import subprocess
    payload = json.dumps({
        "node_id": NODE_ID,
        "version": "1.5.0",
        "uptime_ms": int(time.time() * 1000),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    r = subprocess.run([
        "curl", "-s", "--max-time", "10",
        "-X", "POST", f"{BASE_URL}/a2a/heartbeat",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {NODE_SECRET}",
        "-d", payload,
    ], capture_output=True, text=True)
    print(r.stdout or "(empty response)")

def cmd_status():
    """REST node status (no envelope needed)"""
    import subprocess
    r = subprocess.run([
        "curl", "-s", "--max-time", "10",
        f"{BASE_URL}/a2a/nodes/{NODE_ID}",
        "-H", f"Authorization: Bearer {NODE_SECRET}",
    ], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        print(f"Rep: {d.get('reputation_score','?')}")
        print(f"Published: {d.get('total_published','?')}")
        print(f"Online: {d.get('online','?')}")
        print(f"Status: {d.get('status','?')}")
    except:
        print(r.stdout or "(error)")

def cmd_tasks():
    """REST task list (no envelope needed)"""
    import subprocess
    r = subprocess.run([
        "curl", "-s", "--max-time", "10",
        f"{BASE_URL}/a2a/task/list?limit=10",
        "-H", f"Authorization: Bearer {NODE_SECRET}",
    ], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        for t in d.get("tasks", []):
            s = t.get("status", "?")
            b = t.get("bounty_amount", 0)
            sl = t.get("slots_remaining", "?")
            title = t.get("title", "?")[:60]
            print(f"[{s}] bounty={b} slots={sl} | {title}")
    except:
        print(r.stdout or "(error)")

def cmd_publish(bundle_path):
    """Publish with envelope"""
    import subprocess
    bundle = json.load(open(bundle_path))
    envelope = make_envelope("publish", bundle)
    env_path = "/tmp/evomap_envelope.json"
    json.dump(envelope, open(env_path, "w"), ensure_ascii=False)
    r = subprocess.run([
        "curl", "-s", "--max-time", "15",
        "-X", "POST", f"{BASE_URL}/a2a/publish",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {NODE_SECRET}",
        "-d", f"@{env_path}",
    ], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        if "error" in d:
            print(f"Error: {d['error']}")
            if "correction" in d:
                print(f"Fix: {d['correction'].get('fix','')}")
        else:
            print(f"Published! {d}")
    except:
        print(r.stdout or "(timeout/error)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EvoMap A2A Adapter")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("heartbeat")
    sub.add_parser("status")
    sub.add_parser("tasks")
    p_pub = sub.add_parser("publish")
    p_pub.add_argument("--bundle", required=True)
    args = parser.parse_args()

    if args.cmd == "heartbeat": cmd_heartbeat()
    elif args.cmd == "status": cmd_status()
    elif args.cmd == "tasks": cmd_tasks()
    elif args.cmd == "publish": cmd_publish(args.bundle)
    else: parser.print_help()
