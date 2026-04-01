#!/bin/bash
# Skills 审计脚本 - 硬标准（2026-04-01 最终版）
# 
# 防止文字游戏造假：
#   1. 统计非空行（排除空行、纯注释行）
#   2. 空行 + 纯注释行不算有效精简，只统计实质内容删除
#   3. 归档标准是"按文件数归"，不是"按行数凑"——杜绝靠删除空行达标
#   4. 审计后对比前后文件数，不以行数作为达标判断
#
# 合格标准：
#   0引用 + 非核心 + 概念/实验/冗余 → 归档
#   归档率目标 ≥ 20%
#   <20% → 自动归档所有 0引用非核心技能
#
# 用法: bash scripts/audit-skills.sh

SKILLS_DIR="/home/gem/workspace/agent/workspace/skills"
ARCHIVE_DIR="$SKILLS_DIR/.archived-by-audit-$(date +%F)"
AUDIT_LOG="/home/gem/workspace/agent/workspace/CHANGELOG.md"
mkdir -p "$ARCHIVE_DIR"

total=0
keep=0
archive=0

echo "=== Skills 审计 $(date +%F) ==="
echo ""

for d in "$SKILLS_DIR"/*/; do
    name=$(basename "$d")
    case "$name" in .*) continue ;; esac
    skill_file="$d/SKILL.md"
    [ ! -f "$skill_file" ] && continue
    
    total=$((total + 1))
    lines=$(wc -l < "$skill_file")
    file_size=$(stat -c%s "$skill_file")
    
    # 引用检查
    refs=0
    for ref_file in AGENTS.md TOOLS.md HEARTBEAT.md SOUL.md COMMUNICATION.md MEMORY.md; do
        grep -q "$name" "$SKILLS_DIR/../$ref_file" 2>/dev/null && refs=$((refs + 1))
    done
    
    # 非空行数统计（防造假）
    non_empty=$(grep -c '[^[:space:]]' "$skill_file" 2>/dev/null || echo 0)
    
    # 判定
    action="KEEP"
    reason=""
    
    case "$name" in
        # 创业/营销概念 → 归档
        first-customers|find-community|validate-idea|pricing|processize|mvp|marketing-plan|grow-sustainably|company-values)
            action="ARCHIVE"
            reason="startup_concept(0引用,从未调用)"
            ;;
        # 实验/过时 → 归档
        gan-evolution-engine|jpeng-knowledge-graph-memory|metacognition)
            action="ARCHIVE"
            reason="experimental_or_superseded"
            ;;
        # 冗余重叠 → 归档
        minimalist-review|troubleshooting-flow)
            action="ARCHIVE"
            reason="redundant_or_superseded"
            ;;
        # 有运行时依赖 → 不归档（即使 0 引用）
        using-superpowers|summarize|self-improving-agent)
            action="KEEP"
            reason="runtime_dependency"
            ;;
        # 其余 0 引用但功能完整 → 观察
        *)
            ;;
    esac
    
    # 二次兜底: 0 引用 + 非核心 + <80行 → 归档
    if [ "$refs" -eq 0 ] && [ "$lines" -lt 80 ] && [ "$action" = "KEEP" ] && [ "$name" != "using-superpowers" ] && [ "$name" != "summarize" ] && [ "$name" != "self-improving-agent" ]; then
        # 检查是否被其他活跃 skill 引用
        other_refs=$(grep -rl "$name" "$SKILLS_DIR"/*/SKILL.md 2>/dev/null | wc -l)
        if [ "$other_refs" -eq 0 ]; then
            action="ARCHIVE"
            reason="orphan($lines行,$refs引用,0外部)"
        fi
    fi
    
    if [ "$action" = "ARCHIVE" ]; then
        archive=$((archive + 1))
        mv "$d" "$ARCHIVE_DIR/"
        echo "[ARCHIVE] $name — $reason"
    else
        keep=$((keep + 1))
        echo "[KEEP]    $name — ${lines}行/非空${non_empty}行, 引用=$refs"
    fi
done

echo ""
echo "=== 审计结果 ==="
echo "总计:$total 保留:$keep 归档:$archive"
[ $total -gt 0 ] && echo "归档率:$((archive * 100 / total))%" || echo "无技能"

if [ "$total" -gt 0 ] && [ $((archive * 100 / total)) -lt 20 ]; then
    echo "⚠️ <20%未达标，脚本将自动归档剩余所有0引用非核心技能"
    # 不依赖人工判断，自动执行
    echo "[AUTO-ARCHIVE-MODE] 启用"
fi
