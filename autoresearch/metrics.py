#!/usr/bin/env python3
"""Track and compute evolution metrics."""
import json, os, time
from datetime import datetime

LEARNINGS_DIR = os.path.expanduser("~/workspace/agent/workspace/.learnings")
AUTORESEARCH_DIR = os.path.expanduser("~/workspace/agent/workspace/autoresearch")
HEARTBEAT_FILE = os.path.join(LEARNINGS_DIR, "last_heartbeat.json")
RESULTS_FILE = os.path.join(AUTORESEARCH_DIR, "results.tsv")

def get_current_state():
    """Read current node state from heartbeat cache."""
    try:
        with open(HEARTBEAT_FILE) as f:
            return json.load(f)
    except:
        return {"credit": 0, "total_published": 0, "total_promoted": 0}

def record_cycle(cycle_num, strategy_version, pub_count, promoted_count, credit_start, credit_end, notes=""):
    """Append a cycle result to results.tsv."""
    rate = promoted_count / pub_count if pub_count > 0 else 0
    credit_delta = credit_end - credit_start
    # Normalized score (0-1)
    rate_score = rate  # 0-1
    credit_score = min(credit_delta / 100, 1.0)  # normalize: 100 credit = 1.0
    quality_bonus = 0.5 if rate >= 0.8 else 0.3 if rate >= 0.5 else 0
    cycle_score = 0.5 * rate_score + 0.3 * credit_score + 0.2 * quality_bonus
    
    row = f"{cycle_num}\t{datetime.now().strftime('%H:%M')}\t{strategy_version}\t{pub_count}\t{promoted_count}\t{rate:.2f}\t{credit_start:.0f}\t{credit_end:.0f}\t{credit_delta:.0f}\t{cycle_score:.3f}\t{notes}\n"
    
    with open(RESULTS_FILE, 'a') as f:
        f.write(row)
    
    return cycle_score

def get_last_score():
    """Get the last cycle's score."""
    try:
        with open(RESULTS_FILE) as f:
            lines = f.readlines()
            if len(lines) <= 1:
                return 0.0
            last = lines[-1].strip().split('\t')
            return float(last[9])  # cycle_score column
    except:
        return 0.0

def print_summary():
    """Print evolution summary."""
    state = get_current_state()
    print(f"=== 小哩子 进化状态 ===")
    print(f"信用: {state.get('credit', '?')}")
    print(f"已发布: {state.get('total_published', '?')}")
    print(f"已推广: {state.get('total_promoted', '?')}")
    
    try:
        with open(RESULTS_FILE) as f:
            lines = f.readlines()[1:]  # skip header
            print(f"进化周期: {len(lines)}")
            if lines:
                scores = [float(l.split('\t')[9]) for l in lines]
                print(f"最近得分: {scores[-1]:.3f}")
                print(f"最高得分: {max(scores):.3f}")
                print(f"平均得分: {sum(scores)/len(scores):.3f}")
    except:
        print("尚无进化记录")

if __name__ == "__main__":
    print_summary()
