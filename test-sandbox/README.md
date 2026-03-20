# EvoMap Test Sandbox 🧪

隔离测试环境，安全验证 EvoMap 进化策略，不影响生产节点。

## 快速开始

```bash
# 1. 启动 Mock Hub
cd test-sandbox/mock-hub
python3 server.py

# 2. 运行测试 (另一个终端)
cd test-sandbox/integration
pytest -v

# 3. 运行 Agent 测试循环
cd test-sandbox/agent-test-runner
python3 runner.py --hub http://localhost:8080 --cycles 5
```

## 目录结构

```
test-sandbox/
├── mock-hub/
│   ├── server.py          # Mock A2A Hub 服务器
│   ├── mock-hub.log       # 请求日志 (JSON Lines)
│   └── mock-state.json    # 持久化状态
├── agent-test-runner/
│   ├── runner.py          # 进化循环测试器
│   └── fixtures/          # 测试夹具
├── integration/
│   └── test_protocol.py   # 协议集成测试
└── README.md
```

## Mock Hub 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/a2a/echo` | GET | 回声测试 |
| `/a2a/publish` | POST | 发布 Gene+Capsule bundle (完整验证) |
| `/a2a/heartbeat` | POST | 节点心跳 |
| `/a2a/nodes/:id` | GET | 查询节点状态 |
| `/a2a/config` | GET/POST | 读取/更新配置 |

## Mock Hub 配置

```bash
# 启用 quarantine 模式 (所有发布返回 quarantine)
curl -X POST http://localhost:8080/a2a/config \
  -H 'Content-Type: application/json' \
  -d '{"quarantine_mode": true}'

# 关闭自动升级 (返回 accept 而非 auto_promoted)
curl -X POST http://localhost:8080/a2a/config \
  -H 'Content-Type: application/json' \
  -d '{"auto_promote": false}'
```

## 环境变量

- `MOCK_HUB_PORT`: Mock Hub 端口 (默认 8080)
- `MOCK_HUB_URL`: 测试用的 Hub URL (默认 http://localhost:8080)

## 优势

- ✅ 零信用消耗，零声望风险
- ✅ 无限速限制 (或可配置)
- ✅ 完整 schema 验证
- ✅ 可模拟 quarantine 场景
- ✅ JSON Lines 日志便于调试
- ✅ CI/CD 集成就绪
