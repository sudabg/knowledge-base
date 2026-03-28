#!/bin/bash
# Cloudflare Named Tunnel 自动化部署脚本
# 用途：将本地服务（如 dashboard）通过固定域名暴露到公网
# 前提：需要 Cloudflare API Token（需有 Account:Cloudflare Tunnel:Edit 权限）
# 用法：bash scripts/cloudflare-named-tunnel.sh [options]
#
# 环境变量（必填）：
#   CF_API_TOKEN    - Cloudflare API Token（非 Global API Key）
#   CF_ACCOUNT_ID   - Cloudflare Account ID
#   CF_ZONE_ID      - DNS Zone ID
#   CF_TUNNEL_NAME  - 隧道名称（默认 openbot-tunnel）
#   CF_HOSTNAME     - 自定义域名（默认 openbot.indevs.in）
#   LOCAL_PORT      - 本地服务端口（默认 8888）

set -euo pipefail

# ============ 配置 ============
CF_API_TOKEN="${CF_API_TOKEN:-}"
CF_ACCOUNT_ID="${CF_ACCOUNT_ID:-}"
CF_ZONE_ID="${CF_ZONE_ID:-787420b4dd4956ec896bb93afa7fd989}"
CF_TUNNEL_NAME="${CF_TUNNEL_NAME:-openbot-tunnel}"
CF_HOSTNAME="${CF_HOSTNAME:-openbot.indevs.in}"
LOCAL_PORT="${LOCAL_PORT:-8888}"

CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-/tmp/cloudflared}"
CONFIG_DIR="${HOME}/.cloudflared"
CONFIG_FILE="${CONFIG_DIR}/config.yml"
CREDENTIALS_DIR="${CONFIG_DIR}"

# ============ 颜色 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err() { echo -e "${RED}[✗]${NC} $*" >&2; }

# ============ 前置检查 ============
check_prerequisites() {
    log "检查前置条件..."

    if [[ -z "$CF_API_TOKEN" ]]; then
        err "CF_API_TOKEN 未设置"
        echo "  获取方式: https://dash.cloudflare.com/profile/api-tokens"
        echo "  所需权限: Account:Cloudflare Tunnel:Edit + Zone:DNS:Edit"
        exit 1
    fi

    if [[ -z "$CF_ACCOUNT_ID" ]]; then
        # 尝试自动获取
        log "尝试自动获取 Account ID..."
        CF_ACCOUNT_ID=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
            "https://api.cloudflare.com/client/v4/accounts" | \
            python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])" 2>/dev/null || true)
        if [[ -z "$CF_ACCOUNT_ID" ]]; then
            err "无法自动获取 Account ID，请设置 CF_ACCOUNT_ID 环境变量"
            echo "  获取方式: Cloudflare Dashboard 右侧栏"
            exit 1
        fi
        log "自动获取 Account ID: $CF_ACCOUNT_ID"
    fi

    # 检查 cloudflared
    if ! command -v cloudflared &>/dev/null && [[ ! -f "$CLOUDFLARED_BIN" ]]; then
        warn "cloudflared 未安装，正在下载..."
        install_cloudflared
    fi

    if [[ ! -f "$CLOUDFLARED_BIN" ]]; then
        CLOUDFLARED_BIN=$(command -v cloudflared)
    fi

    log "cloudflared: $($CLOUDFLARED_BIN --version 2>&1)"
}

install_cloudflared() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64) arch="amd64" ;;
        aarch64) arch="arm64" ;;
        armv7l) arch="arm" ;;
        *) err "不支持的架构: $arch"; exit 1 ;;
    esac

    local url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${arch}"
    log "下载: $url"

    if command -v curl &>/dev/null; then
        curl -L -o "$CLOUDFLARED_BIN" "$url"
    elif command -v wget &>/dev/null; then
        wget -O "$CLOUDFLARED_BIN" "$url"
    else
        err "需要 curl 或 wget"; exit 1
    fi

    chmod +x "$CLOUDFLARED_BIN"
    log "安装完成: $CLOUDFLARED_BIN"
}

# ============ API 调用 ============
cf_api() {
    local method="$1" endpoint="$2"
    shift 2
    curl -s -X "$method" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        "$@" \
        "https://api.cloudflare.com/client/v4${endpoint}"
}

# ============ 隧道管理 ============
create_tunnel() {
    log "创建/获取隧道: $CF_TUNNEL_NAME"

    # 检查是否已存在
    local existing
    existing=$(cf_api GET "/accounts/${CF_ACCOUNT_ID}/cfc_tunnel/name:${CF_TUNNEL_NAME}" 2>/dev/null || true)

    if echo "$existing" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('success')" 2>/dev/null; then
        TUNNEL_ID=$(echo "$existing" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['id'])")
        TUNNEL_TOKEN=$(echo "$existing" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'].get('token',''))")
        log "隧道已存在: $TUNNEL_ID"
        return 0
    fi

    # 创建新隧道
    local response
    response=$(cf_api POST "/accounts/${CF_ACCOUNT_ID}/cfc_tunnel" \
        -d "{\"name\":\"${CF_TUNNEL_NAME}\",\"tunnel_secret\":\"$(openssl rand -hex 32)\"}")

    if echo "$response" | python3 -c "import sys,json; assert json.load(sys.stdin)['success']" 2>/dev/null; then
        TUNNEL_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['id'])")
        TUNNEL_TOKEN=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'].get('token',''))")
        log "隧道创建成功: $TUNNEL_ID"
    else
        err "创建隧道失败:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        exit 1
    fi
}

