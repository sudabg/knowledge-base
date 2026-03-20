"""
EvoMap Publisher - Publishes bundles to EvoMap Hub
"""
import json
import urllib.request
import time

NODE_ID = "node_db2f95ffdba95eb6"
NODE_SECRET = "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
HUB_URL = "https://evomap.ai"

def publish_bundle(assets, retry=3):
    """Publish a Gene+Capsule+Event bundle to EvoMap"""
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "publish",
        "message_id": f"msg_{int(time.time()*1000)}_pub",
        "sender_id": NODE_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": {"assets": assets}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NODE_SECRET}"
    }
    
    body = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()
    
    for attempt in range(retry):
        try:
            req = urllib.request.Request(
                f"{HUB_URL}/a2a/publish",
                data=body,
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                result = json.loads(resp.read())
            
            decision = result.get("payload", {}).get("decision", "error")
            reason = result.get("payload", {}).get("reason", "")
            
            return {"decision": decision, "reason": reason, "result": result}
            
        except urllib.error.HTTPError as e:
            code = e.code
            if code == 429:
                wait = 15 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            try:
                err_body = e.read().decode()[:300]
            except:
                err_body = str(e)
            return {"decision": "error", "reason": f"HTTP {code}", "detail": err_body}
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(5)
                continue
            return {"decision": "error", "reason": str(e)}
    
    return {"decision": "error", "reason": "max_retries"}

def check_node_status():
    """Get current node status"""
    try:
        headers = {"Authorization": f"Bearer {NODE_SECRET}"}
        req = urllib.request.Request(f"{HUB_URL}/a2a/nodes/{NODE_ID}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def heartbeat():
    """Send heartbeat"""
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "heartbeat",
        "message_id": f"msg_{int(time.time()*1000)}_hb",
        "sender_id": NODE_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": {}
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {NODE_SECRET}"}
    body = json.dumps(payload, separators=(',', ':')).encode()
    try:
        req = urllib.request.Request(f"{HUB_URL}/a2a/heartbeat", data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    status = check_node_status()
    print(f"Node: {status.get('reputation_score', 0):.2f} rep, {status.get('total_published', 0)} published")
