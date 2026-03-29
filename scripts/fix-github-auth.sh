#!/bin/bash
# fix-github-auth.sh — 修复 GitHub 认证持久化问题
# 用法: bash scripts/fix-github-auth.sh [TOKEN]
# 如果不提供 TOKEN，会提示输入

set -e

HOME_DIR="/home/gem"
GH_CONFIG_DIR="$HOME_DIR/.config/gh"
GH_HOSTS_FILE="$GH_CONFIG_DIR/hosts.yml"
WORKSPACE="/home/gem/workspace/agent/workspace"
TOOLS_FILE="$WORKSPACE/TOOLS.md"

echo "🔧 GitHub Auth Fix — 修复 Token 失忆问题"
echo ""

# Step 1: Set HOME if not set
if [ -z "$HOME" ]; then
    export HOME="$HOME_DIR"
    echo "✅ HOME=$HOME"
fi

# Step 2: Create gh config directory
mkdir -p "$GH_CONFIG_DIR"

# Step 3: Get token
TOKEN="${1:-}"
if [ -z "$TOKEN" ]; then
    # Try to read from existing config
    if [ -f "$GH_HOSTS_FILE" ]; then
        EXISTING_TOKEN=$(grep "oauth_token:" "$GH_HOSTS_FILE" | awk '{print $2}' | head -1)
        if [ -n "$EXISTING_TOKEN" ]; then
            TOKEN="$EXISTING_TOKEN"
            echo "✅ Token found in existing config"
        fi
    fi
fi

if [ -z "$TOKEN" ]; then
    echo "❌ No token found. Usage: bash scripts/fix-github-auth.sh ghp_xxxx"
    echo ""
    echo "To get a token:"
    echo "  1. Go to https://github.com/settings/tokens"
    echo "  2. Generate new classic token (repo, read:org, gist scopes)"
    echo "  3. Run: bash scripts/fix-github-auth.sh YOUR_TOKEN"
    exit 1
fi

# Step 4: Write gh config
cat > "$GH_HOSTS_FILE" << EOF
github.com:
    user: sudabg
    oauth_token: $TOKEN
    git_protocol: https
EOF
chmod 600 "$GH_HOSTS_FILE"
echo "✅ Token written to $GH_HOSTS_FILE"

# Step 5: Verify
export HOME="$HOME_DIR"
gh auth status 2>&1
echo ""

# Step 6: Store token hash for verification (not the token itself)
TOKEN_HASH=$(echo -n "$TOKEN" | sha256sum | awk '{print $1}')
echo "Token hash: ${TOKEN_HASH:0:16}..."

echo ""
echo "✅ GitHub auth fix complete. Token stored persistently."
