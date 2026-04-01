#!/bin/bash
# verify.sh - 快速验证脚本
# 用法: bash scripts/verify.sh [scope]
# scope: git (default), all, or specific file path

set -e
cd "$(dirname "$0")/.."

SCOPE="${1:-git}"

echo "=== 快速验证 ==="

# 1. 文件完整性检查
echo "[1/4] 文件完整性..."
missing=0
for f in AGENTS.md SOUL.md TOOLS.md MEMORY.md; do
  [ ! -f "$f" ] && echo "  ❌ 缺失: $f" && missing=1
done
[ $missing -eq 0 ] && echo "  ✅ 核心文件完整"

# 2. 上下文大小检查
echo "[2/4] 上下文大小..."
total=$(cat AGENTS.md SOUL.md TOOLS.md HEARTBEAT.md USER.md COMMUNICATION.md IDENTITY.md MEMORY.md 2>/dev/null | wc -c)
echo "  📊 总注入: ${total} bytes"
if [ "$total" -gt 40000 ]; then
  echo "  ⚠️ 超过 40KB 阈值"
elif [ "$total" -gt 30000 ]; then
  echo "  🟡 接近 30KB 目标"
else
  echo "  ✅ 在 30KB 目标内"
fi

# 3. Git 状态检查
echo "[3/4] Git 状态..."
if git rev-parse --git-dir > /dev/null 2>&1; then
  changes=$(git status --porcelain 2>/dev/null | wc -l)
  echo "  📝 未提交变更: $changes 文件"
  if [ "$changes" -gt 0 ] && [ "$SCOPE" = "git" ]; then
    echo "  变更文件:"
    git status --porcelain | head -10
  fi
else
  echo "  ⚠️ 非 git 仓库"
fi

# 4. 预检示例
echo "[4/4] 预检脚本可用性..."
python3 scripts/preflight.py "ls -la" > /dev/null 2>&1 && echo "  ✅ scripts/preflight.py 可用" || echo "  ❌ preflight.py 不可用"

echo ""
echo "=== 验证完成 ==="
echo "如需深度审查，使用 review-swarm skill：读取 skills/review-swarm/SKILL.md"
