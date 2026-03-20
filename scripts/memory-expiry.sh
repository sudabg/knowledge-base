#!/usr/bin/env bash
# memory-expiry.sh — 记忆过期维护脚本
# 由 heartbeat 或 cron 触发，扫描过期记忆并自动降级

set -euo pipefail
MEMORY_DIR="/home/gem/workspace/agent/workspace/memory"
ARCHIVE="$MEMORY_DIR/archive.md"
TODAY=$(TZ=Asia/Shanghai date +%Y-%m-%d)
NOW_EPOCH=$(TZ=Asia/Shanghai date +%s)
LOG_PREFIX="[memory-expiry]"

echo "$LOG_PREFIX Running expiry check at $TODAY"

# === 1. Daily log 精简（>3天的文件提取精华后清空）===
find "$MEMORY_DIR" -name '20[0-9][0-9]-*.md' -not -name "$TODAY.md" -not -name "$TODAY-*.md" | while read -r f; do
    filename=$(basename "$f" .md)
    file_date="$filename"
    
    # 计算文件天数差
    file_epoch=$(TZ=Asia/Shanghai date -d "$file_date" +%s 2>/dev/null || echo 0)
    if [ "$file_epoch" -eq 0 ]; then continue; fi
    
    days_old=$(( (NOW_EPOCH - file_epoch) / 86400 ))
    
    if [ "$days_old" -gt 3 ]; then
        lines=$(wc -l < "$f")
        if [ "$lines" -gt 5 ]; then
            echo "$LOG_PREFIX Archiving $filename ($days_old days old, $lines lines)"
            echo "" >> "$ARCHIVE"
            echo "## 📦 $filename (archived $TODAY)" >> "$ARCHIVE"
            # 提取有 ## 标题的段落（精华）
            grep -E '^(## |### |✅|❌|💡|⚠️|重要|关键|教训|决定)' "$f" >> "$ARCHIVE" 2>/dev/null || echo "_(no highlights)_" >> "$ARCHIVE"
            # 清空原文件，保留标题
            head -5 "$f" > "$f.tmp"
            echo "" >> "$f.tmp"
            echo "> ✅ 内容已归档到 archive.md ($TODAY)" >> "$f.tmp"
            mv "$f.tmp" "$f"
        fi
    fi
done

# === 2. Ontology 实体降级（30天无更新的实体移到 archive）===
ONTOLOGY_GRAPH="$MEMORY_DIR/ontology/graph.jsonl"
if [ -f "$ONTOLOGY_GRAPH" ] && [ -s "$ONTOLOGY_GRAPH" ]; then
    # 计算30天前的时间戳
    thirty_days_ago=$(TZ=Asia/Shanghai date -d "30 days ago" --iso-8601=seconds 2>/dev/null || echo "old")
    echo "$LOG_PREFIX Checking ontology entities for 30-day stale threshold"
    # 标记统计（实际降级由 agent 执行，这里只报告）
    stale_count=$(grep -c '"op":"create"' "$ONTOLOGY_GRAPH" 2>/dev/null || echo 0)
    echo "$LOG_PREFIX Ontology has $stale_count total create operations"
fi

# === 3. Ephemeral 清理（.learnings/ 下超过 1 天的临时文件）===
find /home/gem/workspace/agent/workspace/.learnings/ -name '*.tmp' -mtime +1 -delete 2>/dev/null && \
    echo "$LOG_PREFIX Cleaned ephemeral temp files" || true

echo "$LOG_PREFIX Expiry check complete"
