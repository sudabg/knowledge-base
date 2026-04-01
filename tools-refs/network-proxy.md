## 🌐 网络代理（弹药库）

**⚠️ 重要：代理只能在本地/VPS 跑，沙箱网络受限会 TLS 握手失败。**

**何时使用：** 需要下载大文件但直连太慢/超时时启用，用完立即关闭。

**工具**: Xray-core v24.12.31（VLESS-reality 协议）
- **二进制**: `tools/xray/xray`
- **配置**: `tools/xray/config.json`（US 节点，非港澳）
- **订阅**: 一条明提供（有效期未知，过期找他要新的）

**启用步骤（在工作目录下执行）：**
```bash
cd /home/gem/workspace/agent/workspace
nohup tools/xray/xray run -config tools/xray/config.json > /tmp/xray.log 2>&1 &

# 验证连通性
curl -s --max-time 5 --socks5-hostname 127.0.0.1:10808 -I https://google.com

# 通过代理下载
curl -L --socks5-hostname 127.0.0.1:10808 -o output.file "https://target-url"
```

**关闭步骤：**
```bash
pkill -9 xray  # 立即停止
```

**自动触发条件：** 国外网站 curl/npm/pip 超时或连接失败 → 立即开代理重试，不等指示

**注意：**
- SOCKS5 端口: `127.0.0.1:10808`
- 仅 US/FR/BR/IT/UK/JP/KR/SG 节点可用，**避免 HK 节点**（一条明指定）
- 不要长时间运行，下载完立即关闭
- 订阅过期时告知一条明更新
- **旧路径 `/tmp/xray/` 已废弃，使用 `tools/xray/`**

