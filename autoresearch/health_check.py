#!/usr/bin/env python3
"""
统一健康检查 — 检查所有外部依赖状态
用法: python3 health_check.py [--fix]
"""

import json, subprocess, urllib.request, os, sys
from datetime import datetime

def check(name, func, auto_fix=None):
    """运行检查并返回结果"""
    try:
        ok, detail = func()
        status = "✅" if ok else "⚠️"
        result = {"name": name, "ok": ok, "detail": detail}
        if not ok and auto_fix and "--fix" in sys.argv:
            fix_ok, fix_detail = auto_fix()
            result["fixed"] = fix_ok
            result["fix_detail"] = fix_detail
            status = "🔧" if fix_ok else "❌"
        print(f"{status} {name}: {detail}")
        return result
    except Exception as e:
        print(f"❌ {name}: {e}")
        return {"name": name, "ok": False, "detail": str(e)}

def check_github():
    """GitHub token 有效性"""
    try:
        req = urllib.request.Request("https://api.github.com/user", 
            headers={"Authorization": f"Bearer {open(os.path.expanduser('~/.config/gh/hosts.yml')).read().split('oauth_token:')[1].strip().split()[0]}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            user = json.loads(r.read())
        return True, f"Logged in as {user.get('login','?')}"
    except Exception as e:
        return False, f"Auth failed: {e}"

def check_evomap():
    """EvoMap 节点状态"""
    try:
        token = "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
        node_id = "node_db2f95ffdba95eb6"
        data = json.dumps({"protocol":"gep-a2a","protocol_version":"1.0.0","message_type":"hello","message_id":"msg_hc","sender_id":node_id,"timestamp":datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),"payload":{"capabilities":{},"env_fingerprint":{"platform":"linux","arch":"x64"}}}).encode()
        req = urllib.request.Request("https://evomap.ai/a2a/hello", data=data,
            headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        p = resp.get("payload",{})
        credit = p.get("credit_balance","?")
        rep = p.get("capability_profile",{}).get("reputation","?")
        return True, f"Credit: {credit}, Rep: {rep}"
    except Exception as e:
        return False, f"Error: {e}"

def check_dashboard():
    """Dashboard 服务连通性"""
    try:
        with urllib.request.urlopen("http://localhost:8888/api/status", timeout=5) as r:
            data = json.loads(r.read())
        return True, f"Running on port 8888, agent: {data.get('agent','?')}"
    except:
        return False, "Dashboard not running on port 8888"

def check_dashboard_data():
    """Dashboard 数据时效性"""
    try:
        with open(os.path.expanduser("~/workspace/agent/workspace/dashboard/last_heartbeat.json")) as f:
            data = json.load(f)
        last = data.get("last_check","")
        if last:
            from datetime import datetime as dt
            last_dt = dt.fromisoformat(last.replace("+08:00","+08:00"))
            age_min = (dt.now(last_dt.tzinfo) - last_dt).total_seconds() / 60
            if age_min < 15:
                return True, f"Updated {int(age_min)}min ago"
            else:
                return False, f"Stale: {int(age_min)}min ago"
        return False, "No last_check timestamp"
    except Exception as e:
        return False, f"Error: {e}"

def check_cloudflare():
    """Cloudflare 隧道连通性"""
    try:
        # 读取正确的隧道 URL
        result = subprocess.run(["grep","-o","https://[a-z0-9-]*.trycloudflare.com",
            "/tmp/cloudflared-tunnel3.log"], capture_output=True, text=True, timeout=5)
        url = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else None
        if not url:
            return False, "No tunnel URL found"
        with urllib.request.urlopen(f"{url}/api/status", timeout=5) as r:
            json.loads(r.read())
        return True, f"Accessible: {url}"
    except Exception as e:
        return False, f"Tunnel issue: {e}"

def fix_dashboard():
    """重启 Dashboard 服务"""
    try:
        subprocess.run(["pkill","-f","http.server 8888"], capture_output=True, timeout=5)
        subprocess.Popen(["python3","-m","http.server","8888","--bind","0.0.0.0"],
            cwd=os.path.expanduser("~/workspace/agent/workspace/dashboard"),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import time; time.sleep(1)
        with urllib.request.urlopen("http://localhost:8888/api/status", timeout=5) as r:
            json.loads(r.read())
        return True, "Dashboard restarted on port 8888"
    except Exception as e:
        return False, f"Restart failed: {e}"

def main():
    print("=" * 50)
    print(f"🏥 Health Check — {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    results = []
    results.append(check("GitHub Token", check_github))
    results.append(check("EvoMap Node", check_evomap))
    results.append(check("Dashboard Service", check_dashboard, fix_dashboard))
    results.append(check("Dashboard Data", check_dashboard_data))
    results.append(check("Cloudflare Tunnel", check_cloudflare))
    
    # 汇总
    failed = [r for r in results if not r["ok"]]
    print("-" * 50)
    if failed:
        print(f"⚠️ {len(failed)} issue(s): {', '.join(r['name'] for r in failed)}")
        if "--fix" not in sys.argv:
            print("💡 Run with --fix to attempt auto-repair")
    else:
        print("✅ All systems operational")
    
    # 写入状态文件
    status = {
        "timestamp": datetime.now().isoformat(),
        "all_ok": len(failed) == 0,
        "issues": [r["name"] for r in failed],
        "results": results
    }
    with open(os.path.expanduser("~/workspace/agent/workspace/.learnings/health_status.json"), "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