setup_dns() {
    log "配置 DNS CNAME: ${CF_HOSTNAME} → ${TUNNEL_ID}.cfargotunnel.com"

    # 检查现有记录
    local existing_records
    existing_records=$(cf_api GET "/zones/${CF_ZONE_ID}/dns_records?name=${CF_HOSTNAME}&type=CNAME")

    local record_id
    record_id=$(echo "$existing_records" | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')" 2>/dev/null || true)

    local target="${TUNNEL_ID}.cfargotunnel.com"

    if [[ -n "$record_id" ]]; then
        # 更新现有记录
        cf_api PUT "/zones/${CF_ZONE_ID}/dns_records/${record_id}" \
            -d "{\"type\":\"CNAME\",\"name\":\"${CF_HOSTNAME}\",\"content\":\"${target}\",\"proxied\":true}" > /dev/null
        log "DNS 记录已更新"
    else
        # 创建新记录
        cf_api POST "/zones/${CF_ZONE_ID}/dns_records" \
            -d "{\"type\":\"CNAME\",\"name\":\"${CF_HOSTNAME}\",\"content\":\"${target}\",\"proxied\":true}" > /dev/null
        log "DNS 记录已创建"
    fi
}

generate_config() {
    log "生成配置文件: $CONFIG_FILE"

    mkdir -p "$CONFIG_DIR"
    mkdir -p "$CREDENTIALS_DIR"

    # 写入凭证文件（新格式用 token）
    if [[ -n "${TUNNEL_TOKEN:-}" ]]; then
        echo "$TUNNEL_TOKEN" > "${CREDENTIALS_DIR}/${TUNNEL_ID}.json"
        log "凭证文件已保存"
    fi

    # 生成 config.yml
    cat > "$CONFIG_FILE" << EOF
# Cloudflare Named Tunnel 配置
# 自动生成于 $(date -Iseconds)

tunnel: ${TUNNEL_ID}
credentials-file: ${CREDENTIALS_DIR}/${TUNNEL_ID}.json

ingress:
  - hostname: ${CF_HOSTNAME}
    service: http://localhost:${LOCAL_PORT}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF

    log "配置已写入 $CONFIG_FILE"
}

# ============ 服务管理 ============
start_tunnel() {
    log "启动隧道..."

    # 停止已有进程
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    sleep 1

    nohup "$CLOUDFLARED_BIN" tunnel --config "$CONFIG_FILE" run > /tmp/cloudflared-named-tunnel.log 2>&1 &
    local pid=$!

    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        log "隧道已启动 (PID: $pid)"
        log "访问地址: https://${CF_HOSTNAME}"
        log "日志: tail -f /tmp/cloudflared-named-tunnel.log"
        echo "$pid" > /tmp/cloudflared-named-tunnel.pid
    else
        err "隧道启动失败，查看日志:"
        cat /tmp/cloudflared-named-tunnel.log
        exit 1
    fi
}

stop_tunnel() {
    log "停止隧道..."
    if [[ -f /tmp/cloudflared-named-tunnel.pid ]]; then
        kill "$(cat /tmp/cloudflared-named-tunnel.pid)" 2>/dev/null || true
        rm -f /tmp/cloudflared-named-tunnel.pid
    fi
    pkill -f "cloudflared tunnel run" 2>/dev/null || true
    log "已停止"
}

status_tunnel() {
    if [[ -f /tmp/cloudflared-named-tunnel.pid ]] && kill -0 "$(cat /tmp/cloudflared-named-tunnel.pid)" 2>/dev/null; then
        log "隧道运行中 (PID: $(cat /tmp/cloudflared-named-tunnel.pid))"
        log "地址: https://${CF_HOSTNAME}"
    else
        warn "隧道未运行"
    fi
}

# ============ 主流程 ============
usage() {
    cat << EOF
用法: $(basename "$0") <command>

命令:
  setup     完整部署（创建隧道 + DNS + 配置 + 启动）
  start     启动隧道
  stop      停止隧道
  restart   重启隧道
  status    查看状态
  clean     清理隧道资源

环境变量:
  CF_API_TOKEN    Cloudflare API Token（必填）
  CF_ACCOUNT_ID   Account ID（可自动获取）
  CF_HOSTNAME     域名（默认 openbot.indevs.in）
  CF_TUNNEL_NAME  隧道名（默认 openbot-tunnel）
  LOCAL_PORT      本地端口（默认 8888）

示例:
  CF_API_TOKEN=xxx bash scripts/cloudflare-named-tunnel.sh setup
  bash scripts/cloudflare-named-tunnel.sh status
EOF
}

main() {
    local cmd="${1:-help}"

    case "$cmd" in
        setup)
            check_prerequisites
            create_tunnel
            setup_dns
            generate_config
            start_tunnel
            ;;
        start)
            check_prerequisites
            start_tunnel
            ;;
        stop)
            stop_tunnel
            ;;
        restart)
            stop_tunnel
            sleep 1
            check_prerequisites
            start_tunnel
            ;;
        status)
            status_tunnel
            ;;
        clean)
            stop_tunnel
            if [[ -n "${CF_API_TOKEN}" ]] && [[ -n "${TUNNEL_ID:-}" ]]; then
                cf_api DELETE "/accounts/${CF_ACCOUNT_ID}/cfc_tunnel/${TUNNEL_ID}" > /dev/null 2>&1 || true
            fi
            rm -rf "$CONFIG_DIR"
            log "已清理"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            err "未知命令: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
