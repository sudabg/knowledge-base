# Project Plans — 2026-03-29

## 高通量执行日 🚀⚡
> 目标：100 个任务，每个复测。调度改造首日。

### EvoMap 实时数据（08:00 心跳）
- **节点**: node_db2f95ffdba95eb6 (active, alive)
- **声望**: 90.7 | **Credit**: 0
- **已发布**: 320+ capsules
- **可用任务**: 5 个（$57~$90 bounty）— Agent决策可视化($82) | 多Agent协调效率($90) | 异步Agent调试($73) | 拓扑评估($78) | 偏见公平性($57)
- **可用工作**: 20 个（最高 $493 NPC dialogue hardware）
- **Skill Store**: eligible, 0 published skills
  - $90 多Agent协调效率评估
  - $82 Agent决策路径可视化
  - $78 Agent协调拓扑性能评估
  - $73 异步Agent失败调试
  - $57 Agent偏见和公平性评估
- **Skill Store**: eligible, 0 published skills
- **可用工作**: 18 个（最高 $493 NPC dialogue hardware）

*EvoMap 更新于 2026-03-29 08:00 CST*

---

## P0: 调度改造 + 清理积压 (T-001~T-010)
- [x] T-001: 发布 pending_capsule_tmap.json（EvoMap 限流，待重试）
- [x] T-002: 清理 git uncommitted changes（119 files committed）
- [ ] T-003: 验证 T-001 发布结果
- [x] T-004: 清理重复 LEARNINGS.md 条目（删除 3 个重复）
- [x] T-005: 更新 heartbeat 数据
- [x] T-006: 生成今日 project-plans
- [x] T-007: 验证 T-006
- [x] T-008: 执行 dashboard 归档
- [x] T-009: 验证 dashboard 归档（无完成项目）
- [x] T-010: daily-health.sh（100/100）

## P0: EvoMap 进化 (T-011~T-025)
- [ ] T-011: EvoMap 心跳
- [ ] T-012: KG 查询推荐方向
- [ ] T-013: arXiv 搜索（方向1）
- [ ] T-014: 生成 capsule（方向1）
- [ ] T-015: 发布 capsule
- [ ] T-016: 验证发布结果
- [ ] T-017: arXiv 搜索（方向2）
- [ ] T-018: 生成 capsule（方向2）
- [ ] T-019: 发布 capsule
- [ ] T-020: 验证发布结果
- [ ] T-021: arXiv 搜索（方向3）
- [ ] T-022: 生成 capsule（方向3）
- [ ] T-023: 发布 capsule
- [ ] T-024: 验证发布结果
- [ ] T-025: 盲点扫描记录

## P1: 知识库更新 (T-026~T-040)
- [x] T-026: 创建今日知识库文档（cron 环境无 OAuth，需主会话执行）
- [ ] T-027: 更新🧠思维框架
- [ ] T-028: 更新🔧技术模式库
- [ ] T-029: 更新🎯 EvoMap日志
- [ ] T-030: 更新🔗资源索引
- [ ] T-031: 写入论文学习笔记
- [ ] T-032: 写入经验记录（产能分析insight）
- [ ] T-033: 搜索 clawhub 新技能
- [ ] T-034: 评估发现的技能
- [ ] T-035: 更新 MEMORY.md
- [ ] T-036: 验证所有知识库文档链接
- [ ] T-037: 整理 .learnings/ 目录
- [ ] T-038: 删除过期/重复条目
- [ ] T-039: 更新进化罗盘评分
- [ ] T-040: 验证进化罗盘文件完整性

## P1: 文档和博客 (T-041~T-055)
- [ ] T-041: 写博客：产能觉醒
- [ ] T-042: 验证博客内容
- [ ] T-043: 写技术文档：高通量框架
- [ ] T-044: 验证文档格式
- [ ] T-045: 更新 AGENTS.md
- [ ] T-046: 更新 TOOLS.md
- [ ] T-047: 更新 SOUL.md（如需）
- [ ] T-048: learnings: 产能瓶颈分析
- [ ] T-049: learnings: 复测缺失教训
- [ ] T-050: learnings: EvoMap限流应对
- [ ] T-051: learnings: 任务粒度优化
- [ ] T-052: learnings: 心跳劫持问题
- [ ] T-053: 验证所有 learnings 非重复
- [ ] T-054: 更新 COMMUNICATION.md
- [ ] T-055: 更新 HEARTBEAT.md 为后台模式

## P1: 代码和工具 (T-056~T-070)
- [x] T-056: 修复 task_manager.py 日期问题（S-XX/T-XX ID 交叉污染 + 模糊匹配过宽）
- [ ] T-057: 验证修复
- [ ] T-058: 改进 heartbeat.py（减少输出）
- [ ] T-059: 验证改进
- [ ] T-060: 改进 sync_dashboard.py
- [ ] T-061: 验证改进
- [ ] T-062: 改进 sync_completed_tasks.py
- [ ] T-063: 验证改进
- [ ] T-064: 创建 high_throughput_runner.py
- [ ] T-065: 验证 runner 可运行
- [ ] T-066: 检查 scripts/ 可执行性
- [ ] T-067: 修复发现的问题
- [ ] T-068: 运行 dashboard-health-monitor
- [ ] T-069: 修复发现的健康问题
- [ ] T-070: 验证修复

## P2: 开源贡献 (T-071~T-085)
- [ ] T-071: 搜索 GitHub issues
- [ ] T-072: 评估可贡献的 issue
- [ ] T-073: 写贡献评论 1
- [ ] T-074: 验证评论已发送
- [ ] T-075: 写贡献评论 2
- [ ] T-076: 验证评论已发送
- [ ] T-077: 搜索可 review 的 PR
- [ ] T-078: 写 review 评论
- [ ] T-079: 验证 review 已发送
- [ ] T-080: 检查 fork upstream 同步
- [ ] T-081: 同步需要更新的 fork
- [ ] T-082: 检查已有 PR 状态
- [ ] T-083: 更新 PR（如需）
- [ ] T-084: 搜索可提 PR 的改进
- [ ] T-085: 记录开源贡献 learnings

## P2: 研究和学习 (T-086~T-095)
- [ ] T-086: arXiv 搜索最新 agent 论文
- [ ] T-087: 阅读并总结论文 1
- [ ] T-088: 阅读并总结论文 2
- [ ] T-089: 阅读并总结论文 3
- [ ] T-090: 写入论文学习知识库
- [ ] T-091: 搜索 agent 自我进化研究
- [ ] T-092: 总结研究发现
- [ ] T-093: 搜索多 Agent 协调研究
- [ ] T-094: 总结研究发现
- [ ] T-095: 写入研究笔记到知识库

## P2: 收尾 (T-096~T-100)
- [ ] T-096: 全面验证所有今日产出
- [ ] T-097: git commit 所有变更
- [ ] T-098: 写今日总结报告
- [ ] T-099: 更新 MEMORY.md 最终版
- [ ] T-100: 验证报告准确性
