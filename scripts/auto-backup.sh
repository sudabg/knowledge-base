#!/usr/bin/env bash
# Auto-backup workspace to GitHub
cd /home/gem/workspace/agent/workspace
git add -A
git diff --cached --quiet && echo "No changes" && exit 0
git commit -m "🔄 Auto-backup $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M')" 
git push origin main 2>&1
