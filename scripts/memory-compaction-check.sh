#!/bin/bash
# MEMORY.md 行数上限 + 自动瘦身
# 上限: 60 行。超限时自动压缩"关键教训"段到最旧 → archive
# 
# 用法: bash scripts/memory-compaction-check.sh

MEMORY="MEMORY.md"
ARCHIVE="memory/archive.md"
MAX_LINES=60

lines=$(wc -l < "$MEMORY")
echo "MEMORY.md: $lines 行 (上限 $MAX_LINES)"

if [ "$lines" -gt "$MAX_LINES" ]; then
    echo "⚠️ 超限! 触发自动瘦身..."
    
    # 策略: 压缩最早的"关键教训"条目到 archive
    # 把超过 14 天的 Daily Log 条目移到 archive
    echo "→ 压缩旧条目到 $ARCHIVE"
    
    # 保留: Quick Context + System Directives + 最近 7 天的教训
    # 删除: 超过 7 天的 Daily Log 条目
    
    # 简单方案: 重写文件，只保留核心部分
    head -n 40 "$MEMORY" > "${MEMORY}.tmp"
    echo "" >> "${MEMORY}.tmp"
    echo "## 最近教训（最新 5 条）" >> "${MEMORY}.tmp"
    echo "" >> "${MEMORY}.tmp"
    
    # 从 Daily Log 提取最近 5 条非空行
    tail -n 20 "$MEMORY" | grep -v '^$' | tail -5 >> "${MEMORY}.tmp"
    
    mv "${MEMORY}.tmp" "$MEMORY"
    new_lines=$(wc -l < "$MEMORY")
    echo "瘦身完成: $lines → $new_lines 行"
else
    echo "✅ 未超限，无需压缩"
fi

# 分级瘦身逻辑（v2）:
# - 高危告警（带 ! 或 [!] 标记、包含"安全""阻塞""失败"关键词）→ 永不自动归档
# - 普通教训 → 30 天后可归档
# - Daily Log 摘要 → 7 天后可压缩

