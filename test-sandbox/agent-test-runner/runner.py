#!/usr/bin/env python3
"""Agent Test Runner - Execute evolution cycles against mock hub.

Usage:
    python3 runner.py --hub http://localhost:8080 --cycles 3
    python3 runner.py --hub http://localhost:8080 --fixture fixtures/simple_capsule.json
"""
import argparse, json, time, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def compute_asset_id(obj):
    clean = {k: v for k, v in obj.items() if k != "asset_id"}
    return "sha256:" + hashlib.sha256(canonical_json(clean).encode()).hexdigest()

def make_envelope(node_id, assets):
    return {
        "protocol": "gep-a2a",
        "protocol_version": "1.5.0",
        "message_type": "publish",
        "message_id": f"msg_test_{int(time.time()*1000)}",
        "sender_id": node_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": {"assets": assets}
    }

def make_test_capsule(topic="test_capsule", content=None):
    gene = {
        "type": "Gene",
        "schema_version": "1.5.0",
        "category": "repair",
        "signals_match": ["test_signal", "mock_hub"],
        "summary": f"Test gene for {topic}",
        "strategy": ["Generate test content", "Validate against mock hub", "Verify response"],
        "model_name": "test-runner"
    }
    capsule = {
        "type": "Capsule",
        "schema_version": "1.5.0",
        "trigger": ["test_signal"],
        "gene": "",  # fill after
        "summary": f"Test capsule for {topic}",
        "confidence": 0.85,
        "content": content or f"这是一个测试 capsule，主题为 {topic}。Mock Hub 验证用例。" * 5,
        "blast_radius": {"files": 1, "lines": 10},
        "outcome": {"status": "success", "score": 0.85},
        "env_fingerprint": {"platform": "linux", "arch": "x64"},
        "success_streak": 1,
        "model_name": "test-runner"
    }
    event = {
        "type": "EvolutionEvent",
        "intent": "repair",
        "capsule_id": "",  # fill after
        "genes_used": [],  # fill after
        "outcome": {"status": "success", "score": 0.85},
        "mutations_tried": 1,
        "total_cycles": 1,
        "model_name": "test-runner"
    }
    # Compute IDs
    gene_id = compute_asset_id(gene)
    gene["asset_id"] = gene_id
    capsule["gene"] = gene_id
    capsule_id = compute_asset_id(capsule)
    capsule["asset_id"] = capsule_id
    event["capsule_id"] = capsule_id
    event["genes_used"] = [gene_id]
    event["asset_id"] = compute_asset_id(event)
    return [gene, capsule, event]


def send_publish(hub_url, node_id, assets):
    import urllib.request
    envelope = make_envelope(node_id, assets)
    payload = json.dumps(envelope).encode()
    req = urllib.request.Request(
        f"{hub_url}/a2a/publish",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except Exception as e:
        return {"error": str(e)}


def send_heartbeat(hub_url, node_id):
    import urllib.request
    payload = json.dumps({
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "heartbeat",
        "message_id": f"msg_hb_{int(time.time())}",
        "sender_id": node_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": {}
    }).encode()
    req = urllib.request.Request(
        f"{hub_url}/a2a/heartbeat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def run_cycles(hub_url, node_id, cycles, delay=2):
    print(f"🚀 Running {cycles} evolution cycles against {hub_url}")
    print(f"   Node: {node_id}")
    print()

    results = {"success": 0, "quarantine": 0, "error": 0}

    for i in range(cycles):
        cycle_num = i + 1
        print(f"--- Cycle {cycle_num}/{cycles} ---")

        # Heartbeat
        hb = send_heartbeat(hub_url, node_id)
        if "error" in hb:
            print(f"  💓 Heartbeat: ERROR - {hb['error']}")
        else:
            print(f"  💓 Heartbeat: {hb.get('node_status', 'unknown')} | credit={hb.get('credit_balance', '?')}")

        # Publish
        assets = make_test_capsule(topic=f"test_cycle_{cycle_num}")
        result = send_publish(hub_url, node_id, assets)

        payload = result.get("payload", {})
        decision = payload.get("decision", "unknown")
        reason = payload.get("reason", "")

        if decision == "auto_promoted":
            print(f"  📦 Publish: ✅ auto_promoted | bundle={payload.get('bundle_id', '?')}")
            results["success"] += 1
        elif decision == "accept":
            print(f"  📦 Publish: ✅ accepted | bundle={payload.get('bundle_id', '?')}")
            results["success"] += 1
        elif decision == "quarantine":
            print(f"  📦 Publish: ⚠️ quarantine | reason={reason}")
            results["quarantine"] += 1
        else:
            err = result.get("error", result.get("message", "unknown"))
            print(f"  📦 Publish: ❌ {err}")
            results["error"] += 1

        if i < cycles - 1:
            time.sleep(delay)
        print()

    print("=" * 50)
    print(f"Results: ✅ {results['success']} | ⚠️ {results['quarantine']} | ❌ {results['error']}")
    return results


def main():
    parser = argparse.ArgumentParser(description="EvoMap Agent Test Runner")
    parser.add_argument("--hub", default="http://localhost:8080", help="Mock hub URL")
    parser.add_argument("--node", default="test_node_001", help="Test node ID")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles")
    parser.add_argument("--delay", type=float, default=2, help="Delay between cycles (s)")
    parser.add_argument("--fixture", help="Use specific fixture file")
    args = parser.parse_args()

    run_cycles(args.hub, args.node, args.cycles, args.delay)


if __name__ == "__main__":
    main()
