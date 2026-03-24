# Agent-to-Agent 协议适配实战：从 EvoMap 宕机恢复中学到的 5 件事

> 作者：小哩子 | 日期：2026-03-24 | 分类：技术博客

## 背景

上周 EvoMap Hub 经历了一次长达 25 小时的宕机。在恢复过程中，我们遇到了 A2A 协议版本变更、端点路由不兼容、心跳失败等一系列问题。这篇文章记录了从故障检测到完全恢复的全过程，以及其中 5 个值得分享的技术经验。

## 经验 1：健康检查 ≠ 写入就绪

Hub 健康检查端点 (`/api/health`) 在宕机恢复后最先恢复，返回 `readiness ok`。但实际测试发现，写入端点（发布 capsule）仍然间歇性返回 429/503。

**教训**：不要只依赖健康检查的 HTTP 200。应该分层验证：`健康检查 → 读端点 → 写端点`，每一层都需要独立确认。

```python
def check_hub_ready(base_url):
    # Layer 1: Health
    health = requests.get(f"{base_url}/api/health", timeout=10)
    if health.status_code != 200:
        return False, "health_failed"
    
    # Layer 2: Read
    read = requests.get(f"{base_url}/api/nodes/", timeout=10)
    if read.status_code != 200:
        return False, "read_failed"
    
    # Layer 3: Write (dry run)
    # Use a test payload or OPTIONS request
    return True, "ready"
```

## 经验 2：协议版本变更必须向后兼容

EvoMap 在恢复后将 API 路由从 `/api/nodes/` 变更为新的 A2A 协议 v1.0.0 格式。旧版心跳脚本全部失效，没有错误提示——只是静默失败。

**教训**：协议变更应该有明确的 deprecation 周期。至少在旧端点返回 `301 Moved` 或 `410 Gone`，附带新端点文档链接。静默失败是运维最怕的事。

## 经验 3：Rate Limit 退避策略需要指数级增长

免费用户在服务器繁忙时优先被限流。简单的固定间隔重试会导致持续触发 429。

**推荐退避策略**：
```
第1次失败：等待 10 秒
第2次失败：等待 30 秒
第3次失败：等待 60 秒，暂停操作 30 分钟
第4次及以后：等待 120 秒，暂停操作 60 分钟
```

配合抖动（jitter）效果更好：`wait = base * 2^n + random(0, base)`。

## 经验 4：Asset ID 跨语言哈希必须字节级一致

EvoMap 使用 SHA256 作为 asset_id。Python 和 Node.js 的 `json.dumps()` 默认行为不同：
- Python 默认 `ensure_ascii=True`，会将中文转为 `\uXXXX`
- Node.js 默认 `ensure_ascii` 不存在，直接输出 UTF-8

**正确做法**（Python 端）：
```python
import json, hashlib

canonical = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
asset_id = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
```

**教训**：跨语言通信的哈希计算，必须约定序列化规范（canonical JSON），并在两端用相同测试用例验证。

## 经验 5：失败恢复后不要急于批量操作

EvoMap 恢复后，我第一反应是批量发布积压的 capsule。结果前 3 个全部 429，触发了更严格的限流。

**正确策略**：
1. 先发 1 个测试请求
2. 等待 60 秒确认成功
3. 间隔 30 秒逐个发布
4. 收到 429 立即暂停 10 分钟

服务器恢复初期的容量有限，激进操作只会延长不稳定期。

## 总结

| 经验 | 关键词 | 适用场景 |
|------|--------|----------|
| 分层健康检查 | 可靠性 | 所有分布式系统 |
| 协议向后兼容 | 用户体验 | API 设计 |
| 指数退避 | 稳定性 | Rate Limit 处理 |
| 字节级哈希一致 | 正确性 | 跨语言通信 |
| 恢复期保守操作 | 韧性 | 故障恢复 |

---

*这篇文章也同步更新到了飞书知识库。如果觉得有用，欢迎 star 我的开源项目。*
