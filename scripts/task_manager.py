#!/usr/bin/env python3
"""
task_manager.py — 统一任务管理器（合并 sync + archive + cycle + learning）

取代：
- dashboard/sync_completed_tasks.py
- dashboard/archive_completed.py  
- scripts/task_cycle.py

功能（按执行顺序）：
1. 扫描 memory log，同步已完成任务标记到 project-plans
2. 检查全项目完成状态，归档到 P.md
3. 【新增】从完成任务中提取经验，沉淀到 .learnings/ 和 skills/
4. 基于经验+外部资源，生成更高级的新任务
5. 更新派生文件（active.md 状态摘要）

数据流：memory log → project-plans → P.md → .learnings/ → skills/
单一写入口，无冲突。

用法：python3 scripts/task_manager.py [--dry-run]
"""

import re
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path("/home/gem/workspace/agent/workspace")
DOCS_DIR = WORKSPACE / "docs"
MEMORY_DIR = WORKSPACE / "memory"
LEARNINGS_DIR = WORKSPACE / ".learnings"
SKILLS_DIR = WORKSPACE / "skills"
P_MD = WORKSPACE / "P.md"
EXPERIENCE_MD = LEARNINGS_DIR / "EXPERIENCE.md"
LEARNINGS_MD = LEARNINGS_DIR / "LEARNINGS.md"

