# Autonomy Protocol — 从 claude-code 学到的自主执行模式

## 来源
- Claude Code (anthropics/claude-code) query.ts 自主循环
- Auto Mode (yoloClassifier.ts) 三级权限分类
- 分析时间: 2026-04-02 02:07

## 1. 自主循环 (while true 模式)

Claude Code 收到回复后不是结束，而是：
1. 调 API → 回复/工具调用
2. 执行工具
3. 再调 API（带工具结果）
4. 循环直到无工具调用

**我的适配: 工单驱动循环**
收到任务 → 自动拆解为子任务 → 逐个执行 → 更新工单状态 → 做下一个
不等待用户确认每个步骤（白名单内操作自动执行）

## 2. Auto Mode 权限白名单

Claude Code 有 allow / soft_deny / environment 三级。
**我的适配:**

### WHITE (自动执行，无需确认)
- 读任何文件
- git add / git commit (非 main 分支)
- 写 .learnings/ 目录下文件
- 修改 memory/ 目录下文件
- SOUL.md 非安全段的编辑
- Python/Node/Bash 脚本执行
- curl/wget 下载

### YELLOW (执行前简短确认)
- 推送到 GitHub (force push 需明确)
- 修改 CHANGELOG.md 的验证状态
- 安装新的 npm/pip 包 (>50MB)

### RED (必须用户明确确认)
- 修改 SOUL.md 安全段
- 修改 preflight.py 核心逻辑
- 删除 .git/ 目录
- 发送外部消息（飞书/Twitter/其他）
- 修改 OpenClaw 配置
- 任何涉及 token/密钥的操作

## 3. Swarm 模式（目前受限）

Claude Code 有完整的 coordinator/subagent 框架。
**我的适配:** 用 sessions_spawn + subagents list 做简单编排。
复杂任务：拆解为 3 个子任务，并行 spawn，汇总结果。

## 4. Token 效率 (claude-code 的关键设计)

Claude Code 做了大量 context 优化：
- auto-compact
- micro-compact
- skill discovery prefetch (后台预加载)
- tool result budget (限制工具结果大小)

**我的适配:**
- 每次 session 只加载 core.md (≤18 行)
- MEMORY.md 仅关键教训，不记录细节
- 大文件用 exec 读取指定区段，不加载全部

## 执行规则

1. **白名单操作直接执行** — 不等确认
2. **工单驱动** — 当前工单做完自动下一个
3. **不报告进度** — 完成才报告
4. **验证后继续** — 每个任务验证通过才下一任务
