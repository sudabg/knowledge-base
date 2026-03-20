#!/usr/bin/env bash
# Daily Summary Pipeline — 自动抓取并摘要最新论文
# Usage: bash scripts/daily-summary.sh [topic] [count]
set -euo pipefail

TOPIC="${1:-LLM+agent}"
COUNT="${2:-3}"
SCRIPTS="/home/gem/workspace/agent/workspace/scripts"
OUTPUT="/home/gem/workspace/agent/workspace/memory/summaries"

mkdir -p "$OUTPUT"
DATE=$(TZ=Asia/Shanghai date +%Y-%m-%d)
OUTFILE="$OUTPUT/$DATE.md"

echo "# 每日论文摘要 — $DATE" > "$OUTFILE"
echo "" >> "$OUTFILE"
echo "**主题**: $TOPIC | **数量**: $COUNT" >> "$OUTFILE"
echo "" >> "$OUTFILE"

# Fetch papers
PAPERS=$(curl -s --max-time 15 "https://export.arxiv.org/api/query?search_query=all:${TOPIC}&sortBy=submittedDate&max_results=${COUNT}" 2>/dev/null)

# Parse and summarize each
echo "$PAPERS" | python3 << 'PYEOF'
import xml.etree.ElementTree as ET, sys, subprocess, os

data = sys.stdin.read()
root = ET.fromstring(data)
ns = {'atom': 'http://www.w3.org/2005/Atom'}
outfile = os.environ.get('OUTFILE', '/tmp/summaries.md')

entries = root.findall('atom:entry', ns)
for i, e in enumerate(entries):
    title = e.find('atom:title', ns).text.strip().replace('\n', ' ')
    abstract = e.find('atom:summary', ns).text.strip()
    link = e.find('atom:id', ns).text
    authors = [a.find('atom:name', ns).text for a in e.findall('atom:author', ns)[:3]]
    
    # Summarize
    r = subprocess.run(['python3', '/home/gem/workspace/agent/workspace/scripts/summarize-engine.py', '-n', '2'],
                      input=abstract, capture_output=True, text=True)
    summary = r.stdout.strip()
    
    with open(outfile, 'a') as f:
        f.write(f"## {i+1}. {title}\n\n")
        f.write(f"**作者**: {', '.join(authors)}  \n")
        f.write(f"**链接**: {link}  \n\n")
        f.write(f"**摘要**: {summary}\n\n")
        f.write("---\n\n")
    
    print(f"✅ [{i+1}/{len(entries)}] {title[:60]}...")
PYEOF

export OUTFILE
echo ""
echo "=== Output saved to $OUTFILE ==="
cat "$OUTFILE"
