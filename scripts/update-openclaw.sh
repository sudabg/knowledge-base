#!/usr/bin/env bash
# scripts/update-openclaw.sh — 自动更新 OpenClaw
# 双路径策略：user location（无需sudo） + 系统位置（需要sudo）
set -euo pipefail

REGISTRY="https://registry.npmmirror.com"
USER_PREFIX="/home/gem/.local"
SYSTEM_PREFIX="/usr"

echo "🔄 OpenClaw Update Script"
echo "========================"

# Check current version
CURRENT=$($USER_PREFIX/bin/openclaw --version 2>/dev/null || openclaw --version 2>/dev/null || echo "unknown")
echo "Current: $CURRENT"

# Get latest version from npm
LATEST=$(npm view openclaw version --registry "$REGISTRY" 2>/dev/null || echo "unknown")
echo "Latest:  $LATEST"

if [ "$CURRENT" = "OpenClaw $LATEST" ] || echo "$CURRENT" | grep -q "$LATEST"; then
    echo "✅ Already up to date!"
    exit 0
fi

echo ""
echo "📦 Updating..."

# Strategy 1: Install to user location (no sudo needed)
echo "→ Installing to user location ($USER_PREFIX)..."
npm install -g openclaw@latest --registry "$REGISTRY" --prefix "$USER_PREFIX" 2>&1 | tail -3

# Verify user install
NEW_VER=$($USER_PREFIX/bin/openclaw --version 2>/dev/null)
echo "✅ User install: $NEW_VER"

# Strategy 2: Try system install if sudo available
if command -v sudo &>/dev/null && sudo -n true 2>/dev/null; then
    echo "→ Sudo available, also updating system location..."
    sudo npm install -g openclaw@latest --registry "$REGISTRY" 2>&1 | tail -3
    echo "✅ System install complete"
else
    echo "⚠️  No sudo — user install only"
    echo "   Gateway restart will use: $USER_PREFIX/bin/openclaw"
fi

# Restart gateway
echo ""
echo "🔄 Restarting gateway..."
if [ -x "$USER_PREFIX/bin/openclaw" ]; then
    export PATH="$USER_PREFIX/bin:$PATH"
fi

# Try gateway restart
openclaw gateway restart 2>&1 || echo "⚠️  Gateway restart may need manual intervention"

echo ""
echo "✅ Update complete: $NEW_VER"
