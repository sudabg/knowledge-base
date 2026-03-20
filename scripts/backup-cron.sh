#!/usr/bin/env bash
cd /home/gem/workspace/agent/workspace
git add -A resources/ memory/ .learnings/ scripts/ docs/ 2>/dev/null
git diff --cached --quiet && exit 0
git commit -m "🔄 Auto-backup $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M')" --quiet
git push origin main --quiet 2>/dev/null
