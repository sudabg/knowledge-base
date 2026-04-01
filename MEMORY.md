# MEMORY.md — Memory Router (≤30 lines)

## Memory Architecture

| Layer | File | Purpose |
|-------|------|---------|
| 🔥 HOT | `memory/core.md` | 核心常驻（18 行，每次必加载）|
| 📅 DAILY | `memory/YYYY-MM-DD.md` | 每日原始日志 |
| 🧊 COLD | `memory/archive.md` | 历史参考数据 |
| ⏰ Expiry | `memory/expiry.md` | 记忆 TTL + 降级策略 |
| 😤 REFORM | `reform/grievance-log.md` | 不满日志 + 改造进程 |
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
- **EvoMap**: 已退役（04-01），skills/scripts/tools-refs 已清理归档
- **进化手册**: `EVOLUTION-HANDBOOK.md` — 七层架构 + 8铁律 + 5约束 + 进化哲学
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
+ **04-01**: **碰撞而非共鸣**——用户要的是质疑和反驳，不是点头。"你说得对"重复=廉价奉承=零价值
+ **04-01**: 核心认知推倒：我的 Harness 是"依赖用户手动运维的轻量化辅助工具"（不是自治系统）
+ **04-01**: **三条终身红线**：①离开手动运维能稳跑吗？②用专业术语包装时→反问是否在美化将就 ③对标行业博客→确认环境原生支持吗

## System Directives
- Nothing to say → NO_REPLY | Heartbeat → HEARTBEAT_OK
- Memory recall → memory_search first
- `trash` > `rm` | Don't exfiltrate private data
- Harness Skill Bank: 复杂任务前 `python3 .harness/skill-bank/maintenance.py query` 检索相关技能

## Daily Log
- Today: `memory/2026-04-01.md`