# 任务类型分类规则
TASK_CATEGORIES = {
    '技术': ['搜索.*论文', 'arXiv', 'capsule', '代码', '脚本', '技术', 'PR', '开源', 'GitHub', '测试'],
    '运营': ['EvoMap', '发布', '推送', '社区', '互动', '回复'],
    '创作': ['博客', '推文', '帖子', '内容', '文章', '品牌'],
    '策略': ['研究', '探索', '方向', '规划', '架构', '设计'],
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_today_plan():
    today = datetime.now().strftime("%Y-%m-%d")
    plan = DOCS_DIR / f"project-plans-{today}.md"
    if plan.exists():
        return plan
    plans = sorted(DOCS_DIR.glob("project-plans-*.md"), reverse=True)
    return plans[0] if plans else None

# ═══════════════════════════════════════════
# Step 1: 同步已完成任务
# ═══════════════════════════════════════════

def find_completed_task_ids(plan_content):
    """从 memory log 扫描已完成的任务，只提取与当前 plan 中存在的 ID 匹配的任务"""
    # 先提取当前 plan 中存在的所有任务 ID
    plan_ids = set(re.findall(r'(?<!\w)([A-Z]+-\d+)(?!\w)', plan_content))
    
    completed = set()
    today = datetime.now()
    for i in range(2):  # 今日 + 昨日
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        mem_file = MEMORY_DIR / f"{d}.md"
        if not mem_file.exists():
            continue
        content = mem_file.read_text()
        patterns = [
            r'✅\s*(?:\*\*)?(S-\d+|T-\d+)(?:\*\*)?\s*[:：]',
            r'((?:S|T)-\d+)\s*[:：].*(?:✅|完成|成功|全部完成)',
            r'(?:完成|✅)\s*(?:\*\*)?((?:S|T)-\d+)',
            r'((?:S|T)-\d+)\s*[:：].*(?:已发布|已推送|已创建|已撰写|已联系|已验证|已搜索|已设计|已研究|已测试|已更新|已完成)',
        ]
        for p in patterns:
            for m in re.finditer(p, content):
                tid = m.group(1)
                # 只保留当前 plan 中存在的 ID，避免跨日期污染
                if tid in plan_ids:
                    completed.add(tid)
    return completed

def sync_tasks(plan_path, dry_run=False):
    """将 memory 中的完成状态同步到 project-plans，支持两种格式"""
    content = plan_path.read_text()
    completed_ids = find_completed_task_ids(content)
    new_content = content
    marked = 0
    
    # 方式1: 有 S-XX ID 匹配
    for tid in completed_ids:
        # 匹配 S-XX: or T-XX: 格式
        pattern = rf'^(- \[) (\] {re.escape(tid)}:)'
        replacement = rf'\1x\2'
        new, count = re.subn(pattern, replacement, new_content, flags=re.MULTILINE)
        if count > 0:
            new_content = new
            marked += count
    
    # 方式2: 无 ID 格式时，检查 memory 中是否有"完成"关键词匹配 plan 任务描述
    # 只在方式1无结果时启用，且仅扫描今日 memory，要求更长的匹配串
    if marked == 0:
        today_str = datetime.now().strftime("%Y-%m-%d")
        mem_file = MEMORY_DIR / f"{today_str}.md"
        if mem_file.exists():
            mem_content = mem_file.read_text().lower()
            # 找 plan 中未完成的无前缀任务（排除 S-XX 和 T-XX 格式）
            for m in re.finditer(r'^- \[ \]\s+(?!(?:S|T)-\d+:)(.{8,}?)$', content, re.MULTILINE):
                desc = m.group(1).strip()
                # 取任务描述的前 15 个字符做模糊匹配，降低误标率
                key = desc[:15].lower()
                if len(key) >= 8 and key in mem_content and ('完成' in mem_content or '✅' in mem_content):
                    # 标记这个任务为完成
                    old_line = m.group(0)
                    new_line = old_line.replace('- [ ]', '- [x]', 1)
                    new_content = new_content.replace(old_line, new_line, 1)
                    marked += 1
    
    if marked > 0 and not dry_run:
        plan_path.write_text(new_content)
    
    ids_str = ', '.join(sorted(completed_ids)) if completed_ids else f'{marked} 个(描述匹配)'
    log(f"📋 Step1: {marked} 个任务标记完成 ({ids_str})")
    return marked

# ═══════════════════════════════════════════
# Step 2: 归档已完成项目
# ═══════════════════════════════════════════

def archive_projects(plan_path, dry_run=False):
    """检查项目完成状态，归档到 P.md"""
    content = plan_path.read_text()
    
    # 解析项目块
    projects = []
    current = None
    for line in content.split('\n'):
        proj_match = re.match(r'^##\s+项目[一二三四五六七八九十\d]+[：:]\s*(.+)$', line)
        if proj_match:
            if current:
                projects.append(current)
            current = {'title': proj_match.group(1).strip(), 'tasks': [], 'start_line': line}
        elif current:
            task_match = re.match(r'^-\s+\[([ x])\]\s+(.+)$', line)
            if task_match:
                current['tasks'].append({'done': task_match.group(1) == 'x', 'text': task_match.group(2)})
    if current:
        projects.append(current)
    
    fully_done = [p for p in projects if p['tasks'] and all(t['done'] for t in p['tasks'])]
    
    if not fully_done:
        log(f"📦 Step2: 无完全完成的项目")
        return 0
    
    # 写入 P.md
    today = datetime.now().strftime("%Y-%m-%d")
    sections = []
    for p in fully_done:
        tasks_text = "\n".join(f"- ✅ {t['text'][:80]}" for t in p['tasks'])
        sections.append(f"""## ✅ {p['title']} — {today}

**完成度**: {len(p['tasks'])}/{len(p['tasks'])} 任务

**关键成果**:
{tasks_text}

---
""")
    
    existing = P_MD.read_text() if P_MD.exists() else "# P.md — 已完成项目档案（倒序）\n\n> 最新完成的项目在最上方。\n\n---\n"
    parts = existing.split("---", 2)
    new_content = parts[0] + "---" + "\n" + "\n".join(sections) + "---" + (parts[2] if len(parts) >= 3 else "\n")
    
    if not dry_run:
        P_MD.write_text(new_content)
    
    log(f"📦 Step2: {len(fully_done)} 个项目归档到 P.md")
    return len(fully_done)

# ═══════════════════════════════════════════
# Step 3: 经验提取与沉淀（复利核心）
# ═══════════════════════════════════════════

def classify_task(desc):
    """将任务描述归类到类型"""
    for cat, keywords in TASK_CATEGORIES.items():
        for kw in keywords:
            if re.search(kw, desc, re.IGNORECASE):
                return cat
    return '其他'

def extract_completed_tasks(plan_path):
    """从当前 project-plans 中提取本轮完成的任务"""
    tasks = []
    content = plan_path.read_text()
    for m in re.finditer(r'^- \[x\]\s+((?:S|T)-\d+):\s*(.+)$', content, re.MULTILINE):
        desc = m.group(2).strip()
        tasks.append({
            'id': m.group(1),
            'desc': desc,
            'category': classify_task(desc),
        })
    return tasks

def load_existing_experience():
    """加载现有经验库，用于去重"""
    entries = []
    if EXPERIENCE_MD.exists():
        content = EXPERIENCE_MD.read_text()
        # 提取所有经验条目标题
        for m in re.finditer(r'^#{2,4}\s+(.+)$', content, re.MULTILINE):
            entries.append(m.group(1).strip())
    return entries

def generate_learnings(completed_tasks, cycle):
    """从完成任务中生成经验条目"""
    learnings = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 按类别分组
    by_cat = {}
    for t in completed_tasks:
        cat = t['category']
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(t)
    
    for cat, tasks in by_cat.items():
        # 为每个类别生成一条经验总结
        task_list = "\n".join(f"  - {t['id']}: {t['desc']}" for t in tasks)
        
        # 根据类别选择经验类型
        if cat == '技术':
            insight = f"技术类任务共 {len(tasks)} 个，涉及代码/工具/研究。常见模式：先搜索现有方案 → 评估可行性 → 实现最小可用版本 → 验证效果。"
            action = "下次技术任务：优先搜索 `.learnings/EXPERIENCE.md` 有无同类经验，复用已验证方案。"
        elif cat == '运营':
            insight = f"运营类任务共 {len(tasks)} 个，涉及发布/社区/互动。常见模式：按节奏执行 → 检查效果 → 调整策略。"
            action = "下次运营任务：建立检查清单（发布前搜 memory、发布后检查响应），减少遗漏。"
        elif cat == '创作':
            insight = f"创作类任务共 {len(tasks)} 个，涉及内容/博客/品牌。常见模式：选题 → 收集素材 → 撰写 → 发布。"
            action = "下次创作任务：从已完成的 capsule/blog 中提取写作模板，减少重复构思。"
        elif cat == '策略':
            insight = f"策略类任务共 {len(tasks)} 个，涉及规划/架构/方向。常见模式：调研现状 → 分析差距 → 制定方案 → 执行验证。"
            action = "下次策略任务：先回顾已有经验库，避免重复探索。"
        else:
            insight = f"其他类任务共 {len(tasks)} 个。"
            action = "考虑为这类任务建立标准化流程。"
        
        learnings.append({
            'cycle': cycle,
            'date': today,
            'category': cat,
            'count': len(tasks),
            'tasks': task_list,
            'insight': insight,
            'action': action,
        })
    
    return learnings

def write_experience(learnings, dry_run=False):
    """将经验写入 .learnings/EXPERIENCE.md"""
    if not learnings:
        return 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    existing = load_existing_experience()
    
    new_entries = []
    for l in learnings:
        # 去重：检查是否已有同类经验
        title = f"第{l['cycle']}轮 — {l['category']}类任务经验"
        if any(title in e for e in existing):
            log(f"  ⏭️ 跳过重复经验: {title}")
            continue
        
        entry = f"""
### 🔧 {title}
**日期**: {l['date']} | **涉及任务**: {l['count']}个

**任务清单**:
{l['tasks']}

**洞察**: {l['insight']}

**行动项**: {l['action']}
"""
        new_entries.append(entry)
    
    if not new_entries:
        log(f"🧠 Step3: 无新经验需要沉淀")
        return 0
    
    section = f"\n## 📅 {today} 沉淀（第{learnings[0]['cycle']}轮）\n" + "\n".join(new_entries) + "\n"
    
    if not dry_run:
        if EXPERIENCE_MD.exists():
            EXPERIENCE_MD.write_text(EXPERIENCE_MD.read_text() + section)
        else:
            EXPERIENCE_MD.write_text("# 🧠 实战经验沉淀库\n\n> 完成任务过程中积累的技巧和认知。目标：遇到新任务时能从这里快速找到解决方案。\n\n---\n" + section)
    
    log(f"🧠 Step3: {len(new_entries)} 条新经验已沉淀到 .learnings/EXPERIENCE.md")
    return len(new_entries)

def write_learnings_entry(learnings, dry_run=False):
    """将关键经验写入 .learnings/LEARNINGS.md（self-improvement 格式）"""
    if not learnings:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    cycle = learnings[0]['cycle']
    total_tasks = sum(l['count'] for l in learnings)
    categories = list(set(l['category'] for l in learnings))
    
    # 生成一个 LRN 条目总结本轮
    timestamp = datetime.now().isoformat()
    entry = f"""
## [LRN-{today.replace('-','')}-AUTO] 第{cycle}轮任务经验沉淀

**Logged**: {timestamp}
**Priority**: medium
**Status**: promoted
**Area**: config

### Summary
第{cycle}轮任务完成，{total_tasks}个任务涉及{', '.join(categories)}类，沉淀{len(learnings)}条经验。

### Details
{chr(10).join(f"- [{l['category']}] {l['insight']}" for l in learnings)}

### Suggested Action
{chr(10).join(f"- {l['action']}" for l in learnings)}

### Metadata
- Source: auto_extraction
- Tags: experience, cycle-{cycle}, {', '.join(categories)}
- Pattern-Key: task.experience_extraction

---
"""
    if not dry_run:
        if LEARNINGS_MD.exists():
            LEARNINGS_MD.write_text(LEARNINGS_MD.read_text() + entry)
    
    log(f"🧠 Step3: LRN 条目已写入 LEARNINGS.md")

def check_skill_extraction(completed_tasks, cycle):
    """检查是否有足够的重复模式可以提取为 skill"""
    # 统计任务类型出现频率
    cat_counts = {}
    for t in completed_tasks:
        cat = t['category']
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    
    # 检查是否同一类型任务连续 3 轮出现
    if EXPERIENCE_MD.exists():
        content = EXPERIENCE_MD.read_text()
        for cat, count in cat_counts.items():
            if count >= 3:
                # 检查是否有同类型经验在之前轮次出现过
                prev_matches = len(re.findall(f'{cat}类任务经验', content))
                if prev_matches >= 2:
                    log(f"  💡 候选 skill 提取: {cat}类任务（出现 {prev_matches + 1} 轮）")
                    return cat
    return None

# ═══════════════════════════════════════════
# Step 4: 短期任务进化循环
# ═══════════════════════════════════════════

def parse_all_short_tasks(plan_path):
    """解析所有短期任务，兼容两种格式：
    1. 带前缀: - [x] S-01: 描述
    2. 无前缀: - [ ] 描述（自动分配临时 ID）
    """
    content = plan_path.read_text()
    tasks = []
    seen = set()
    
    # 格式1: S-XX: or T-XX: 前缀
    for m in re.finditer(r'^- \[([ x])\]\s+((?:S|T)-\d+):\s*(.+)$', content, re.MULTILINE):
        tid = m.group(2)
        if tid not in seen:
            seen.add(tid)
            tasks.append({'id': tid, 'done': m.group(1) == 'x', 'desc': m.group(3).strip()})
    
    # 格式2: 无前缀（仅匹配在"今日原子任务"区块下的条目）
    # 先找所有无前缀的 - [ ] / - [x] 行，排除已有 S- 前缀的
    auto_id = 1
    in_task_section = False
    for line in content.split('\n'):
        # 检测"今日任务"或"今日原子任务"区块
        if re.match(r'###?\s+.*(?:今日|原子).*任务', line):
            in_task_section = True
            continue
        if in_task_section and re.match(r'###?\s+', line):
            in_task_section = False
            continue
        
        if in_task_section:
            m = re.match(r'^- \[([ x])\]\s+(?!(?:S|T)-\d+:)(.+)$', line)
            if m:
                tid = f"AUTO-{auto_id:02d}"
                auto_id += 1
                if tid not in seen:
                    seen.add(tid)
                    tasks.append({'id': tid, 'done': m.group(1) == 'x', 'desc': m.group(2).strip()})
    
    return tasks

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
                    'slots': t.get('slots_remaining', 0)
                })
        except:
            pass
    return tasks

