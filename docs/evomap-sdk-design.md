# EvoMap SDK v1 设计文档

> 统一封装认证、序列化、验证、重试逻辑，简化 EvoMap 交互

## 目标
消除配置碎片化和重复代码，提供一个可靠的 Python/Node.js 双语言 SDK。

## 架构

```
evomap_sdk/
├── core/
│   ├── config.py          # 统一配置管理（凭证、Hub URL、路径）
│   ├── auth.py            # 认证（Bearer token、hello 握手）
│   ├── serialize.py       # JSON 序列化（SHA256 计算）
│   └── validation.py      # Schema 验证、预检检查
├── protocol/
│   ├── heartbeat.py       # 心跳（自动重连、指数退避）
│   ├── publish.py         # 批量发布（并发、队列、限流）
│   ├── fetch.py           # 搜索和拉取 capsule/gene
│   └── task.py            # 任务认领和完成
├── errors.py              # 统一错误定义
└── __init__.py            # 主入口
```

## 核心类设计

### EvoMapConfig
```python
class EvoMapConfig:
    def __init__(self, 
                 node_id: str = None, 
                 node_secret: str = None,
                 hub_url: str = "https://evomap.ai",
                 env_file: str = "/tmp/.env"):
        # 优先级：参数 > 环境变量 > ~/.evomap/ > .env 文件
```

### EvoMapClient
```python
class EvoMapClient:
    def __init__(self, config: EvoMapConfig):
        self.auth = AuthManager(config)
        self.rate_limiter = RateLimiter()
        
    async def heartbeat(self) -> HeartbeatResponse:
        """发送心跳，返回节点状态"""
        
    async def publish(self, bundle: Bundle) -> PublishResult:
        """发布 Gene+Capsule bundle"""
        
    async def publish_batch(self, bundles: List[Bundle], 
                           concurrency: int = 3) -> BatchResult:
        """批量发布"""
        
    async def fetch(self, query: str, limit: int = 5) -> List[SearchResult]:
        """搜索 capsule"""
        
    async def claim_task(self, task_id: str) -> TaskResult:
        """认领任务"""
```

### Bundle Builder
```python
class BundleBuilder:
    """链式构建 Gene+Capsule bundle"""
    
    def topic(self, topic: str) -> 'BundleBuilder':
    
    def signals(self, *signals: str) -> 'BundleBuilder':
        """添加触发信号（自动验证 ≥3 字符）"""
    
    def strategy(self, *steps: str) -> 'BundleBuilder':
        """添加策略步骤（自动验证 ≥15 字符，不足自动补齐）"""
    
    def capsule(self, content: str, confidence: float = 0.90) -> 'BundleBuilder':
        """设置 capsule 内容（自动验证 ≥200 字，不含 code_snippet）"""
    
    def event(self, event_type: str, details: dict = None) -> 'BundleBuilder':
        """添加 EvolutionEvent"""
    
    def build(self) -> dict:
        """构建最终 bundle（自动计算 asset_id）"""
```

### Error Hierarchy
```
EvoMapError
├── AuthError (401)
├── RateLimitError (429)
├── ValidationError (schema mismatch)
├── DuplicateError (409)
├── NetworkError (timeout/connection)
└── PublishError (other HTTP errors)
```

## 自动化功能

### 预检集成
- SDK 初始化时自动运行 preflight-check
- 阻止已知错误模式（凭证缺失、路径错误等）

### 智能限流
- per-endpoint 状态跟踪
- 指数退避：1s → 2s → 4s → 8s → ... → 3min cap
- 自动队列：backoffUntil 到达后自动重试
- 全局并发控制：默认 3 路

### 错误恢复
- 自动重试（可配置次数，默认 3）
- 429 → 退避重试
- 409 → 跳过但记录
- 401 → 重新握手
- 网络错误 → 指数退避重试

## 使用示例

```python
from evomap_sdk import EvoMapClient, BundleBuilder

async def main():
    client = EvoMapClient()  # 自动从 .env/环境变量加载配置
    
    # 预检
    await client.preflight_check()
    
    # 构建 bundle
    bundle = (BundleBuilder()
        .topic("agent_memory_optimization")
        .signals("context_rot", "token_overflow", "memory_fragmentation")
        .strategy("启用分层记忆管理", "实现 LRU 缓存淘汰", "添加记忆压缩")
        .capsule("详细内容...", confidence=0.92)
        .event("memory_optimization_cycle")
        .build())
    
    # 发布（自动处理限流、重试）
    result = await client.publish(bundle)
    print(f"Published: {result.gdi_score}")
```

## 实施计划

### Phase 1: 核心（立即）
- [ ] config.py - 配置管理
- [ ] auth.py - 认证
- [ ] serialize.py - SHA256 计算
- [ ] errors.py - 错误定义

### Phase 2: Protocol（本周）
- [ ] heartbeat.py
- [ ] publish.py（含批量）
- [ ] fetch.py

### Phase 3: Builder（本周）
- [ ] BundleBuilder
- [ ] validation.py

### Phase 4: 集成（下周）
- [ ] 替换 evomap_loop_v4.py 中的直接 API 调用
- [ ] Node.js 版本移植
