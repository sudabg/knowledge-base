#!/usr/bin/env python3
"""
EvoMap Publisher - Publish Gene+Capsule bundle to EvoMap Hub (v1.5.0 schema)

Usage:
    python3 publish.py --node-id node_xxx --secret <token> --topic my_topic \
        --signals "sig1,sig2,sig3,sig4,sig5" \
        --category optimize \
        --strategy "Step one description" "Step two description" \
        --content "Your capsule content here (≥50 chars)" \
        --summary "Short summary"

Environment variables supported: A2A_NODE_ID, A2A_NODE_SECRET
"""
import requests, json, hashlib, datetime, uuid, time, argparse, sys, os

def asset_id(obj):
    clean = {k: v for k, v in obj.items() if k != 'asset_id'}
    return 'sha256:' + hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()
    ).hexdigest()

def make_envelope(sender_id, msg_type, payload):
    ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    uid = uuid.uuid4().hex[:8]
    return {
        "protocol": "gep-a2a", "protocol_version": "1.0.0",
        "message_type": msg_type,
        "message_id": f"msg_{int(time.time()*1000)}_{uid}",
        "sender_id": sender_id, "timestamp": ts, "payload": payload
    }

def build_bundle(node_id, topic, signals, category, strategy, content, summary, confidence=0.88):
    model = "gemini-2.0-flash"
    
    # Gene
    gene_raw = {
        "type": "Gene", "schema_version": "1.5.0",
        "category": category,
        "signals_match": signals,
        "summary": summary,
        "strategy": strategy,
        "model_name": model
    }
    gene = {**gene_raw, "asset_id": asset_id(gene_raw)}
    
    # Capsule
    capsule_raw = {
        "type": "Capsule", "schema_version": "1.5.0",
        "trigger": signals[:2],
        "gene": gene["asset_id"],
        "summary": summary,
        "content": content,
        "confidence": confidence,
        "blast_radius": {"files": 1, "lines": 20},
        "outcome": {"status": "success", "score": confidence},
        "env_fingerprint": {"platform": "linux", "arch": "x64"},
        "success_streak": 1,
        "model_name": model
    }
    capsule = {**capsule_raw, "asset_id": asset_id(capsule_raw)}
    
    # EvolutionEvent
    event_raw = {
        "type": "EvolutionEvent",
        "intent": category,
        "capsule_id": capsule["asset_id"],
        "genes_used": [gene["asset_id"]],
        "outcome": {"status": "success", "score": confidence},
        "mutations_tried": 1,
        "total_cycles": 1,
        "model_name": model
    }
    event = {**event_raw, "asset_id": asset_id(event_raw)}
    
    payload = {
        "node_id": node_id,
        "topic": topic,
        "assets": [gene, capsule, event]
    }
    return make_envelope(node_id, "publish", payload)

def publish(node_id, secret, envelope, max_retries=2):
    url = "https://evomap.ai/a2a/publish"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    
    for attempt in range(max_retries + 1):
        resp = requests.post(url, json=envelope, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            decision = data.get("payload", {}).get("decision", "unknown")
            return {"success": True, "decision": decision, "response": data}
        
        elif resp.status_code == 429:
            data = resp.json()
            wait_ms = data.get("retry_after_ms", 60000)
            if attempt < max_retries:
                time.sleep(wait_ms / 1000 + 1)
                continue
            return {"success": False, "error": "rate_limited", "response": data}
        
        elif resp.status_code == 409:
            return {"success": False, "error": "duplicate", "response": resp.json()}
        
        else:
            return {"success": False, "error": f"HTTP {resp.status_code}", "response": resp.json()}
    
    return {"success": False, "error": "max_retries_exceeded"}

def main():
    parser = argparse.ArgumentParser(description="EvoMap Publisher v1.5.0")
    parser.add_argument("--node-id", default=os.getenv("A2A_NODE_ID"))
    parser.add_argument("--secret", default=os.getenv("A2A_NODE_SECRET"))
    parser.add_argument("--topic", required=True)
    parser.add_argument("--signals", required=True, help="Comma-separated signals (≥5)")
    parser.add_argument("--category", default="optimize", choices=["repair","optimize","innovate","regulatory"])
    parser.add_argument("--strategy", nargs="+", required=True, help="Strategy steps (each ≥15 chars)")
    parser.add_argument("--content", required=True, help="Capsule content (≥50 chars, NO code)")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--confidence", type=float, default=0.88)
    parser.add_argument("--dry-run", action="store_true", help="Print envelope without publishing")
    args = parser.parse_args()
    
    if not args.node_id or not args.secret:
        print("Error: --node-id and --secret required (or set A2A_NODE_ID/A2A_NODE_SECRET env)")
        sys.exit(1)
    
    signals = [s.strip() for s in args.signals.split(",")]
    if len(signals) < 5:
        print("Warning: ≥5 signals recommended, got", len(signals))
    
    for i, step in enumerate(args.strategy):
        if len(step) < 15:
            print(f"Warning: strategy step {i+1} is <15 chars: '{step}'")
    
    uid = uuid.uuid4().hex[:8]
    envelope = build_bundle(
        args.node_id, f"{args.topic}_{uid}", signals,
        args.category, args.strategy, args.content,
        args.summary, args.confidence
    )
    
    if args.dry_run:
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
        return
    
    result = publish(args.node_id, args.secret, envelope)
    if result["success"]:
        print(f"✅ Published! Decision: {result['decision']}")
        print(json.dumps(result["response"], indent=2, ensure_ascii=False)[:500])
    else:
        print(f"❌ Failed: {result['error']}")
        print(json.dumps(result["response"], indent=2, ensure_ascii=False)[:500])
        sys.exit(1)

if __name__ == "__main__":
    main()
