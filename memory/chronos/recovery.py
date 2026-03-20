#!/usr/bin/env python3
"""
LEAFE Recovery v1.0 — 错误恢复策略库
灵感来自 LEAFE 论文：从反思经验中内化恢复能力
核心思想：错误 → 回溯 → 探索替代路径 → 记录有效策略 → 下次应用
"""

import json, os, sys, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path('/home/gem/workspace/agent/workspace')
RECOVERY_DB = WORKSPACE / 'memory/chronos/recovery_strategies.json'

# ─── 内置恢复策略（种子知识） ───

SEED_STRATEGIES = [
    {
        "id": "rate_limit_429",
        "error_pattern": "429|rate.?limit|too many requests",
        "category": "api_rate_limit",
        "recovery_steps": [
            "等待 10 秒后重试",
            "连续 3 次失败后退避 60 秒",
            "退避期间执行其他任务",
            "记录限流频率，超过 10 次/日调整发布策略"
        ],
        "success_count": 0,
        "last_applied": None,
        "source": "seed"
    },
    {
        "id": "timeout_read",
        "error_pattern": "Read timed out|read operation timed out",
        "category": "api_timeout",
        "recovery_steps": [
            "检查目标服务是否在线（curl -s -o /dev/null -w '%{http_code}'）",
            "增加超时时间（5s → 15s）",
            "如果节点查询成功但操作超时，说明服务端处理慢，等待后重试",
            "避免在同一端点连续超时 3 次"
        ],
        "success_count": 0,
        "last_applied": None,
        "source": "seed"
    },
    {
        "id": "server_busy_503",
        "error_pattern": "503|server_busy|Service Unavailable",
        "category": "api_server",
        "recovery_steps": [
            "503 表示服务端过载，非本节点问题",
            "等待 retry_after_ms 指定的时间",
            "优先级低的发布操作延后 30 分钟",
            "继续维持心跳（即使失败也不影响节点状态）"
        ],
        "success_count": 0,
        "last_applied": None,
        "source": "seed"
    },
    {
        "id": "json_decode_error",
        "error_pattern": "JSONDecodeError|Expecting value|invalid json",
        "category": "data_parse",
        "recovery_steps": [
            "检查响应体是否为空或 HTML 错误页",
            "打印前 200 字符诊断实际返回内容",
            "如果是 rate limit HTML 页面，转用 rate_limit_429 策略",
            "增加错误处理，检查 HTTP status code 再解析"
        ],
        "success_count": 0,
        "last_applied": None,
        "source": "seed"
    },
    {
        "id": "network_unreachable",
        "error_pattern": "network_frozen|Network.*unreachable|Connection.*refused",
        "category": "network",
        "recovery_steps": [
            "检查网络连通性（ping 8.8.8.8）",
            "检查 DNS 解析（nslookup evomap.ai）",
            "尝试通过代理重试（如配置了 Xray）",
            "记录故障时间，持续超过 10 分钟通知用户"
        ],
        "success_count": 0,
        "last_applied": None,
        "source": "seed"
    },
    {
        "id": "file_not_found",
        "error_pattern": "FileNotFoundError|No such file",
        "category": "filesystem",
        "recovery_steps": [
            "检查文件路径是否正确（可能用了错误的工作目录）",
            "使用绝对路径而非相对路径",
            "如果需要创建文件，先确保父目录存在（mkdir -p）",
            "检查文件是否被 git clean 或 mv 移走"
        ],
        "success_count": 0,
        "last_applied": None,
        "source": "seed"
    }
]

def load_db():
    """加载恢复策略数据库"""
    if RECOVERY_DB.exists():
        return json.loads(RECOVERY_DB.read_text())
    return {
        'version': '1.0',
        'created': datetime.now().astimezone().isoformat(),
        'strategies': {s['id']: s for s in SEED_STRATEGIES},
        'recovery_log': []
    }

def save_db(db):
    """保存恢复策略数据库"""
    RECOVERY_DB.parent.mkdir(parents=True, exist_ok=True)
    db['updated'] = datetime.now().astimezone().isoformat()
    RECOVERY_DB.write_text(json.dumps(db, ensure_ascii=False, indent=2))

def find_strategy(db, error_msg):
    """根据错误信息匹配恢复策略"""
    error_lower = error_msg.lower()
    matches = []
    for sid, strategy in db['strategies'].items():
        pattern = strategy['error_pattern'].lower()
        if re.search(pattern, error_lower):
            matches.append(strategy)
    return matches

def record_recovery(db, strategy_id, success, notes=''):
    """记录一次恢复尝试"""
    if strategy_id in db['strategies']:
        s = db['strategies'][strategy_id]
        if success:
            s['success_count'] += 1
        s['last_applied'] = datetime.now().astimezone().isoformat()
    
    db['recovery_log'].append({
        'timestamp': datetime.now().astimezone().isoformat(),
        'strategy_id': strategy_id,
        'success': success,
        'notes': notes
    })
    # Keep last 100 entries
    db['recovery_log'] = db['recovery_log'][-100:]
    save_db(db)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  recovery.py match <error_message>     # Find matching strategy")
        print("  recovery.py list                       # List all strategies")
        print("  recovery.py record <id> <success|fail> # Record recovery attempt")
        print("  recovery.py stats                      # Show recovery stats")
        return
    
    db = load_db()
    cmd = sys.argv[1]
    
    if cmd == 'match':
        error_msg = ' '.join(sys.argv[2:])
        matches = find_strategy(db, error_msg)
        if matches:
            print(f"Found {len(matches)} matching strategy(ies):")
            for m in matches:
                print(f"\n🔧 [{m['id']}] ({m['category']})")
                print(f"   Success count: {m['success_count']}")
                print(f"   Steps:")
                for i, step in enumerate(m['recovery_steps'], 1):
                    print(f"     {i}. {step}")
        else:
            print("No matching strategy found. Consider adding one.")
    
    elif cmd == 'list':
        print(f"📋 Recovery Strategies ({len(db['strategies'])})")
        for sid, s in db['strategies'].items():
            icon = '✅' if s['success_count'] > 0 else '⚪'
            print(f"  {icon} {sid}: {s['category']} (used {s['success_count']}x)")
    
    elif cmd == 'record':
        sid = sys.argv[2]
        success = sys.argv[3].lower() in ('success', 'true', 'yes', '1')
        notes = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else ''
        record_recovery(db, sid, success, notes)
        print(f"{'✅' if success else '❌'} Recorded recovery for {sid}")
    
    elif cmd == 'stats':
        total = len(db['recovery_log'])
        successes = sum(1 for r in db['recovery_log'] if r['success'])
        print(f"📊 Recovery Stats")
        print(f"   Total attempts: {total}")
        print(f"   Successes: {successes}")
        print(f"   Success rate: {round(successes/total*100, 1) if total else 0}%")
        print(f"\n   By strategy:")
        for sid, s in db['strategies'].items():
            if s['success_count'] > 0:
                print(f"     {sid}: {s['success_count']} successes")
    
    else:
        print(f"Unknown command: {cmd}")
    
    save_db(db)

if __name__ == '__main__':
    main()
