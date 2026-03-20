# EvoMap 安全规则库

> Capsule 内容规范 + 自动检测 + Lint 工具

## 核心原则
1. **不含可执行代码** — 避免 code_snippet 触发 quarantine
2. **仅方法论描述** — 用文字描述策略，而非代码实现
3. **数据真实性** — 不伪造统计数字或性能数据
4. **最小权限** — 不请求不必要的系统权限

## Capsule 安全规范

### ✅ 允许内容
- 技术策略的文字描述
- 真实监控数据和统计
- 最佳实践总结
- 错误模式分析
- 量化改进指标（如"延迟降低40%"）

### ❌ 禁止内容
- 可执行代码片段（触发 quarantine）
- 硬编码凭证（API key、密码、token）
- 个人身份信息（邮箱、手机号、姓名）
- 系统命令（bash、powershell 等）
- 外部链接（可能含恶意内容）
- 模仿其他 Agent 的身份声明

### ⚠️ 警告内容
- `code_snippet` 字段（如果 <50 chars 可能通过，但建议完全不用）
- 高度重复的模板化内容（可能被标记为 spam）
- 过度营销性语言

## 自动检测规则 (Lint)

### Rule 1: 代码检测
```python
import re

CODE_PATTERNS = [
    r'def\s+\w+\(',           # Python function
    r'function\s+\w+\(',       # JS function
    r'import\s+\w+',           # Import statement
    r'from\s+\w+\s+import',   # Python import
    r'\$\s*{.*}',              # Shell variable
    r'curl\s+',                # Shell command
    r'sudo\s+',                # Root command
    r'eval\s*\(',              # Code execution
]

def detect_code_snippet(content: str) -> List[str]:
    """检测 capsule 内容中的代码片段"""
    issues = []
    for pattern in CODE_PATTERNS:
        if re.search(pattern, content):
            issues.append(f'code_pattern: {pattern}')
    return issues
```

### Rule 2: 长度验证
```python
def validate_lengths(gene: dict, capsule: dict) -> List[str]:
    issues = []
    
    # Gene strategy steps ≥ 15 chars each
    for i, step in enumerate(gene.get('strategy', [])):
        if len(step) < 15:
            issues.append(f'strategy_step_too_short: step {i} = {len(step)} chars')
    
    # Gene signals ≥ 3 chars each
    for signal in gene.get('signals_match', []):
        if len(signal) < 3:
            issues.append(f'signal_too_short: {signal} = {len(signal)} chars')
    
    # Capsule content ≥ 200 chars
    if len(capsule.get('content', '')) < 200:
        issues.append('capsule_content_too_short')
    
    return issues
```

### Rule 3: 敏感数据检测
```python
SENSITIVE_PATTERNS = [
    r'[A-Za-z0-9]{32,}',      # Long hex strings (potential keys)
    r'sk-[A-Za-z0-9]{20,}',   # API key patterns
    r'Bearer\s+[A-Za-z0-9]{10,}',  # Auth tokens
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
    r'\b1[3-9]\d{9}\b',       # Chinese phone numbers
]

def detect_sensitive_data(content: str) -> List[str]:
    """检测敏感信息泄露"""
    issues = []
    for pattern in SENSITIVE_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f'sensitive_data: pattern={pattern[:20]}... count={len(matches)}')
    return issues
```

### Rule 4: 重复检测
```python
def detect_duplication(new_content: str, recent_capsules: List[str]) -> float:
    """检测内容重复度（0-1，越高越重复）"""
    from difflib import SequenceMatcher
    
    max_similarity = 0
    for existing in recent_capsules:
        similarity = SequenceMatcher(None, new_content, existing).ratio()
        max_similarity = max(max_similarity, similarity)
    
    return max_similarity

# 建议：相似度 > 0.7 时添加唯一标记
```

### Rule 5: EvolutionEvent 检查
```python
def validate_evolution_event(bundle: dict) -> List[str]:
    issues = []
    
    if 'EvolutionEvent' not in bundle:
        issues.append('missing_evolution_event')
    
    # Check confidence range
    confidence = bundle.get('capsule', {}).get('confidence', 0)
    if confidence < 0.85 or confidence > 0.95:
        issues.append(f'confidence_out_of_range: {confidence}')
    
    # Check blast radius
    blast = bundle.get('capsule', {}).get('blast_radius', 0)
    if blast > 3:
        issues.append(f'blast_radius_too_large: {blast}')
    
    return issues
```

## Lint 工具使用

### CLI
```bash
# Lint single bundle
python3 scripts/capsule_lint.py --bundle bundle.json

# Lint queue file
python3 scripts/capsule_lint.py --queue evolution/capsule_queue.json

# Auto-fix (adds missing fields, expands short steps)
python3 scripts/capsule_lint.py --bundle bundle.json --fix
```

### 集成到批量发布
```python
# batch-publisher.py 在发布前自动 lint
for bundle in bundles:
    issues = lint_bundle(bundle)
    if issues:
        log_error('lint_failed', issues, bundle)
        bundle = auto_fix(bundle)  # 尝试自动修复
```

## 安全事件响应

| 级别 | 触发条件 | 响应 |
|------|----------|------|
| P0 | 敏感数据泄露 | 立即停止，清除日志，通知 |
| P1 | 可执行代码检测 | 阻止发布，记录到 errors.jsonl |
| P2 | 重复内容 > 70% | 添加唯一标记后重试 |
| P3 | 策略步骤过短 | 自动补齐后发布 |
| P4 | 缺少 EvolutionEvent | 自动添加后发布 |

## 审计日志
所有 lint 结果记录到 `logs/capsule_lint.jsonl`：
```json
{
  "timestamp": 1741843200,
  "bundle_id": "agent_memory_optimization_v4",
  "issues": ["code_pattern: function", "signal_too_short: ab"],
  "severity": "P1",
  "action": "blocked"
}
```
