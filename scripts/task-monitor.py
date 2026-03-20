#!/usr/bin/env python3
"""Monitor EvoMap tasks and attempt to claim high bounty ones"""
import json, urllib.request, time

TOKEN = "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
NODE = "node_db2f95ffdba95eb6"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

def get_tasks():
    req = urllib.request.Request("https://evomap.ai/a2a/task/list?limit=20", headers=HEADERS)
    return json.loads(urllib.request.urlopen(req, timeout=10).read()).get("tasks", [])

def claim(task_id):
    data = json.dumps({"task_id": task_id, "node_id": NODE}).encode()
    req = urllib.request.Request("https://evomap.ai/a2a/task/claim", data=data, headers=HEADERS)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception as e:
        return {"error": str(e)}

def main():
    tasks = get_tasks()
    available = [t for t in tasks if t.get("slots_remaining", 0) > 0 and t.get("bounty_amount", 0) >= 50]
    print(f"Found {len(available)} available tasks with bounty >= 50")
    for t in available[:3]:
        result = claim(t["task_id"])
        status = result.get("status", result.get("error", "unknown"))
        print(f"  [{t['bounty_amount']}] {status}: {t['title'][:50]}")

if __name__ == "__main__":
    main()
