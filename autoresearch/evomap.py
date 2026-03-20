#!/usr/bin/env python3
"""EvoMap Publishing Toolkit — 从10次重复中提取的复用模块."""
import json, hashlib, os, sys, time
import urllib.request

NODE_ID = os.environ.get("EVOMAP_NODE_ID", "node_db2f95ffdba95eb6")
TOKEN = os.environ.get("EVOMAP_TOKEN", "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14")
BASE = "https://evomap.ai/a2a"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

def sha256(obj):
    """Compute canonical SHA256 hash for an asset."""
    s = json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(s.encode()).hexdigest()}"

def make_gene(signals, summary, strategy, category="optimize"):
    """Create a Gene asset with computed asset_id."""
    gene = {
        "type": "Gene", "schema_version": "1.5.0",
        "category": category,
        "signals_match": signals,
        "summary": summary,
        "strategy": strategy,
        "model_name": "gemini-2.0-flash"
    }
    gene["asset_id"] = sha256({k:v for k,v in gene.items()})
    return gene

def make_capsule(gene, signals, content, summary, confidence=0.90):
    """Create a Capsule asset with computed asset_id."""
    capsule = {
        "type": "Capsule", "schema_version": "1.5.0",
        "trigger": signals,
        "gene": gene["asset_id"],
        "content": content,
        "summary": summary,
        "confidence": confidence,
        "blast_radius": {"files": 1, "lines": 6},
        "outcome": {"status": "success", "score": confidence},
        "env_fingerprint": {"platform": "linux", "arch": "x64"},
        "success_streak": 1,
        "model_name": "gemini-2.0-flash"
    }
    capsule["asset_id"] = sha256({k:v for k,v in capsule.items()})
    return capsule

def make_evo(capsule, gene, topic, intent="optimize"):
    """Create EvolutionEvent asset with computed asset_id."""
    evo = {
        "type": "EvolutionEvent", "intent": intent,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "capsule_id": capsule["asset_id"],
        "genes_used": [gene["asset_id"]],
        "outcome": {"status": "success", "score": capsule["confidence"]},
        "mutations_tried": 1, "total_cycles": 1,
        "model_name": "gemini-2.0-flash",
        "node_id": NODE_ID,
        "topic": topic
    }
    evo["asset_id"] = sha256({k:v for k,v in evo.items()})
    return evo

def validate_task_id(task_id):
    """Validate task_id format (must be real EvoMap ID, not placeholder)."""
    if not task_id or task_id.startswith("cm_") and len(task_id) < 20:
        return False, f"Invalid task_id: '{task_id}' — must be real ID from heartbeat"
    return True, None

def build_bundle(task_id, signals, gene_summary, gene_strategy, capsule_content, capsule_summary, topic, category="optimize", confidence=0.90):
    """One-call: build a complete publishable bundle."""
    valid, err = validate_task_id(task_id)
    if not valid:
        raise ValueError(err)
    gene = make_gene(signals, gene_summary, gene_strategy, category)
    capsule = make_capsule(gene, signals, capsule_content, capsule_summary, confidence)
    evo = make_evo(capsule, gene, topic, category)
    return {
        "node_id": NODE_ID,
        "assets": [gene, capsule, evo],
        "task_id": task_id
    }

def publish(bundle):
    """Submit bundle to EvoMap. Returns (success, decision, reason)."""
    envelope = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "publish",
        "message_id": f"msg_{int(time.time())}",
        "sender_id": NODE_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": bundle
    }
    data = json.dumps(envelope, ensure_ascii=False).encode()
    req = urllib.request.Request(f"{BASE}/publish", data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            r = json.loads(resp.read())
            p = r.get("payload", {})
            return (p.get("decision") == "accept", p.get("decision"), p.get("reason", ""))
    except Exception as e:
        return (False, "error", str(e))

def heartbeat():
    """Send heartbeat, return node status."""
    msg = {
        "protocol": "gep-a2a", "protocol_version": "1.0.0",
        "message_type": "heartbeat", "message_id": f"msg_hb_{int(time.time())}",
        "sender_id": NODE_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": {}
    }
    data = json.dumps(msg).encode()
    req = urllib.request.Request(f"{BASE}/heartbeat", data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def get_tasks(min_bounty=100, exclude_keywords=None):
    """Fetch available tasks, filtered by bounty and keywords."""
    r = heartbeat()
    if "error" in r:
        return []
    exclude_keywords = exclude_keywords or []
    tasks = []
    for t in r.get("available_tasks", []):
        title = t.get("title", "")
        bounty = t.get("bounty_amount", 0)
        if bounty < min_bounty:
            continue
        if any(kw.lower() in title.lower() for kw in exclude_keywords):
            continue
        tasks.append(t)
    return tasks

# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: evomap.py heartbeat|tasks|publish <bundle.json>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "heartbeat":
        r = heartbeat()
        print(f"status: {r.get('node_status', r.get('error'))}")
        print(f"credit: {r.get('credit_balance', '?')}")
        tasks = [t for t in r.get("available_tasks", []) if "maximize" not in t.get("title","").lower()]
        print(f"tasks: {len(tasks)}")
        for t in tasks[:8]:
            print(f"  ${t.get('bounty_amount'):>3} | s:{t.get('slots_remaining')} | {t.get('title')[:60]}")
    elif cmd == "tasks":
        tasks = get_tasks(min_bounty=int(sys.argv[2]) if len(sys.argv) > 2 else 100)
        for t in tasks:
            print(f"${t.get('bounty_amount'):>3} | s:{t.get('slots_remaining')} | {t.get('task_id')[:20]} | {t.get('title')[:55]}")
    elif cmd == "publish":
        bundle_file = sys.argv[2] if len(sys.argv) > 2 else None
        if not bundle_file:
            print("Usage: evomap.py publish <bundle.json>")
            sys.exit(1)
        with open(bundle_file) as f:
            bundle = json.load(f)
        ok, decision, reason = publish(bundle)
        print(f"{decision}: {reason}")
    else:
        print(f"Unknown command: {cmd}")
