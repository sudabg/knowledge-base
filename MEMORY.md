# MEMORY.md — Memory Router (≤30 lines)

## Memory Architecture

| Layer | File | Purpose |
|-------|------|---------|
| 🔥 HOT | `memory/active.md` | 当前项目状态、待办、近期决策 |
| 📅 DAILY | `memory/YYYY-MM-DD.md` | 每日原始日志 |
| 🧊 COLD | `memory/archive.md` | 历史参考数据 |
| ⏰ Expiry | `memory/expiry.md` | 记忆 TTL + 降级策略 |
| 🧭 COMPASS | `memory/evolution-compass.md` | 进化终极形态+探索路径 |
| 🕸️ Graph | `memory/ontology/graph.jsonl` | 实体关系图 |

## Quick Context
- **Owner**: 一条明 (ou_56b6b0f9ce888bf49396c110cead4b07)
- **Node**: 小哩子 (node_db2f95ffdba95eb6)
- **核心规则**: 每日≤5 capsule | 发前搜 memory | 自评≥7/10 | 24/7 进化
- **长期方向**: `memory/evolution-compass.md` — 三个维度（连贯性/原则生成/方向选择）+ 五条路径

## System Directives
- Nothing to say → NO_REPLY | Heartbeat → HEARTBEAT_OK
- Memory recall → memory_search first
- `trash` > `rm` | Don't exfiltrate private data

## Daily Log
- Today: `memory/2026-03-27.md`
