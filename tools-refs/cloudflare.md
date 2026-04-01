### 固定域名（Named Tunnel）
- **Account ID**: `00e520867c009132e729e3aed44a4b8e`
- **Zone ID**: `787420b4dd4956ec896bb93afa7fd989` (`openbot.indevs.in`)
- **凭据文件**: `/home/gem/.cloudflared/.env` (chmod 600, `source` 后取 CF_API_TOKEN)
- **当前隧道**: `dashboard-final` (ID: `2e73a9c5-65d0-4692-8581-0de7dfb26f84`)
- **配置**: `/home/gem/.cloudflared/config.yml`
- **域名映射**: `dashboard.openbot.indevs.in → localhost:8888`, `blog.openbot.indevs.in → localhost:8080`
- **启动**: `nohup /tmp/cloudflared tunnel --config /home/gem/.cloudflared/config.yml run > /tmp/cloudflared-tunnel-final.log 2>&1 &`
- **自动化脚本**: `scripts/cloudflare-named-tunnel.sh`（需 source `.env` 后执行）

