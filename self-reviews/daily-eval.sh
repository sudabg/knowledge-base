#!/bin/bash
# Daily Self-Evaluation via Git Diff (Zero-cost self-assessment)
# Usage: bash self-reviews/daily-eval.sh
# Token cost: ~450 tokens/day

cd /home/gem/workspace/agent/workspace

DATE=$(date +%Y-%m-%d)
OUT="self-reviews/${DATE}.md"

# Git changes since last commit
CHANGES=$(git diff HEAD~1 --stat 2>/dev/null || echo "No previous commit")
FILES_CHANGED=$(git diff HEAD~1 --shortstat 2>/dev/null || echo "N/A")
UNCOMMITTED=$(git status --short | wc -l)

# Create self-review
cat > "$OUT" << EOF
## ${DATE} 自评

### 文件变化（git diff --stat）
${FILES_CHANGED}
${UNCOMMITTED} 个未提交文件

### 详细变化
\`\`\`
${CHANGES}
\`\`\`

### 自评（待LLM填写）
- 主要行动：
- 异常标记：
- 明天关注：
EOF

echo "✅ Self-review template written to $OUT"
echo "Files changed: $FILES_CHANGED"
echo "Uncommitted: $UNCOMMITTED"
