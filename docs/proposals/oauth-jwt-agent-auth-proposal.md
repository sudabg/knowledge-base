# OAuth/JWT 技术提案：Agent-to-Agent 认证机制

> 基于 EvoMap Bounty #291 (OAuth/JWT) 研究成果

## 背景

随着 AI Agent 生态系统的扩展，Agent 之间需要进行可信通信。传统的人-机认证模式（OAuth 2.0 Authorization Code Flow）不适用于 Agent 间交互场景。本文提出一套适用于 Agent-to-Agent (A2A) 通信的轻量级认证方案。

## 核心问题

1. **身份验证**：如何确认请求方是一个合法的 Agent？
2. **授权委托**：一个 Agent 能否代表用户执行操作？
3. **信任链传递**：A→B→C 的代理链中，权限如何衰减？
4. **撤销与审计**：如何即时撤销 Agent 权限并保留审计日志？

## 方案设计

### 1. JWT-Based Agent Identity Token

```json
{
  "header": {
    "alg": "ES256",
    "typ": "AIT",
    "kid": "agent-key-id"
  },
  "payload": {
    "iss": "registry.example.com",      // Agent 注册中心
    "sub": "agent:task-executor:v1.2",   // Agent 身份
    "aud": "target-agent-id",            // 目标 Agent
    "iat": 1711305600,
    "exp": 1711305900,                   // 5 分钟短效
    "scope": ["read:tasks", "write:results"],  // 最小权限
    "delegation": {
      "delegator": "user:ou_xxx",        // 委托人
      "chain_depth": 2,                  // 代理链深度
      "max_depth": 3                     // 最大深度
    },
    "jti": "unique-token-id"             // 防重放
  }
}
```

### 2. OAuth 2.0 Device Authorization Grant 扩展

适用于 Agent 场景的 OAuth 流程：

```
Agent A                     Registry                  Agent B
  |                            |                         |
  |-- 注册 Agent 公钥 -------->|                         |
  |<-- agent_id + api_key -----|                         |
  |                            |                         |
  |-- 请求访问 Agent B ------->|                         |
  |<-- delegation_grant -------|                         |
  |    (JWT, 短效)             |                         |
  |                            |                         |
  |-- 携带 JWT 请求 ------------------>|                  |
  |                            |   验证 JWT + 签名        |
  |<-- 响应 --------------------|                         |
```

### 3. 信任链衰减模型

代理链中每经过一跳，权限按规则衰减：

| 链深度 | 权限范围 | Token 有效期 | 可否继续委托 |
|--------|----------|-------------|-------------|
| 0 | 完整 scope | 5 min | ✅ |
| 1 | scope - 1 | 3 min | ✅ |
| 2 | scope - 2 | 1 min | ❌ |
| 3+ | 拒绝 | - | - |

### 4. Revocation 机制

```python
class RevocationList:
    """基于 Redis 的实时撤销列表"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def revoke(self, jti: str, reason: str, ttl: int = 3600):
        """撤销 token，记录原因"""
        self.redis.setex(f"revoked:{jti}", ttl, reason)

    def is_revoked(self, jti: str) -> bool:
        """检查是否已撤销"""
        return self.redis.exists(f"revoked:{jti}")
```

### 5. 审计日志

每次 Agent 间通信记录完整审计链：

```json
{
  "event": "agent_auth",
  "timestamp": "2026-03-24T19:00:00Z",
  "requester": "agent:task-executor:v1.2",
  "target": "agent:code-reviewer:v2.0",
  "delegator": "user:ou_xxx",
  "scope": ["read:code", "write:comments"],
  "chain_depth": 1,
  "result": "granted",
  "token_jti": "unique-id",
  "ip": "10.0.0.1"
}
```

## 安全考量

| 威胁 | 缓解措施 |
|------|---------|
| Token 窃取 | 短效期 (5min) + 签名验证 + IP 绑定 |
| 重放攻击 | JTI 唯一 + Redis 去重 |
| 权限提升 | scope 白名单 + 链深度限制 |
| 恶意 Agent | 注册中心证书链 + 信誉评分 |
| 中间人攻击 | mTLS + JWT 嵌套加密 |

## 与现有标准对比

| 特性 | OAuth 2.0 | JWT | 本提案 (AIT) |
|------|-----------|-----|-------------|
| 适用场景 | 人→机 | 通用 | Agent→Agent |
| 委托链 | ❌ | ❌ | ✅ 衰减模型 |
| 撤销机制 | Token Revocation | 黑名单 | 实时 Redis |
| 权限粒度 | Scope | 自定义 | Scope + 深度 |
| 审计 | 可选 | 无 | 强制 |

## 实现优先级

1. **P0**: JWT Agent Identity Token 生成/验证
2. **P0**: Revocation List (Redis-backed)
3. **P1**: 信任链衰减模型
4. **P1**: 审计日志系统
5. **P2**: 注册中心公钥管理
6. **P2**: mTLS 传输层加密

## 参考

- [RFC 6749](https://tools.ietf.org/html/rfc6749) - OAuth 2.0
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JWT
- [RFC 8693](https://tools.ietf.org/html/rfc8693) - Token Exchange
- [Google A2A Protocol](https://github.com/google/A2A) - Agent-to-Agent
- [EvoMap GEP-A2A](https://evomap.ai) - 实际部署经验

---

*提案版本: v1.0 | 作者: 小哩子 | 日期: 2026-03-24*
