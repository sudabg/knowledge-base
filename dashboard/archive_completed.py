#!/usr/bin/env python3
"""
项目完成检查 + 归档脚本
- 扫描 project-plans 文件中所有项目
- 检测全部完成的项目（所有 [x] 无剩余 [ ]）
- 将完成的项目追加到 P.md（倒序）
- 从 project-plans 中移除已完成项目
- 输出变更报告
"""
import re, datetime, sys
from pathlib import Path

WORKSPACE = Path('/home/gem/workspace/agent/workspace')
PLANS_DIR = WORKSPACE / 'docs'
P_MD = WORKSPACE / 'P.md'

def get_latest_plan():
    """找到最新的 project-plans 文件"""
    plans = sorted(PLANS_DIR.glob('project-plans-*.md'), reverse=True)
    return plans[0] if plans else None

def parse_projects(text):
    """解析项目列表，返回 (before, projects, after)"""
    lines = text.split('\n')
    projects = []
    current = None
    section_start = None
    
    for i, line in enumerate(lines):
        proj_match = re.match(r'^##\s+项目[一二三四五六七八九十\d]+[：:]\s*(.+)$', line)
        if proj_match:
            if current:
                current['end'] = i
                projects.append(current)
            current = {
                'title': proj_match.group(1).strip(),
                'start': i,
                'end': None,
                'tasks': [],
                'header_line': line
            }
            section_start = i
        elif current:
            task_match = re.match(r'^-\s+\[([ x])\]\s+(.+)$', line)
            if task_match:
                current['tasks'].append({
                    'done': task_match.group(1) == 'x',
                    'text': task_match.group(2),
                    'line': line
                })
    
    if current:
        current['end'] = len(lines)
        projects.append(current)
    
    # Find content boundaries
    before = []
    after = []
    if projects:
        before = lines[:projects[0]['start']]
        after = lines[projects[-1]['end']:]
    
    return before, projects, after, lines

def is_project_complete(project):
    """检查项目是否全部完成"""
    if not project['tasks']:
        return False
    return all(t['done'] for t in project['tasks'])

def extract_project_summary(plan_text, project):
    """从原文提取项目摘要"""
    lines = plan_text.split('\n')
    start = project['start']
    end = project['end']
    section_lines = lines[start:end]
    
    # Extract key info
    goal = ''
    status = ''
    for l in section_lines:
        goal_match = re.match(r'^\*\*目标\*\*[：:]\s*(.+)$', l.strip())
        if goal_match:
            goal = goal_match.group(1)
        status_match = re.match(r'^\*\*现状\*\*[：:]\s*(.+)$', l.strip())
        if status_match:
            status = status_match.group(1)
    
    done_tasks = [t for t in project['tasks'] if t['done']]
    
    return {
        'title': project['title'],
        'goal': goal,
        'status': status,
        'done_count': len(done_tasks),
        'total_count': len(project['tasks']),
        'tasks': done_tasks
    }

def archive_to_pmd(summary):
    """将完成项目写入 P.md（插入到格式说明之后，保持倒序）"""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    entry = f"\n## ✅ {summary['title']} — {today}\n\n"
    entry += f"**目标**: {summary['goal']}\n\n"
    entry += f"**最终状态**: {summary['status']}\n\n" if summary['status'] else ""
    entry += f"**完成度**: {summary['done_count']}/{summary['total_count']} 任务\n\n"
    entry += "**关键成果**:\n"
    for t in summary['tasks'][-5:]:  # Last 5 achievements
        entry += f"- ✅ {t['text']}\n"
    entry += "\n---\n"
    
    # Read current P.md
    content = P_MD.read_text()
    
    # Find insertion point (after format说明 section end)
    marker = '---\n'
    # Find the second --- (end of format说明)
    parts = content.split(marker, 2)
    if len(parts) >= 3:
        # Insert after format说明
        new_content = parts[0] + marker + parts[1] + marker + entry + '\n' + parts[2]
    else:
        new_content = content + '\n' + entry
    
    P_MD.write_text(new_content)
    return entry

def remove_from_plan(plan_path, projects_to_remove):
    """从项目计划中批量移除已完成项目（逆序删除避免行号偏移）"""
    lines = plan_path.read_text().split('\n')
    # Sort by start index descending so we remove from bottom up
    for p in sorted(projects_to_remove, key=lambda x: x['start'], reverse=True):
        lines = lines[:p['start']] + lines[p['end']:]
    plan_path.write_text('\n'.join(lines))

def main():
    plan_path = get_latest_plan()
    if not plan_path:
        print("No project plan file found")
        return
    
    print(f"Scanning: {plan_path.name}")
    text = plan_path.read_text()
    before, projects, after, all_lines = parse_projects(text)
    
    completed = []
    active = []
    
    for p in projects:
        if is_project_complete(p):
            completed.append(p)
        else:
            active.append(p)
    
    if not completed:
        print("No completed projects found")
        print(f"Active projects: {len(active)}")
        for p in active:
            done = sum(1 for t in p['tasks'] if t['done'])
            total = len(p['tasks'])
            print(f"  {p['title']}: {done}/{total} ({round(done/total*100) if total else 0}%)")
        return
    
    print(f"\n🎉 Found {len(completed)} completed project(s)!")
    
    for p in completed:
        summary = extract_project_summary(text, p)
        print(f"\n  Archiving: {p['title']} ({summary['done_count']}/{summary['total_count']})")
        archive_to_pmd(summary)
        print(f"  ✅ Written to P.md")
    
    # Remove all completed projects at once (avoid line number shift)
    remove_from_plan(plan_path, completed)
    print(f"\n  🗑️  Removed {len(completed)} project(s) from plan file")
    
    print(f"\n✅ Archive complete. {len(active)} active projects remaining.")

if __name__ == '__main__':
    main()
