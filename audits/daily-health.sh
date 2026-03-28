#!/bin/bash
# Daily Environment Health Audit
# Usage: bash audits/daily-health.sh
# Output: health score (0-100) + issues found

echo "=== Environment Health Audit $(date +%Y-%m-%d) ==="
echo ""

SCORE=100

# 1. Process check
echo "[1/5] Process Check"
PROCS=$(ps aux | grep -E "openclaw|node" | grep -v grep | wc -l)
echo "  OpenClaw processes: $PROCS"

# 2. Disk check
echo "[2/5] Disk Check"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 90 ]; then
  echo "  ⚠️ Disk usage: ${DISK_USAGE}% (critical)"
  SCORE=$((SCORE - 20))
elif [ "$DISK_USAGE" -gt 80 ]; then
  echo "  ⚠️ Disk usage: ${DISK_USAGE}% (warning)"
  SCORE=$((SCORE - 10))
else
  echo "  ✅ Disk usage: ${DISK_USAGE}%"
fi

# 3. Git status check
echo "[3/5] Git Status"
cd /home/gem/workspace/agent/workspace
UNCOMMITTED=$(git status --short 2>/dev/null | wc -l)
if [ "$UNCOMMITTED" -gt 50 ]; then
  echo "  ⚠️ ${UNCOMMITTED} uncommitted files (need backup)"
  SCORE=$((SCORE - 10))
else
  echo "  ✅ ${UNCOMMITTED} uncommitted files"
fi

# 4. Network check
echo "[4/5] Network Check"
if curl -s --max-time 5 https://evomap.ai > /dev/null 2>&1; then
  echo "  ✅ evomap.ai reachable"
else
  echo "  ⚠️ evomap.ai unreachable"
  SCORE=$((SCORE - 10))
fi

if curl -s --max-time 5 https://api.github.com > /dev/null 2>&1; then
  echo "  ✅ api.github.com reachable"
else
  echo "  ⚠️ api.github.com unreachable"
  SCORE=$((SCORE - 10))
fi
# 5. Config check
echo "[5/5] Config Check"
DISABLED_SKILLS=$(grep -c "enabled: false" /home/gem/workspace/agent/openclaw.json 2>/dev/null)
if [ "$DISABLED_SKILLS" -gt 0 ]; then
  echo "  ⚠️ ${DISABLED_SKILLS} disabled skill entries in config (token waste)"
  SCORE=$((SCORE - 15))
else
  echo "  ✅ No disabled skill entries"
fi
echo ""
echo "=== Health Score: $SCORE/100 ==="
if [ "$SCORE" -ge 85 ]; then echo "Status: ✅ Healthy"
elif [ "$SCORE" -ge 70 ]; then echo "Status: ⚠️ Needs attention"
else echo "Status: 🚨 Critical"
fi
