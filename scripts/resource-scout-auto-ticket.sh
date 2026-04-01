#!/bin/bash
# Resource Scout 自动工单转换器
# 读取最新的 discovered/*.md 文件，自动生成工单
# 用法: bash scripts/resource-scout-auto-ticket.sh

set -e

BASE="/home/gem/workspace/agent/workspace"
DISCOVERED_DIR="$BASE/awesome-openclaw/discovered"
TICKETS_FILE="$BASE/.learnings/external-evolution-tickets.md"

echo "=== Resource Scout 自动工单转换 ==="

# 1. 检查 Resource Scout 是否正常运行
if [ ! -d "$DISCOVERED_DIR" ]; then
    echo "⚠️ discovered 目录不存在，Resource Scout 未运行"
    exit 1
fi

# 2. 检查资源发现文件
FILES=$(find "$DISCOVERED_DIR" -name "*.md" -type f | sort -r | head -3)
if [ -z "$FILES" ]; then
    echo "ℹ️ 无资源发现文件"
    exit 0
fi

echo "发现文件:"
echo "$FILES"
echo ""

# 3. 用 Python 处理
python3 << 'PYEOF'
import os, re, glob
from datetime import datetime

BASE = "/home/gem/workspace/agent/workspace"
DISCOVERED_DIR = os.path.join(BASE, "awesome-openclaw", "discovered")
TICKETS_FILE = os.path.join(BASE, ".learnings", "external-evolution-tickets.md")

# Load existing tickets
if os.path.isfile(TICKETS_FILE):
    with open(TICKETS_FILE) as f:
        existing = f.read()
else:
    existing = ""

# Parse existing tickets
existing_projects = set()
for m in re.finditer(r'### #\d+: (.+?)\n', existing):
    existing_projects.add(m.group(1).lower())

# Find latest discovered file
files = sorted(glob.glob(os.path.join(DISCOVERED_DIR, "*.md")), reverse=True)
if not files:
    print("No discovery files found")
    exit(0)

latest = files[0]
with open(latest) as f:
    content = f.read()

# Extract GitHub projects with stars
projects = []
for m in re.finditer(r'### (\d+)\. (.+?) ⭐(.+?)\n(.*?)(?=###|\Z)', content, re.DOTALL):
    num = int(m.group(1))
    repo = m.group(2).strip()
    stars = m.group(3).strip()
    details = m.group(4).strip()
    
    # Extract link
    link_match = re.search(r'\*\*链接\*\*: (.+)', details)
    link = link_match.group(1).strip() if link_match else ""
    
    # Extract why it matters
    why_match = re.search(r'\*\*为什么有用\*\*: (.+)', details)
    why = why_match.group(1).strip() if why_match else ""
    
    # Extract confidence
    conf_match = re.search(r'\*\*置信度\*\*: (.+)', details)
    conf = conf_match.group(1).strip() if conf_match else "medium"
    
    if repo.lower() not in existing_projects:
        # Only auto-create ticket for high confidence
        if conf == "high":
            projects.append({"repo": repo, "stars": stars, "link": link, "why": why, "conf": conf})
            print(f"  📋 新工单: {repo} ⭐{stars} (high confidence)")
        else:
            print(f"  ⏭️ 跳过 (置信度=conf): {repo}")
    else:
        print(f"  ✅ 已有工单: {repo}")

if not projects:
    print("\n无新项目需要创建工单")
    exit(0)

# Get next ticket number
ticket_nums = re.findall(r'### #(\d+):', existing)
next_num = max([int(n) for n in ticket_nums], default=0) + 1

# Create tickets
now = datetime.now().strftime('%Y-%m-%d')
new_tickets = []
for p in projects:
    next_num += 1
    ticket = f"""### #{next_num}: {p['repo']}
- 发现: {now}
- 置信度: {p['conf']}
- 星标: {p['stars']}
- 链接: {p['link']}
- 拆解: {p['why']}
- 可行性: 待评估
- 适配计划: 待制定
- 落地状态: pending
- 验证方式: 待定义
- 归档条件: 待定义
"""
    new_tickets.append(ticket)

# Append to tickets file
with open(TICKETS_FILE, 'a', encoding='utf-8') as f:
    f.write('\n' + '\n'.join(new_tickets))

print(f"\n✅ 创建了 {len(new_tickets)} 个新工单")

# Check saturation
pending_count = existing.count("- 落地状态: pending") + len(new_tickets)
if pending_count > 5:
    print(f"\n🚫 饱和停止: {pending_count} 个 pending 工单 > 5 阈值")
    print("建议: 先消化现有工单，再开启新发现")
else:
    print(f"\n✅ 未饱和: {pending_count} 个 pending 工单 (< 5)")
PYEOF