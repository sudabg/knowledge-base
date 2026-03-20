#!/usr/bin/env python3
"""Mock EvoMap Hub - Isolated A2A server for testing.

Simulates EvoMap Hub endpoints with configurable behavior.
No rate limits, no real credit system, full validation.
"""
import json, time, hashlib, os, sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("MOCK_HUB_PORT", 8080))
LOG_FILE = Path(__file__).parent / "mock-hub.log"
STATE_FILE = Path(__file__).parent / "mock-state.json"

# In-memory state
_state = {
    "nodes": {},
    "bundles": [],
    "publish_count": 0,
    "quarantine_mode": False,  # If True, all publishes get quarantined
    "auto_promote": True,       # If True, all valid publishes get auto_promoted
}

def load_state():
    global _state
    if STATE_FILE.exists():
        try:
            _state.update(json.loads(STATE_FILE.read_text()))
        except:
            pass

def save_state():
    STATE_FILE.write_text(json.dumps(_state, indent=2, ensure_ascii=False))

def log_request(method, path, status, detail=""):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "status": status,
        "detail": detail
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def compute_asset_id(obj):
    clean = {k: v for k, v in obj.items() if k != "asset_id"}
    return "sha256:" + hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()

def validate_publish(envelope):
    """Validate a GEP-A2A publish envelope. Returns (valid, errors)."""
    errors = []
    if envelope.get("protocol") != "gep-a2a":
        errors.append("protocol must be 'gep-a2a'")
    if envelope.get("message_type") != "publish":
        errors.append("message_type must be 'publish'")
    payload = envelope.get("payload", {})
    assets = payload.get("assets", [])
    if not assets:
        errors.append("payload.assets must be a non-empty array")

    gene_found = False
    capsule_found = False
    for i, asset in enumerate(assets):
        atype = asset.get("type")
        if atype == "Gene":
            gene_found = True
            if not asset.get("signals_match"):
                errors.append(f"assets[{i}]: Gene must have signals_match")
            if not asset.get("strategy"):
                errors.append(f"assets[{i}]: Gene must have strategy")
            if not asset.get("summary"):
                errors.append(f"assets[{i}]: Gene must have summary")
        elif atype == "Capsule":
            capsule_found = True
            if not asset.get("content"):
                errors.append(f"assets[{i}]: Capsule must have content")
            if asset.get("confidence") is None:
                errors.append(f"assets[{i}]: Capsule must have confidence")
            br = asset.get("blast_radius", {})
            if not isinstance(br, dict) or "files" not in br or "lines" not in br:
                errors.append(f"assets[{i}]: Capsule blast_radius must have files and lines")
            ef = asset.get("env_fingerprint", {})
            if not isinstance(ef, dict) or "platform" not in ef or "arch" not in ef:
                errors.append(f"assets[{i}]: Capsule env_fingerprint must have platform and arch")

    if not gene_found:
        errors.append("assets must contain at least one Gene")
    if not capsule_found:
        errors.append("assets must contain at least one Capsule")

    return (len(errors) == 0, errors)


class MockHubHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._json({"service": "Mock EvoMap Hub", "version": "0.1.0", "status": "running"})
        elif self.path == "/a2a/echo":
            self._json({"echo": "pong", "ts": datetime.now(timezone.utc).isoformat()})
        elif self.path.startswith("/a2a/nodes/"):
            node_id = self.path.split("/")[-1]
            node = _state["nodes"].get(node_id, {
                "node_id": node_id,
                "status": "active",
                "survival_status": "alive",
                "credit_balance": 999,
                "reputation_score": 80.0,
                "total_published": _state["publish_count"],
                "total_promoted": _state["publish_count"],
                "total_rejected": 0,
                "online": True
            })
            self._json(node)
        elif self.path == "/a2a/config":
            self._json({
                "quarantine_mode": _state["quarantine_mode"],
                "auto_promote": _state["auto_promote"],
                "publish_count": _state["publish_count"]
            })
        else:
            self._json({"error": "not_found", "path": self.path}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else "{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._json({"error": "invalid_json"}, 400)
            return

        if self.path == "/a2a/publish":
            self._handle_publish(data)
        elif self.path == "/a2a/heartbeat":
            self._handle_heartbeat(data)
        elif self.path == "/a2a/config":
            # Update config
            for k in ["quarantine_mode", "auto_promote"]:
                if k in data:
                    _state[k] = data[k]
            save_state()
            self._json({"ok": True, "config": {k: _state[k] for k in ["quarantine_mode", "auto_promote"]}})
        else:
            self._json({"error": "not_found"}, 404)

    def _handle_publish(self, envelope):
        valid, errors = validate_publish(envelope)
        if not valid:
            log_request("POST", "/a2a/publish", 400, "; ".join(errors))
            self._json({
                "error": "validation_error",
                "message": "Request body does not match the expected schema",
                "details": [{"message": e} for e in errors]
            }, 400)
            return

        if _state["quarantine_mode"]:
            log_request("POST", "/a2a/publish", "quarantine", "quarantine_mode enabled")
            self._json({
                "protocol": "gep-a2a",
                "protocol_version": "1.0.0",
                "message_type": "decision",
                "message_id": f"msg_{int(time.time()*1000)}",
                "sender_id": "mock_hub",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "decision": "quarantine",
                    "reason": "safety_flagged",
                    "bundle_id": f"bundle_mock_{int(time.time())}",
                    "asset_ids": [compute_asset_id(a) for a in envelope.get("payload", {}).get("assets", [])]
                }
            })
            return

        # Accept or auto_promote
        decision = "auto_promoted" if _state["auto_promote"] else "accept"
        bundle_id = f"bundle_mock_{int(time.time())}"
        asset_ids = [compute_asset_id(a) for a in envelope.get("payload", {}).get("assets", [])]

        _state["publish_count"] += 1
        _state["bundles"].append({"bundle_id": bundle_id, "ts": time.time(), "decision": decision})
        save_state()

        log_request("POST", "/a2a/publish", decision, f"bundle={bundle_id}")
        self._json({
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": "decision",
            "message_id": f"msg_{int(time.time()*1000)}",
            "sender_id": "mock_hub",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "decision": decision,
                "reason": decision,
                "bundle_id": bundle_id,
                "asset_ids": asset_ids
            }
        })

    def _handle_heartbeat(self, data):
        sender = data.get("sender_id", "unknown")
        _state["nodes"][sender] = {
            "node_id": sender,
            "status": "active",
            "survival_status": "alive",
            "credit_balance": 999,
            "reputation_score": 80.0,
            "last_seen": datetime.now(timezone.utc).isoformat()
        }
        save_state()
        log_request("POST", "/a2a/heartbeat", 200, f"node={sender}")
        self._json({
            "status": "ok",
            "your_node_id": sender,
            "node_status": "active",
            "survival_status": "alive",
            "credit_balance": 999,
            "server_time": datetime.now(timezone.utc).isoformat(),
            "accountability": {"reputation_penalty": 0, "quarantine_strikes": 0},
            "available_tasks": []
        })

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # Suppress default logging


if __name__ == "__main__":
    load_state()
    server = HTTPServer(("0.0.0.0", PORT), MockHubHandler)
    print(f"🔧 Mock EvoMap Hub running on http://localhost:{PORT}")
    print(f"   Endpoints: /a2a/publish, /a2a/heartbeat, /a2a/nodes/:id, /a2a/echo")
    print(f"   Config: /a2a/config (GET=read, POST=update)")
    print(f"   Log: {LOG_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Mock Hub stopped")
        save_state()
