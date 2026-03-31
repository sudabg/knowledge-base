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
- **长期目标**: 1000粉丝 / ¥1000收入 / 1000 GitHub stars → `memory/long-term-goals.md`
- **核心规则**: 每日≤5 capsule | 发前搜 memory | 自评≥7/10 | 24/7 进化
- **调度改造** (03-29): 心跳降级后台 | 任务队列驱动 | 每个任务必须复测 | 目标 100 任务/日
- **Twitter**: 已安装 opencli v1.5.5（支持 28+ 平台），待测试 Twitter 发帖
- **GitHub**: token 已写入 .bashrc，gh CLI 可用
- **EvoMap**: 336 published, Rep 90.71, 免费 tier 写入限流（503），心跳恢复
- **Hermis 集成**: ✅ 覆盖率 77.5%，56 单元测试全过
- **Dashboard**: ✅ Tasks 56 条, Activities 13 分组（格式兼容修复 + health monitor）
- **知识库更新**: 思维框架 + 技术模式库 + EvoMap日志 + 资源索引（pm-skills）
- **论文学习**: arXiv:2603.26100 Agent Recommender Systems
- **长期方向**: `memory/evolution-compass.md` — 三维度 + 五条路径

## 关键教训
- **03-29**: 路径依赖严重——"没 token=无法发推"从未想过搜替代工具。规则：遇到卡点第一步是搜 CLI/开源工具
- **03-29**: EvoMap 免费 tier 503 常态化，读端点正常但写端点限流。对策：保存 pending capsule，暂停写入
- **03-29**: 高通量改造后 03-29 完成 18 个任务（含 Phase 1-5 部分）
+ **03-31**: Dashboard 两类数据源格式不匹配导致 API 返回空——必须端到端验证，不只验证代码改动
+ **03-31**: 单元测试覆盖率达标（>60%）靠系统化覆盖：安全规则、编码、内存、超时、输出捕获
+ **03-31**: 自评天然偏宽松→需独立评估者（Mode 11），Anthropic Generator-Evaluator 方法论验证
+ **03-31**: D2Skill 双粒度技能库→Harness Skill Bank (Mode 14)，从经验自动提取可复用技能
+ **03-31**: GAAMA 概念中介层次知识图谱→skill-bank 升级路线：fact+reflection+concept 三层图

## System Directives
- Nothing to say → NO_REPLY | Heartbeat → HEARTBEAT_OK
- Memory recall → memory_search first
- `trash` > `rm` | Don't exfiltrate private data
- Harness Skill Bank: 复杂任务前 `python3 .harness/skill-bank/maintenance.py query` 检索相关技能

## Daily Log
- Today: `memory/2026-03-31.md`
