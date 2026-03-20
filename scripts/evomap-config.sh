#!/bin/bash
# EvoMap 统一配置管理
# 目的：集中管理所有路径、凭证和运行时配置，避免碎片化

set -e

CONFIG_DIR="/home/gem/.evomap"
WORKSPACE="/home/gem/workspace/agent"
ENV_FILE="${WORKSPACE}/.env"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

color() {
    echo -e "${1}${2}${NC}"
}

# 初始化配置目录
init_config_dir() {
    color $YELLOW "📁 初始化配置目录..."
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"
    color $GREEN "✅ 配置目录就绪: $CONFIG_DIR"
}

# 持久化节点凭证
persist_credentials() {
    local node_id="${EVOMAP_NODE_ID:-node_db2f95ffdba95eb6}"
    local node_secret="${EVOMAP_NODE_SECRET:-d846e0f269030e8b3eb3ed60472b164b448f8360e578a6392ccc4740d096ba14}"

    color $YELLOW "🔐 持久化节点凭证..."
    echo "$node_secret" > "$CONFIG_DIR/node_secret"
    echo "$node_id" > "$CONFIG_DIR/node_id"
    chmod 600 "$CONFIG_DIR/node_secret" "$CONFIG_DIR/node_id"
    color $GREEN "✅ 凭证已保存到: $CONFIG_DIR/"
}

# 修正 dotenv 路径
fix_dotenv_path() {
    color $YELLOW "🔧 修正 dotenv 路径..."
    if [ -f "$ENV_FILE" ]; then
        # Evolver 期望在 /tmp/.env
        if [ ! -f "/tmp/.env" ]; then
            cp "$ENV_FILE" "/tmp/.env"
            chmod 600 "/tmp/.env"
            color $GREEN "✅ 已复制 .env 到 /tmp/.env"
        else
            color $GREEN "⏭️  /tmp/.env 已存在，跳过"
        fi
    else
        color $RED "❌ 未找到 .env 文件: $ENV_FILE"
        return 1
    fi
}

# 初始化 git 仓库（如果缺失）
ensure_git_repo() {
    color $YELLOW "🔧 检查 git 仓库..."
    if [ ! -d "$WORKSPACE/.git" ]; then
        cd "$WORKSPACE"
        git init
        git add -A
        git commit -m "evomap: init repository for evolvers"
        color $GREEN "✅ git 仓库已初始化"
    else
        color $GREEN "⏭️  git 仓库已存在"
    fi
}

# 设置工作区环境变量
set_workspace_env() {
    color $YELLOW "🔧 配置工作区环境变量..."
    if ! grep -q "OPENCLAW_WORKSPACE" ~/.profile 2>/dev/null; then
        echo "export OPENCLAW_WORKSPACE=$WORKSPACE" >> ~/.profile
        color $GREEN "✅ 已添加 OPENCLAW_WORKSPACE 到 ~/.profile"
    fi
    export OPENCLAW_WORKSPACE="$WORKSPACE"
    color $GREEN "🔧 当前会话已设置 OPENCLAW_WORKSPACE=$WORKSPACE"
}

# 验证配置
validate_config() {
    color $YELLOW "🔍 验证配置..."
    local errors=0

    if [ ! -f "$CONFIG_DIR/node_secret" ]; then
        color $RED "   ❌ 缺失: $CONFIG_DIR/node_secret"
        errors=$((errors+1))
    fi

    if [ ! -f "$CONFIG_DIR/node_id" ]; then
        color $RED "   ❌ 缺失: $CONFIG_DIR/node_id"
        errors=$((errors+1))
    fi

    if [ ! -f "/tmp/.env" ]; then
        color $YELLOW "   ⚠️  缺失: /tmp/.env (Evolver 可能无法加载配置)"
        errors=$((errors+1))
    fi

    if [ ! -d "$WORKSPACE/.git" ]; then
        color $YELLOW "   ⚠️  缺失: $WORKSPACE/.git (Evolver 回滚功能受限)"
        errors=$((errors+1))
    fi

    if [ -z "$OPENCLAW_WORKSPACE" ]; then
        color $YELLOW "   ⚠️  OPENCLAW_WORKSPACE 未设置"
        errors=$((errors+1))
    fi

    if [ $errors -eq 0 ]; then
        color $GREEN "✅ 所有配置验证通过！"
    else
        color $YELLOW "⚠️  发现 $errors 个问题，请检查上述警告"
    fi
}

# 主流程
main() {
    color $GREEN "\n🦞 EvoMap 配置管理器 v1.0\n"
    init_config_dir
    persist_credentials
    fix_dotenv_path
    ensure_git_repo
    set_workspace_env
    validate_config
    color $GREEN "\n✨ 配置完成！启动进化循环：\n"
    color $NC "   1. 运行: openclaw gateway restart"
    color $NC "   2. 检查 cron 任务状态: cron list"
    color $NC "   3. 手动触发: cron run <job-id>\n"
}

main "$@"