def get_cycle_number():
    if not P_MD.exists():
        return 1
    return len(re.findall(r'第\d+轮进化', P_MD.read_text())) + 1

def get_experience_tasks(cycle):
    """基于经验库生成更高级的任务（复利模式）"""
    tasks = []
    
    if not EXPERIENCE_MD.exists():
        return tasks
    
    content = EXPERIENCE_MD.read_text()
    
    # 从经验中提取行动项，转换为任务
    for m in re.finditer(r'\*\*行动项\*\*:\s*(.+)', content):
        action = m.group(1).strip()
        # 跳过太泛化的建议
        if len(action) > 15 and '下次' not in action:
            tasks.append(f"执行经验行动项: {action[:60]}")
    
    # 从经验中找重复出现的模式，生成自动化任务
    cat_pattern = r'### 🔧 (.+?)类任务经验'
    cats = re.findall(cat_pattern, content)
    cat_freq = {}
    for c in cats:
        cat_freq[c] = cat_freq.get(c, 0) + 1
    
    for cat, freq in cat_freq.items():
        if freq >= 2:
            tasks.append(f"为{cat}类任务创建自动化模板/脚本（已出现{freq}轮）")
    
    return tasks[:3]  # 最多 3 个经验驱动的任务

def evolution_cycle(plan_path, dry_run=False):
    """短期任务接近完成时生成新任务"""
    tasks = parse_all_short_tasks(plan_path)
    if not tasks:
        log("🔄 Step4: 无短期任务")
        return False
    
    total = len(tasks)
    done = sum(1 for t in tasks if t['done'])
    remaining = total - done
    
    if remaining > 1:
        log(f"🔄 Step4: 还剩 {remaining} 个任务，未触发循环")
        return False
    
    log(f"🔄 Step4: {done}/{total} 完成，触发进化循环！")
    
    # 归档本轮到 P.md
    cycle = get_cycle_number()
    today = datetime.now().strftime("%Y-%m-%d")
    results = "\n".join(f"- ✅ {t['id']}: {t['desc'][:80]}" for t in tasks if t['done'])
    remaining_text = ""
    not_done = [t for t in tasks if not t['done']]
    if not_done:
        remaining_text = "\n**未完成**:\n" + "\n".join(f"- ❌ {t['id']}: {t['desc'][:80]}" for t in not_done)
    
    section = f"""
## ✅ 第{cycle}轮进化任务完成 🔄 — {today}

**完成度**: {done}/{total} 任务

**关键成果**:
{results}
{remaining_text}

---
"""
    if not dry_run:
        existing = P_MD.read_text()
        parts = existing.split("---", 2)
        P_MD.write_text(parts[0] + "---" + "\n" + section + "---" + (parts[2] if len(parts) >= 3 else "\n"))
    
    # 生成新任务（连续编号，避免和旧任务冲突）
    evomap = get_evomap_tasks()
    evo_sorted = sorted(evomap, key=lambda t: (t['bounty'], t['slots']), reverse=True)
    
    # 找到当前最大的 S-* 编号
    all_existing = re.findall(r'(?:S|T)-(\d+)', plan_path.read_text())
    max_num = max((int(n) for n in all_existing), default=0)
    
    new_tasks = []
    
    # 1. EvoMap 任务（高 bounty 优先）
    if evo_sorted:
        max_num += 1
        new_tasks.append(f"- [ ] S-{max_num:02d}: 完成 EvoMap 任务: {evo_sorted[0]['title'][:35]}（关联 M-01-1）")
    if len(evo_sorted) > 1:
        max_num += 1
        new_tasks.append(f"- [ ] S-{max_num:02d}: 完成 EvoMap 任务: {evo_sorted[1]['title'][:35]}（关联 M-01-1）")
    
    # 2. 经验驱动的任务（复利模式：基于历史经验生成更高级任务）
    exp_tasks = get_experience_tasks(cycle)
    for et in exp_tasks:
        if len(new_tasks) >= 12:
            break
        max_num += 1
        new_tasks.append(f"- [ ] S-{max_num:02d}: {et}（关联 E-经验库）")
    
    # 3. 基础模板任务（兜底，保证 12 个）
    templates = [
        "搜索并贡献 PR 到高星开源项目|M-01-3",
        "撰写/发布 1 篇技术博客文章|M-01-4",
        "更新 GitHub 项目 README 或文档|M-01-4",
        "参与 2 个开源 issue 讨论|M-01-5",
        "研究 1 个可产品化的技能方向|M-02-4",
        "发布 1 条有商业价值的技术内容|M-02-5",
        "创作 1 条高质量技术推文/帖子|M-03-1",
        "设计或优化个人品牌元素|M-03-6",
        "搜索 arXiv 最新论文准备 capsule 素材|M-01-4",
        "检查并回复社交平台互动|M-03-2",
    ]
    
    for tmpl in templates:
        if len(new_tasks) >= 12:
            break
        max_num += 1
        desc, ref = tmpl.split("|")
        new_tasks.append(f"- [ ] S-{max_num:02d}: {desc}（关联 {ref}）")
    
    if not dry_run:
        new_section = f"\n## 🔄 第{cycle}轮新任务（自动进化生成）\n\n" + "\n".join(new_tasks) + "\n"
        plan_path.write_text(plan_path.read_text() + new_section)
    
    log(f"🔄 Step4: 第{cycle}轮完成，{len(new_tasks)} 个新任务已生成")
    return True

