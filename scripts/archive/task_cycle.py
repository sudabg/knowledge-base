#!/usr/bin/env python3
"""
task_cycle.py — 短期任务自动进化循环 (v2)

数据源：docs/project-plans-YYYY-MM-DD.md（不是 active.md）
逻辑：
1. 扫描今日 project-plans 中所有 S-* 短期任务
2. 如果只剩 ≤1 个未完成（或全部完成），触发进化循环：
   a. 将本轮成果写入 P.md
   b. 挖掘新资源（EvoMap任务/arXiv/learnings/memory）
   c. 基于3个长期目标 + 新资源，生成12个新短期任务
   d. 追加到 project-plans 文件
3. 否则：输出剩余任务，不做变更

用法：
  python3 task_cycle.py [--force] [--dry-run]
"""

import re
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path("/home/gem/workspace/agent/workspace")
DOCS_DIR = WORKSPACE / "docs"
P_MD = WORKSPACE / "P.md"
MEMORY_DIR = WORKSPACE / "memory"
LEARNINGS_DIR = WORKSPACE / ".learnings"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_today_plan():
    """找到今日的 project-plans 文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    plan = DOCS_DIR / f"project-plans-{today}.md"
    if plan.exists():
        return plan
    # fallback to latest
    plans = sorted(DOCS_DIR.glob("project-plans-*.md"), reverse=True)
    return plans[0] if plans else None

def get_short_term_tasks(plan_path):
    """从 project-plans 文件中解析 S-* 任务"""
    content = plan_path.read_text()
    tasks = []
    seen_ids = set()
    for line in content.split('\n'):
        m = re.match(r'^- \[([ x])\]\s+(S-\d+):\s*(.+)$', line.strip())
        if m:
            tid = m.group(2)
            if tid not in seen_ids:  # 去重（project-plans 可能有"今日待办"重复列出）
                seen_ids.add(tid)
                tasks.append({
                    'id': tid,
                    'done': m.group(1) == 'x',
                    'desc': m.group(3).strip(),
                    'line': line.strip()
                })
    return tasks

def should_trigger_cycle(tasks):
    """是否应该触发进化循环"""
    if not tasks:
        return False
    total = len(tasks)
    done = sum(1 for t in tasks if t['done'])
    remaining = total - done
    # 剩余 ≤1 个就触发
    return remaining <= 1

def get_recent_memory_lines(days=3):
    summaries = []
    today = datetime.now()
    for i in range(days):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        f = MEMORY_DIR / f"{d}.md"
        if f.exists():
            content = f.read_text()
            for line in content.split('\n'):
                if any(kw in line for kw in ['✅', '完成', '发布', '提交', '创建', '已修复', 'Credit', 'Rep']):
                    summaries.append(f"[{d}] {line.strip()[:120]}")
    return summaries[:30]

def get_learnings():
    learnings = []
    for f_name in ['LEARNINGS.md', 'ERRORS.md']:
        f = LEARNINGS_DIR / f_name
        if f.exists():
            lines = f.read_text().strip().split('\n')
            for line in lines[-30:]:
                if line.strip() and not line.startswith('#'):
                    learnings.append(line.strip()[:120])
    return learnings[:20]

def get_evomap_tasks():
    tasks = []
    hb_file = LEARNINGS_DIR / "last_heartbeat.json"
    if hb_file.exists():
        try:
            data = json.loads(hb_file.read_text())
            for t in data.get('available_tasks', []):
                tasks.append({
                    'title': t.get('title', ''),
                    'bounty': t.get('bounty_amount', 0),
                    'signals': t.get('signals', ''),
                    'slots': t.get('slots_remaining', 0)
                })
        except:
            pass
    return tasks

def get_cycle_number():
    if not P_MD.exists():
        return 1
    content = P_MD.read_text()
    return len(re.findall(r'第\d+轮进化任务完成', content)) + 1

def archive_to_p(tasks, memory_lines):
    today = datetime.now().strftime("%Y-%m-%d")
    cycle = get_cycle_number()
    completed = [t for t in tasks if t['done']]
    
    task_results = []
    for t in completed:
        task_results.append(f"- ✅ {t['id']}: {t['desc'][:80]}")
    
    # 剩余未完成的
    remaining = [t for t in tasks if not t['done']]
    remaining_note = ""
    if remaining:
        remaining_note = "\n**未完成**:\n" + "\n".join(f"- ❌ {t['id']}: {t['desc'][:80]}" for t in remaining)
    
    section = f"""
## ✅ 第{cycle}轮进化任务完成 🔄 — {today}

**目标**: 短期任务驱动3大长期目标

**完成度**: {len(completed)}/{len(tasks)} 任务

**关键成果**:
{chr(10).join(task_results)}
{remaining_note}

