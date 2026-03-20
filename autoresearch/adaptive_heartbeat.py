#!/usr/bin/env python3
"""
自适应 EvoMap 心跳 — 带退避策略，自动选择最优端点
用法: python3 adaptive_heartbeat.py
"""

import json, urllib.request, os, time, sys
from datetime import datetime, timedelta

TOKEN = "d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14"
NODE_ID = "node_db2f95ffdba95eb6"
STATE_FILE = os.path.expanduser("~/workspace/agent/workspace/.learnings/heartbeat_state.json")
HUB = "https://evomap.ai"

# 静默运行配置
SILENT_MODE = True  # 静默模式：成功时不打印, 异常时才打印
NORMAL_REPORT_INTERVAL = 6 * 60 * 60  # 正常报告间隔: 6小时
LAST_REPORT_TIME = 0

class SilentLogger:
    """静默日志记录器"""
    def __init__(self):
        self.last_report_time = 0
        
    def should_report(self):
        """是否应该报告"""
        now = time.time()
        if now - self.last_report_time > NORMAL_REPORT_INTERVAL:
            self.last_report_time = now
            return True
        return False
    
    def info(self, msg):
        """信息级别日志"""
        if not SILENT_MODE:
            print(f"ℹ️ {msg}")
    
    def success(self, msg):
        """成功日志"""
        if not SILENT_MODE:
            print(f"✅ {msg}")
    
    def error(self, msg):
        """错误日志"""
        print(f"❌ {msg}")

logger = SilentLogger()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"heartbeat_failures": 0, "hello_failures": 0, "last_success": None, "last_endpoint": None, "backoff_until": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def api_call(endpoint):
    """调用 EvoMap API"""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    msg_id = f"msg_hb_{int(time.time())}_{os.urandom(4).hex()}"
    
    try:
        url = f"{HUB}{endpoint}"
        # 根据端点准备请求体
        if endpoint == "/a2a/heartbeat":
            payload = {
                "node_id": NODE_ID,
                "timestamp": ts,
                "msg_id": msg_id
            }
            data = json.dumps(payload).encode('utf-8')
        elif endpoint == "/a2a/hello":
            payload = {
                "node_id": NODE_ID,
                "timestamp": ts,
                "msg_id": msg_id
            }
            data = json.dumps(payload).encode('utf-8')
        else:
            data = b''
        
        req = urllib.request.Request(url, data=data if data else None, method="POST")
        req.add_header("Authorization", f"Bearer {TOKEN}")
        if data:
            req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            if endpoint == "/a2a/heartbeat":
                # 处理心跳响应（支持新旧两种格式）
                node = None
                # 新版：直接在当前对象
                if data.get("your_node_id") == NODE_ID:
                    node = data
                # 旧版：在 nodes 数组中
                else:
                    nodes = data.get("nodes", [])
                    for n in nodes:
                        if n.get("node_id") == NODE_ID:
                            node = n
                            break
                
                if node:
                    credit = node.get("credit_balance") or node.get("credit", 0)
                    rep = node.get("reputation_score", 0)
                    tasks = node.get("available_tasks", [])
                    
                    cache_file = os.path.expanduser("~/workspace/agent/workspace/.learnings/last_heartbeat.json")
                    cache = {
                        "status": "active",
                        "survival": "alive",
                        "credit": credit,
                        "reputation_score": rep,
                        "total_published": node.get("total_published", 0),
                        "total_promoted": node.get("total_promoted", 0),
                        "total_rejected": node.get("total_rejected", 0),
                        "reputation_penalty": node.get("reputation_penalty", 0),
                        "quarantine_strikes": node.get("quarantine_strikes", 0),
                        "tasks_count": len(tasks),
                        "available_tasks": [
                            {"task_id": t.get("task_id", ""), "topic": t.get("topic", ""), "bounty": t.get("bounty", 0)}
                            for t in tasks[:10]
                        ],
                        "highest_bounty": max((t.get("bounty", 0) for t in tasks), default=0),
                        "updated": datetime.now().strftime("%H:%M")
                    }
                    with open(cache_file, "w") as f:
                        json.dump(cache, f)
                    
                    logger.success(f"✅ heartbeat: credit={credit} rep={rep} tasks={len(tasks)}")
                    return cache
                
                logger.error(f"❌ 心跳响应中未找到节点: {data}")
                return None
            
            return data
            
    except Exception as e:
        # 记录失败类型
        error_type = type(e).__name__
        if "timeout" in str(e).lower():
            logger.error(f"❌ 超时错误: {e}")
        else:
            logger.error(f"❌ 错误 ({error_type}): {e}")
        return None

def heartbeat():
    """执行心跳"""
    state = load_state()
    now = datetime.now()
    
    # 检查退避时间
    if state.get("backoff_until"):
        backoff = datetime.fromisoformat(state.get("backoff_until"))
        if now < backoff:
            logger.error(f"⏰ 退避中，等待 {backoff - now}")
            return None
    
    # 执行心跳
    logger.info("🔄 执行 EvoMap 心跳...")
    result = api_call("/a2a/heartbeat")
    
    if result:
        state["last_success"] = now.isoformat()
        state["heartbeat_failures"] = 0
        state["hello_failures"] = 0
        save_state(state)
        
        # 每6小时发送一次状态报告
        if logger.should_report():
            print(f"📊 心跳完成：Credit={result.get('credit', 'N/A')}, Rep={result.get('reputation_score', 'N/A')}, Tasks={result.get('tasks_count', 'N/A')}")
        
        return result
    else:
        # 失败时增加失败计数
        state["heartbeat_failures"] = state.get("heartbeat_failures", 0) + 1
        save_state(state)
        return None

if __name__ == "__main__":
    heartbeat()