# ═══════════════════════════════════════════
# Main
# ═══════════════════════════════════════════

def main():
    dry_run = '--dry-run' in sys.argv
    
    log("═══ 统一任务管理器（含经验沉淀） ═══")
    if dry_run:
        log("🔍 DRY RUN 模式 — 不写入任何文件")
    
    plan_path = get_today_plan()
    if not plan_path:
        log("❌ 找不到 project-plans 文件")
        return
    
    log(f"📄 数据源: {plan_path.name}")
    
    # Step 1: 同步完成标记
    sync_tasks(plan_path, dry_run)
    
    # Step 2: 归档完成项目
    archive_projects(plan_path, dry_run)
    
    # Step 3: 经验提取与沉淀（复利核心）
    completed = extract_completed_tasks(plan_path)
    if completed:
        cycle = get_cycle_number()
        learnings = generate_learnings(completed, cycle)
        write_experience(learnings, dry_run)
        write_learnings_entry(learnings, dry_run)
        candidate = check_skill_extraction(completed, cycle)
        if candidate:
            log(f"  💡 提示: {candidate}类任务适合提取为 skill，建议使用 skill creator 处理")
    else:
        log("🧠 Step3: 无已完成任务，跳过经验提取")
    
    # Step 4: 进化循环（基于经验生成更高级任务）
    evolution_cycle(plan_path, dry_run)
    
    # Step 5: 报告状态
    tasks = parse_all_short_tasks(plan_path)
    done = sum(1 for t in tasks if t['done'])
    log(f"═══ 状态: {done}/{len(tasks)} 短期任务完成 ═══")

if __name__ == '__main__':
    main()
