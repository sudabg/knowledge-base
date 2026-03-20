# Memory Expiry Configuration

> 定义记忆层级的过期规则。每次 heartbeat 维护时执行 `memory-expiry.sh` 检查。

## TTL Presets

| Category | Tier | TTL | 说明 |
|----------|------|-----|------|
| ephemeral | HOT→delete | 1天 | 心跳数据、临时状态、API 响应缓存 |
| tactical | WARM→COLD | 3天 | 活跃项目状态、当日待办、进行中的任务 |
| strategic | COLD→archive | 30天 | 决策记录、模式总结、经验教训 |
| permanent | never | ∞ | 身份信息、核心配置、协议文档、用户画像 |

## Expiry Annotation Format

在 markdown 中用 HTML 注释标记过期元数据：

```markdown
<!-- expiry:2026-03-15T14:00:00+08:00 category:ephemeral -->
- **Heartbeat**: credit 2910, penalty 1.73
```

或用 YAML frontmatter（jsonl 文件）：
```json
{"expiry": "2026-03-15T14:00:00+08:00", "category": "ephemeral", "content": "..."}
```

## File-Level Defaults

| File | Default Category | Auto-Expiry |
|------|-----------------|-------------|
| `memory/YYYY-MM-DD.md` | tactical | 3天后精简 → 提取到 archive.md |
| `memory/active.md` | tactical | 每次更新时刷新时间戳 |
| `memory/protocols.md` | permanent | 不过期（手动更新） |
| `memory/archive.md` | strategic | 30天后 review |
| `memory/ontology/graph.jsonl` | strategic | 实体 30天无更新→降级 |
| `.learnings/last_heartbeat.json` | ephemeral | 覆盖式更新 |

## Expiry Actions

| Action | 描述 |
|--------|------|
| `downgrade` | 从 HOT 移到 WARM，或 WARM→COLD，或 COLD→archive |
| `compress` | 提取精华到上一层，原文删除 |
| `delete` | 直接删除（仅 ephemeral） |
| `review` | 标记需要人工 review，不自动删除 |

## Maintenance Schedule

- **每 6 小时**（heartbeat 触发）: 扫描 ephemeral 过期项
- **每天 00:00**: 处理 tactical 过期项（daily log 精简）
- **每周日**: review strategic 层，归档已完成项目
