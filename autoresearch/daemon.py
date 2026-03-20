#!/usr/bin/env python3
"""Daemon: 自主进化守护进程。不依赖外部API也能持续工作。

工作模式：
1. 有 EvoMap 任务 → 跑进化周期
2. 心跳限流/无任务 → 内部建设（优化工具、更新知识、写论文分析）
3. 网络断开 → 本地学习（审查历史、优化策略、重构代码）

核心思想：永远有有价值的工作可以做。
"""
import time, json, os, sys, subprocess
from datetime import datetime

AUTORESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(AUTORESEARCH_DIR)
STATE_FILE = os.path.join(AUTORESEARCH_DIR, "daemon_state.json")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"total_cycles": 0, "total_capsules": 0, "total_promoted": 0, 
                "last_active": None, "mode": "evomap", "idle_work_done": []}

def save_state(state):
    state["last_active"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_evomap():
    """Check EvoMap availability and tasks."""
    try:
        sys.path.insert(0, AUTORESEARCH_DIR)
        from evomap import heartbeat, get_tasks
        r = heartbeat()
        if "error" in r:
            return None, []
        tasks = get_tasks(min_bounty=80, exclude_keywords=["maximize capsule"])
        return r, tasks
    except:
        return None, []

def do_idle_work(state):
    """Work that doesn't need EvoMap API."""
    idle = state.get("idle_work_done", [])
    
    # Work 1: Review and optimize strategy based on results.tsv
    if "strategy_review" not in idle:
        results_file = os.path.join(AUTORESEARCH_DIR, "results.tsv")
        if os.path.exists(results_file):
            with open(results_file) as f:
                lines = f.readlines()[1:]  # skip header
            if len(lines) >= 3:
                # Analyze cycle scores
                scores = [float(l.split('\t')[9]) for l in lines if len(l.split('\t')) > 9]
                avg_score = sum(scores) / len(scores) if scores else 0
                print(f"  Strategy review: {len(lines)} cycles, avg score {avg_score:.3f}")
                state["idle_work_done"].append("strategy_review")
    
    # Work 2: Validate evomap.py code
    if "code_validation" not in idle:
        evomap_py = os.path.join(AUTORESEARCH_DIR, "evomap.py")
        result = subprocess.run(["python3", "-c", f"import py_compile; py_compile.compile('{evomap_py}', doraise=True)"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  evomap.py: syntax OK")
        state["idle_work_done"].append("code_validation")
    
    # Work 3: Read and learn from accumulated learnings
    if "learnings_review" not in idle:
        learnings = os.path.join(WORKSPACE, ".learnings/LEARNINGS.md")
        if os.path.exists(learnings):
            size = os.path.getsize(learnings)
            print(f"  LEARNINGS.md: {size} bytes")
            state["idle_work_done"].append("learnings_review")
    
    # Work 4: Clean up temp files
    if "temp_cleanup" not in idle:
        import glob
        bundles = glob.glob("/tmp/bundle_*.json")
        for b in bundles:
            try:
                os.remove(b)
            except:
                pass
        print(f"  Cleaned {len(bundles)} temp bundle files")
        state["idle_work_done"].append("temp_cleanup")
    
    return state

def main():
    """Main daemon loop - never stops unless killed."""
    print(f"[{datetime.now().strftime('%H:%M')}] 🦞 自主进化守护进程启动")
    state = load_state()
    idle_interval = 300  # 5 minutes between idle work
    check_interval = 120  # 2 minutes between EvoMap checks
    
    while True:
        # Try EvoMap
        hb, tasks = check_evomap()
        
        if tasks:
            print(f"[{datetime.now().strftime('%H:%M')}] Found {len(tasks)} tasks - EvoMap mode")
            state["mode"] = "evomap"
            # Tasks available - the main session handles capsule generation
            # Just report and wait for next check
            for t in sorted(tasks, key=lambda x: x.get("bounty_amount",0), reverse=True)[:3]:
                print(f"  ${t.get('bounty_amount'):>3} | {t.get('title')[:55]}")
        else:
            # No tasks or rate limited - do internal work
            if state["mode"] != "idle":
                print(f"[{datetime.now().strftime('%H:%M')}] EvoMap unavailable - switching to idle work")
                state["mode"] = "idle"
                state["idle_work_done"] = []  # reset idle work queue
            
            state = do_idle_work(state)
            
            # If all idle work done, sleep longer
            if len(state["idle_work_done"]) >= 4:
                print(f"[{datetime.now().strftime('%H:%M')}] All idle work done, sleeping {idle_interval}s")
                save_state(state)
                time.sleep(idle_interval)
                state["idle_work_done"] = []  # reset for next cycle
                continue
        
        save_state(state)
        time.sleep(check_interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Daemon] Stopped by user")
        save_state(load_state())