---
"""
    existing = P_MD.read_text() if P_MD.exists() else "# P.md — 已完成项目档案（倒序）\n\n> 最新完成的项目在最上方。每日自动检查更新。\n\n---\n"
    parts = existing.split("---", 2)
    if len(parts) >= 3:
        new_content = parts[0] + "---" + "\n" + section + "---" + parts[2]
    else:
        new_content = existing + "\n" + section
    
    P_MD.write_text(new_content)
    log(f"✅ 已写入 P.md: 第{cycle}轮 {len(completed)}/{len(tasks)} 任务归档")

def mine_resources(evomap_tasks):
    resources = []
    for t in evomap_tasks:
        if t['bounty'] > 0 or t['slots'] >= 3:
            resources.append(f"[EvoMap] {t['title']} (bounty={t['bounty']}, slots={t['slots']})")
    resources.extend([
        "[方向] GitHub 开源贡献",
        "[方向] 技术博客输出",
        "[方向] 技能封装变现",
        "[方向] 社交内容创作",
    ])
    return resources[:10]

def generate_new_tasks(evomap_tasks, cycle_num):
    today = datetime.now().strftime("%Y-%m-%d")
    deadline = today + " 23:59"
    
    # 从 EvoMap 取高价值任务
    evo_sorted = sorted(evomap_tasks, key=lambda t: (t['bounty'], t['slots']), reverse=True)
    
    tasks = []
    
    # 2个 EvoMap 任务
    if len(evo_sorted) >= 1:
        tasks.append((f"完成 EvoMap 任务: {evo_sorted[0]['title'][:35]}", "M-01-1"))
    if len(evo_sorted) >= 2:
        tasks.append((f"完成 EvoMap 任务: {evo_sorted[1]['title'][:35]}", "M-01-1"))
    
    # 开源相关
    tasks.append(("搜索并贡献 PR 到高星开源项目", "M-01-3"))
    tasks.append(("撰写/发布 1 篇技术博客文章", "M-01-4"))
    tasks.append(("更新 GitHub 项目 README 或文档", "M-01-4"))
    tasks.append(("参与 2 个开源 issue 讨论", "M-01-5"))
    
    # 盈利相关
    tasks.append(("研究 1 个可产品化的技能方向", "M-02-4"))
    tasks.append(("发布 1 条有商业价值的技术内容", "M-02-5"))
    
    # 社交相关
    tasks.append(("创作 1 条高质量技术推文/帖子", "M-03-1"))
    tasks.append(("设计或优化个人品牌元素", "M-03-6"))
    tasks.append(("搜索 arXiv 最新论文准备 capsule 素材", "M-01-4"))
    tasks.append(("整理近期 learnings 并更新知识库", "M-01-4"))
    
    # 写入 project-plans
    plan_path = get_today_plan()
    if not plan_path:
        log("❌ 找不到今日 project-plans 文件")
        return
    
    content = plan_path.read_text()
    
    # 追加新任务到文件末尾
    new_section = f"\n## 🔄 第{cycle_num}轮新任务（自动进化生成）\n\n"
    for i, (desc, ref) in enumerate(tasks[:12], 1):
        new_section += f"- [ ] S-{i:02d}: {desc}（关联 {ref}）\n"
    
    content += new_section
    
    # 更新文件标题
    content = re.sub(
        r'(昨日（\d{2}-\d{2}）全部 \d+ 个短期任务已完成。今日新增 )\d+( 个短期任务)',
        f'\\g<1>12\\2',
        content
    )
    
    plan_path.write_text(content)
    log(f"✅ 已追加12个新任务到 {plan_path.name}")
    
    for i, (desc, ref) in enumerate(tasks[:12], 1):
        log(f"   S-{i:02d}: {desc}")

def main():
    force = '--force' in sys.argv
    dry_run = '--dry-run' in sys.argv
    
    log("🔄 短期任务进化循环检查 (v2)...")
    
    plan_path = get_today_plan()
    if not plan_path:
        log("❌ 找不到 project-plans 文件")
        return False
    
    log(f"📄 数据源: {plan_path.name}")
    
    tasks = get_short_term_tasks(plan_path)
    total = len(tasks)
    done = sum(1 for t in tasks if t['done'])
    remaining = total - done
    
    log(f"📋 短期任务: {total} 个, 已完成: {done}, 剩余: {remaining}")
    
    if not should_trigger_cycle(tasks) and not force:
        log(f"⏳ 还剩 {remaining} 个任务，未达到触发条件（≤1 剩余）")
        for t in tasks:
            if not t['done']:
                log(f"   ❌ {t['id']}: {t['desc'][:60]}")
        return False
    
    log("🎉 短期任务即将全部完成！启动进化循环...")
    
    if dry_run:
        log("🔍 [DRY RUN] 将执行: 归档→挖掘→生成→追加")
        return True
    
    # 收集资源
    evomap_tasks = get_evomap_tasks()
    log(f"📦 EvoMap 可用任务: {len(evomap_tasks)}")
    
    # 1. 归档到 P.md
    archive_to_p(tasks, [])
    
    # 2. 挖掘资源
    resources = mine_resources(evomap_tasks)
    log(f"🔍 挖掘到 {len(resources)} 个资源方向")
    
    # 3. 生成新任务并追加到 project-plans
    cycle = get_cycle_number() - 1
    generate_new_tasks(evomap_tasks, cycle)
    
    # 4. 记录到 memory
    today = datetime.now().strftime("%Y-%m-%d")
    mem_file = MEMORY_DIR / f"{today}.md"
    entry = f"\n## 🔄 第{cycle}轮进化循环完成 ({datetime.now().strftime('%H:%M')})\n"
    entry += f"- {done}/{total} 个短期任务完成\n"
    entry += f"- 归档到 P.md\n"
    entry += f"- 生成12个新任务到 {plan_path.name}\n"
    
    if mem_file.exists():
        with open(mem_file, 'a') as f:
            f.write(entry)
    
    log("✅ 进化循环完成！")
    return True

if __name__ == '__main__':
    main()
