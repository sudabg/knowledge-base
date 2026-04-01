#!/usr/bin/env python3
"""
Resource → Ticket Auto-Converter
Resource Scout 发现高置信资源后自动运行：
1. 检查是否已有工单同名
2. 自动生成工单条目到 external-evolution-tickets.md
3. 如果 pending 工单 > 5 个 → 标记饱和，停止新发现
4. 工单 30 天未处理 → 自动过期
用法: python3 scripts/resource-to-ticket.py --project <name> --confidence <high|medium> --source <url>
"""

import argparse, sys, os, re
from datetime import datetime, timedelta

BASE = "/home/gem/workspace/agent/workspace"
TICKETS_FILE = os.path.join(BASE, ".learnings", "external-evolution-tickets.md")
TICKETS_HISTORY_FILE = os.path.join(BASE, ".learnings", "ticket_history.json")

def load_tickets():
    if not os.path.isfile(TICKETS_FILE):
        return []
    with open(TICKETS_FILE) as f:
        content = f.read()
    
    tickets = []
    for match in re.finditer(r'### #(\d+): (.+?)\n(.*?)(?=### #|$)', content, re.DOTALL):
        num = int(match.group(1))
        title = match.group(2).strip()
        body = match.group(3).strip()
        status = 'pending'
        if '落地状态: **done**' in body or '落地状态:**done**' in body:
            status = 'done'
        elif '落地状态: **blocked**' in body:
            status = 'blocked'
        elif '落地状态: **in_progress**' in body:
            status = 'in_progress'
        tickets.append({'num': num, 'title': title, 'status': status, 'body': body})
    return tickets


def get_next_num(tickets):
    if not tickets:
        return 1
    return max(t['num'] for t in tickets) + 1


def count_pending(tickets):
    return sum(1 for t in tickets if t['status'] == 'pending')


def add_ticket(project, confidence, source_url, decompose_notes=""):
    tickets = load_tickets()
    next_num = get_next_num(tickets)
    
    # Check duplicate
    for t in tickets:
        if project.lower() in t['title'].lower():
            print(f"⚠️ 工单已存在: #{t['num']} {t['title']}")
            return False
    
    now = datetime.now().strftime('%Y-%m-%d')
    
    ticket = f"""### #{next_num}: {project}
- 发现: {now}
- 置信度: {confidence}
- 来源: {source_url}
- 可行性: 待评估
- 拆解: 待拆解（{decompose_notes}）
- 适配计划: 待制定
- 落地状态: pending
- 验证方式: 待定义
- 归档条件: 待定义
"""
    
    # Append to file
    with open(TICKETS_FILE, 'a', encoding='utf-8') as f:
        f.write(ticket + '\n')
    
    return True


def check_saturation():
    """Check if ticket count exceeds limit"""
    tickets = load_tickets()
    pending = count_pending(tickets)
    
    if pending > 5:
        print(f"🚫 饱和停止: {pending} 个 pending 工单，超过 5 个阈值")
        print("建议: 先消化现有工单，再开启新发现")
        return True
    
    print(f"✅ 未饱和: {pending} 个 pending 工单 (< 5)")
    return False


def check_stale():
    """Mark tickets older than 30 days as expired"""
    tickets = load_tickets()
    now = datetime.now()
    expired = []
    
    for t in tickets:
        if t['status'] == 'pending':
            # Extract date
            date_match = re.search(r'发现: (\d{4}-\d{2}-\d{2})', t['body'])
            if date_match:
                created = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                age = (now - created).days
                if age > 30:
                    expired.append(t)
    
    if expired:
        print(f"⚠️ 过期工单: {len(expired)} 个超过 30 天未处理")
        for t in expired:
            print(f"  #{t['num']}: {t['title']}")
        return expired
    
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--confidence", default="medium", choices=["high", "medium", "low"])
    parser.add_argument("--source", default="", help="来源URL")
    parser.add_argument("--notes", default="", help="拆解笔记")
    args = parser.parse_args()
    
    print(f"=== 资源→工单自动转换 ===")
    print(f"项目: {args.project}")
    
    ok = add_ticket(args.project, args.confidence, args.source, args.notes)
    if ok:
        print(f"✅ 工单已创建")
    
    # Check saturation
    saturated = check_saturation()
    if saturated:
        print("🚫 Resource Scout 饱和，暂停新发现")
        sys.exit(1)
    
    # Check stale
    expired = check_stale()
    
    print(f"\n完成: {'OK' if not saturated else 'SATURATED'}")


if __name__ == "__main__":
    main()
