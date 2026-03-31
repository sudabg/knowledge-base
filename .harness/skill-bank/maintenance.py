#!/usr/bin/env python3
"""
Harness Skill Bank — 动态双粒度技能库 (Mode 14)
借鉴 D2Skill: task skills + step skills, utility-aware retrieval, pruning

数据来源: .harness/skill-bank/skills.jsonl
每个技能有 utility_score，随使用更新，低效技能自动修剪。

用法:
  python3 maintenance.py store    — 从当前项目经验自动提取并存储新技能
  python3 maintenance.py query    — 查询匹配当前任务的技能
  python3 maintenance.py list     — 列出所有技能及其效用
  python3 maintenance.py prune    — 修剪低效技能
  python3 maintenance.py stats    — 技能库统计
  python3 maintenance.py reflect  — 从 lessons.json 反射式扩展技能库
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

BANK_DIR = Path(__file__).parent
SKILLS_FILE = BANK_DIR / "skills.jsonl"
CONFIG_FILE = BANK_DIR / "bank_config.json"
LESSONS_FILE = BANK_DIR.parent / "lessons.json"
HARNESS_STUDY = BANK_DIR.parent / "harness-study.json"
VALIDATION_LOG = BANK_DIR.parent / "validation.log"

# === Default config ===
DEFAULT_CONFIG = {
    "max_skills": 100,
    "min_utility_threshold": 0.3,  # Below this, skills get pruned
    "utility_decay_rate": 0.95,    # Each period without use
    "prune_frequency_days": 7,
    "granularity_levels": {
        "task": {
            "description": "高层模式 — 知道做什么（战略层）",
            "example": "复杂任务拆分成子任务，每个子任务有验收标准"
        },
        "step": {
            "description": "细粒度模式 — 知道怎么做（战术层）",
            "example": "验证 API 响应时，先检查 status code，再检查 body 字段"
        }
    }
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

def load_skills():
    skills = []
    if SKILLS_FILE.exists():
        for line in SKILLS_FILE.read_text().strip().split('\n'):
            if line.strip():
                try:
                    skills.append(json.loads(line))
                except:
                    pass
    return skills

def save_skills(skills):
    with open(SKILLS_FILE, 'w') as f:
        for s in skills:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')

def compute_skill_id(skills_entry):
    raw = json.dumps({k:v for k,v in skills_entry.items() if k != 'skill_id'}, 
                     sort_keys=True, ensure_ascii=False)
    return "sk_" + hashlib.sha256(raw.encode()).hexdigest()[:12]

# === Core operations ===

def store_skill(granularity, signals, action, outcome, source_ref="", utility_init=0.7):
    """存储一条新技能"""
    skill = {
        "skill_id": "",
        "granularity": granularity,  # "task" or "step"
        "signals": signals if isinstance(signals, list) else [signals],
        "action": action,
        "outcome": outcome,
        "utility_score": utility_init,
        "use_count": 0,
        "success_count": 0,
        "source_ref": source_ref,
        "created": datetime.now(timezone.utc).isoformat(),
        "last_used": None,
        "tags": []
    }
    skill["skill_id"] = compute_skill_id(skill)
    
    skills = load_skills()
    # Deduplicate by signals
    existing_signals = set()
    for s in skills:
        for sig in s.get("signals", []):
            existing_signals.add(sig.lower())
    
    overlap = set(sig.lower() for sig in skill["signals"]) & existing_signals
    if len(overlap) == len(skill["signals"]):
        print(f"⚠️ 技能已存在（信号完全重叠），跳过")
        return None
    
    skills.append(skill)
    save_skills(skills)
    print(f"✅ 存储技能: {skill['skill_id']} [{granularity}] {', '.join(signals[:3])}")
    return skill

def query_skills(task_description, top_k=3):
    """查询匹配当前任务的技能"""
    skills = load_skills()
    if not skills:
        print("📭 技能库为空")
        return []
    
    task_lower = task_description.lower()
    scored = []
    for s in skills:
        signal_match = sum(1 for sig in s.get("signals", []) if sig.lower() in task_lower)
        action_match = any(w in s.get("action", "").lower() for w in task_lower.split())
        relevance = (signal_match * 0.6 + (0.4 if action_match else 0)) * s.get("utility_score", 0.5)
        if relevance > 0:
            scored.append((relevance, s))
    
    scored.sort(reverse=True)
    results = scored[:top_k]
    
    if not results:
        print(f"🔍 无直接匹配: '{task_description}'")
        # Return top utility skills as fallback
        skills_by_utility = sorted(skills, key=lambda x: x.get("utility_score", 0), reverse=True)
        print(f"📊 基于效用的 Top-{top_k}:")
        for s in skills_by_utility[:top_k]:
            print(f"  [{s['granularity']}] utility={s['utility_score']:.2f} | {s['action'][:60]}")
        return skills_by_utility[:top_k]
    
    print(f"🔍 匹配 {len(results)} 个技能:")
    for rel, s in results:
        print(f"  [{s['granularity']}] relevance={rel:.2f} utility={s['utility_score']:.2f}")
        print(f"    信号: {', '.join(s['signals'][:4])}")
        print(f"    操作: {s['action'][:80]}")
    
    return [s for _, s in results]

def update_utility(skill_id, success=True, delta=0.1):
    """使用后更新技能效用"""
    skills = load_skills()
    for s in skills:
        if s["skill_id"] == skill_id:
            s["use_count"] = s.get("use_count", 0) + 1
            if success:
                s["success_count"] = s.get("success_count", 0) + 1
                s["utility_score"] = min(1.0, s.get("utility_score", 0.5) + delta)
            else:
                s["utility_score"] = max(0.0, s.get("utility_score", 0.5) - delta * 1.5)
            s["last_used"] = datetime.now(timezone.utc).isoformat()
            save_skills(skills)
            print(f"📊 更新 {skill_id}: utility={s['utility_score']:.2f} (use={s['use_count']}, ok={s['success_count']})")
            return s
    print(f"❌ 未找到技能: {skill_id}")

def prune_skills():
    """修剪低效技能（utility < threshold 且 use_count > 0）"""
    config = load_config()
    threshold = config.get("min_utility_threshold", 0.3)
    skills = load_skills()
    
    before = len(skills)
    kept = []
    pruned = []
    
    for s in skills:
        utility = s.get("utility_score", 0.5)
        use_count = s.get("use_count", 0)
        
        if utility < threshold and use_count > 0:
            pruned.append(s)
            print(f"✂️ 修剪: {s['skill_id']} [{s['granularity']}] utility={utility:.2f} use={use_count}")
        else:
            # Apply decay if unused
            if s.get("last_used"):
                days_since = (datetime.now(timezone.utc) - 
                             datetime.fromisoformat(s["last_used"])).days
                if days_since > 7:
                    decay = config.get("utility_decay_rate", 0.95)
                    s["utility_score"] *= decay ** (days_since // 7)
            kept.append(s)
    
    save_skills(kept)
    print(f"📋 修剪完成: {before} → {len(kept)} (移除 {len(pruned)} 个低效技能)")
    return pruned

def reflect_from_lessons():
    """从 lessons.json 反射式提取技能"""
    if not LESSONS_FILE.exists():
        print("📭 无 lessons.json")
        return
    
    with open(LESSONS_FILE) as f:
        lessons = json.load(f)
    
    stored = 0
    for decision in lessons.get("decisions", []):
        signals = [decision.get("context", "")[:30]]
        if decision.get("reason"):
            signals.append(decision["reason"][:30])
        
        skill = store_skill(
            granularity="task",
            signals=signals,
            action=decision.get("decision", "")[:120],
            outcome=decision.get("outcome", "")[:120],
            source_ref=f"lessons:{decision.get('id', 'unknown')}",
            utility_init=0.75
        )
        if skill:
            stored += 1
    
    print(f"🔄 反射完成: 从 {len(lessons.get('decisions',[]))} 个决策中提取了 {stored} 个新技能")

def show_stats():
    """显示技能库统计"""
    skills = load_skills()
    config = load_config()
    
    if not skills:
        print("📭 技能库为空")
        return
    
    by_gran = {}
    for s in skills:
        g = s.get("granularity", "unknown")
        by_gran.setdefault(g, []).append(s)
    
    print(f"📊 Harness Skill Bank 统计")
    print(f"{'='*50}")
    print(f"总计: {len(skills)} 个技能 (上限: {config.get('max_skills', 100)})")
    print()
    
    for gran, group in by_gran.items():
        avg_utility = sum(s.get("utility_score", 0) for s in group) / len(group)
        total_uses = sum(s.get("use_count", 0) for s in group)
        total_success = sum(s.get("success_count", 0) for s in group)
        print(f"  [{gran}] {len(group)} 个 | avg_utility={avg_utility:.2f} | uses={total_uses} | success={total_success}")
    
    print()
    top = sorted(skills, key=lambda x: x.get("utility_score", 0), reverse=True)[:5]
    print("🏆 Top 5 高效技能:")
    for s in top:
        print(f"  [{s['granularity']}] {s['utility_score']:.2f} | {s['action'][:60]}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'store':
        if len(sys.argv) < 5:
            print("用法: python3 maintenance.py store <task|step> <signals> <action>")
            sys.exit(1)
        store_skill(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "pending")
    elif cmd == 'query':
        query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not query:
            print("用法: python3 maintenance.py query <task_description>")
            sys.exit(1)
        query_skills(query)
    elif cmd == 'list':
        show_stats()
    elif cmd == 'prune':
        prune_skills()
    elif cmd == 'stats':
        show_stats()
    elif cmd == 'reflect':
        reflect_from_lessons()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
