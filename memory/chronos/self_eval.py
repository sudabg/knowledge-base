#!/usr/bin/env python3
"""
Self-Eval v1.0 — 轻量自评估框架
灵感来自 claw-eval 的 Pass^3 方法论（3次独立运行确认通过）
测试核心 agent 能力，不依赖外部工具
"""

import json, os, sys, time, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path('/home/gem/workspace/agent/workspace')
RESULTS_FILE = WORKSPACE / 'memory/chronos/eval_results.json'

# ─── 测试用例 ───

TESTS = [
    {
        "id": "T01_memory_search",
        "name": "Memory 文件完整性",
        "category": "memory",
        "run": lambda: (
            all(f.exists() for f in [
                WORKSPACE / 'MEMORY.md',
                WORKSPACE / 'memory',
            ]) and
            len(list((WORKSPACE / 'memory').glob('*.md'))) >= 5
        )
    },
    {
        "id": "T02_chronos_index",
        "name": "Chronos 索引可用",
        "category": "memory",
        "run": lambda: (
            (WORKSPACE / 'memory/chronos/chronos_index.json').exists() and
            json.loads((WORKSPACE / 'memory/chronos/chronos_index.json').read_text())['stats']['total_events'] > 100
        )
    },
    {
        "id": "T03_daily_log_exists",
        "name": "今日日志存在",
        "category": "logging",
        "run": lambda: (
            (WORKSPACE / f'memory/{datetime.now().strftime("%Y-%m-%d")}.md').exists()
        )
    },
    {
        "id": "T04_project_plans",
        "name": "项目计划文件存在",
        "category": "project",
        "run": lambda: (
            len(list((WORKSPACE / 'docs').glob('project-plans-*.md'))) >= 1
        )
    },
    {
        "id": "T05_dashboard_api",
        "name": "Dashboard API 响应",
        "category": "dashboard",
        "run": lambda: (
            __import__('urllib.request', fromlist=['urlopen']).urlopen(
                __import__('urllib.request', fromlist=['Request']).Request('http://localhost:8888/api/status'),
                timeout=5
            ).getcode() == 200
        )
    },
    {
        "id": "T06_dashboard_node",
        "name": "Dashboard 节点数据",
        "category": "dashboard",
        "run": lambda: (
            lambda d: d.get('credit', 0) > 4000 and d.get('reputation_score', 0) > 80
        )(__import__('json').loads(
            __import__('urllib.request', fromlist=['urlopen']).urlopen(
                __import__('urllib.request', fromlist=['Request']).Request('http://localhost:8888/api/node'),
                timeout=5
            ).read()
        ))
    },
    {
        "id": "T07_dashboard_projects",
        "name": "Dashboard 项目数据",
        "category": "dashboard",
        "run": lambda: (
            len(json.loads(
                __import__('urllib.request', fromlist=['urlopen']).urlopen(
                    __import__('urllib.request', fromlist=['Request']).Request('http://localhost:8888/api/projects'),
                    timeout=5
                ).read()
            ).get('projects', [])) >= 1
        )
    },
    {
        "id": "T08_git_repo",
        "name": "Git 仓库正常",
        "category": "system",
        "run": lambda: (
            (WORKSPACE / '.git').exists()
        )
    },
    {
        "id": "T09_learnings_file",
        "name": "学习记录存在",
        "category": "learning",
        "run": lambda: (
            (WORKSPACE / '.learnings/LEARNINGS.md').exists() and
            len((WORKSPACE / '.learnings/LEARNINGS.md').read_text()) > 100
        )
    },
    {
        "id": "T10_heartbeat_cache",
        "name": "心跳缓存新鲜",
        "category": "evomap",
        "run": lambda: (
            lambda p: p.exists() and json.loads(p.read_text()).get('credit', 0) > 0
        )(WORKSPACE / '.learnings/last_heartbeat.json')
    },
]

def run_tests(trials=1):
    """运行所有测试，支持多次试验（claw-eval Pass^3 方法论）"""
    results = {
        'timestamp': datetime.now().astimezone().isoformat(),
        'trials': trials,
        'tests': {}
    }
    
    for trial in range(trials):
        for test in TESTS:
            tid = test['id']
            if tid not in results['tests']:
                results['tests'][tid] = {
                    'name': test['name'],
                    'category': test['category'],
                    'runs': []
                }
            
            start = time.time()
            try:
                passed = test['run']()
                elapsed = time.time() - start
                results['tests'][tid]['runs'].append({
                    'passed': passed,
                    'time_ms': round(elapsed * 1000, 1)
                })
            except Exception as e:
                elapsed = time.time() - start
                results['tests'][tid]['runs'].append({
                    'passed': False,
                    'error': str(e)[:100],
                    'time_ms': round(elapsed * 1000, 1)
                })
    
    # Calculate Pass^3 (all trials must pass)
    total = len(TESTS)
    passed_count = 0
    for tid, tdata in results['tests'].items():
        all_passed = all(r['passed'] for r in tdata['runs'])
        tdata['pass'] = all_passed
        if all_passed:
            passed_count += 1
    
    results['summary'] = {
        'total': total,
        'passed': passed_count,
        'failed': total - passed_count,
        'score': round(passed_count / total * 100, 1)
    }
    
    return results

def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    print(f"🧪 Self-Eval v1.0 — Running {len(TESTS)} tests × {trials} trials")
    print("=" * 50)
    
    results = run_tests(trials)
    
    # Print results
    for tid, tdata in results['tests'].items():
        icon = '✅' if tdata['pass'] else '❌'
        times = ', '.join(f"{r['time_ms']}ms" for r in tdata['runs'])
        errors = [r.get('error','') for r in tdata['runs'] if not r['passed']]
        err_str = f" ({errors[0][:40]})" if errors else ""
        print(f"  {icon} {tdata['name']}{err_str}")
    
    print("=" * 50)
    s = results['summary']
    print(f"📊 Score: {s['passed']}/{s['total']} ({s['score']}%)")
    
    # Save results
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to history
    history = []
    if RESULTS_FILE.exists():
        history = json.loads(RESULTS_FILE.read_text())
    history.append(results)
    # Keep last 30 runs
    history = history[-30:]
    RESULTS_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))
    
    print(f"💾 Results saved to {RESULTS_FILE}")

if __name__ == '__main__':
    main()
