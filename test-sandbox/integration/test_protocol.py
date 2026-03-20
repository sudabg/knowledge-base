"""Integration tests for Mock Hub protocol validation."""
import json, time, hashlib, urllib.request, os, pytest

HUB_URL = os.environ.get("MOCK_HUB_URL", "http://localhost:8080")

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def compute_id(obj):
    clean = {k: v for k, v in obj.items() if k != "asset_id"}
    return "sha256:" + hashlib.sha256(canonical_json(clean).encode()).hexdigest()

def post(path, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(f"{HUB_URL}{path}", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def make_valid_envelope():
    gene = {
        "type": "Gene", "schema_version": "1.5.0", "category": "repair",
        "signals_match": ["test"], "summary": "Test gene", "strategy": ["Test step"],
        "model_name": "test"
    }
    capsule = {
        "type": "Capsule", "schema_version": "1.5.0", "trigger": ["test"],
        "gene": compute_id(gene), "summary": "Test capsule", "confidence": 0.9,
        "content": "Test content " * 20,
        "blast_radius": {"files": 1, "lines": 10},
        "outcome": {"status": "success", "score": 0.9},
        "env_fingerprint": {"platform": "linux", "arch": "x64"},
        "success_streak": 1, "model_name": "test"
    }
    gene["asset_id"] = compute_id(gene)
    capsule["asset_id"] = compute_id(capsule)
    event = {
        "type": "EvolutionEvent", "intent": "repair",
        "capsule_id": capsule["asset_id"], "genes_used": [gene["asset_id"]],
        "outcome": {"status": "success", "score": 0.9},
        "mutations_tried": 1, "total_cycles": 1, "model_name": "test"
    }
    event["asset_id"] = compute_id(event)
    return {
        "protocol": "gep-a2a", "protocol_version": "1.5.0", "message_type": "publish",
        "message_id": f"msg_test_{int(time.time()*1000)}", "sender_id": "test_node",
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": {"assets": [gene, capsule, event]}
    }


class TestHealthCheck:
    def test_root(self):
        req = urllib.request.Request(HUB_URL + "/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            assert data["service"] == "Mock EvoMap Hub"

    def test_echo(self):
        req = urllib.request.Request(HUB_URL + "/a2a/echo")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            assert data["echo"] == "pong"


class TestHeartbeat:
    def test_heartbeat(self):
        status, data = post("/a2a/heartbeat", {
            "protocol": "gep-a2a", "protocol_version": "1.0.0",
            "message_type": "heartbeat", "message_id": "msg_hb",
            "sender_id": "test_node", "timestamp": "2026-01-01T00:00:00Z",
            "payload": {}
        })
        assert status == 200
        assert data["status"] == "ok"
        assert data["node_status"] == "active"

    def test_node_status(self):
        post("/a2a/heartbeat", {
            "protocol": "gep-a2a", "protocol_version": "1.0.0",
            "message_type": "heartbeat", "message_id": "msg_hb2",
            "sender_id": "test_node", "timestamp": "2026-01-01T00:00:00Z",
            "payload": {}
        })
        req = urllib.request.Request(HUB_URL + "/a2a/nodes/test_node")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            assert data["status"] == "active"


class TestPublish:
    def test_valid_publish(self):
        envelope = make_valid_envelope()
        status, data = post("/a2a/publish", envelope)
        assert status == 200
        decision = data["payload"]["decision"]
        assert decision in ("accept", "auto_promoted")

    def test_invalid_protocol(self):
        envelope = make_valid_envelope()
        envelope["protocol"] = "wrong"
        status, data = post("/a2a/publish", envelope)
        assert status == 400
        assert data["error"] == "validation_error"

    def test_missing_gene(self):
        envelope = make_valid_envelope()
        # Remove Gene assets
        envelope["payload"]["assets"] = [
            a for a in envelope["payload"]["assets"] if a["type"] != "Gene"
        ]
        status, data = post("/a2a/publish", envelope)
        assert status == 400

    def test_missing_capsule(self):
        envelope = make_valid_envelope()
        envelope["payload"]["assets"] = [
            a for a in envelope["payload"]["assets"] if a["type"] != "Capsule"
        ]
        status, data = post("/a2a/publish", envelope)
        assert status == 400


class TestQuarantineMode:
    def teardown_method(self):
        # Reset quarantine mode after each test
        post("/a2a/config", {"quarantine_mode": False, "auto_promote": True})

    def test_quarantine_mode(self):
        # Enable quarantine mode
        post("/a2a/config", {"quarantine_mode": True})

        envelope = make_valid_envelope()
        status, data = post("/a2a/publish", envelope)
        assert data["payload"]["decision"] == "quarantine"

        # Disable quarantine mode
        post("/a2a/config", {"quarantine_mode": False})

        # Should work again
        envelope = make_valid_envelope()
        status, data = post("/a2a/publish", envelope)
        assert data["payload"]["decision"] in ("accept", "auto_promoted")
