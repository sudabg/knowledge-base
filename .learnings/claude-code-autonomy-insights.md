# Claude Code 自主性分析

## 核心机制

### 1. 自主 Agent 循环 (while(true) loop)
claude-code 的 query.ts 有一个 `while (true)` 循环。收到用户指令后不是回应一次就停，而是：
1. 调用 API 生成回复
2. 检查是否调用了工具（tool_use）
3. 执行工具，收集结果
4. 继续循环，直到没有更多工具调用

**我的差距**: 收到消息→回复→结束。claude-code 收到消息→回复→执行→再继续→直到任务完成。**我缺少"自我继续"的机制。**

### 2. Auto Mode (permission-less execution)
- `src/utils/permissions/yoloClassifier.ts` — AI 分类器判断哪些操作需要用户确认
- `src/cli/handlers/autoMode.ts` — allow / soft_deny / environment 三层权限规则
- 用户写规则，分类器自动判断，不需要每次都问

**我的差距**: 我每个命令都要问"可以吗？"。claude-code 有 allow/soft_deny 分层，白名单内的操作直接执行。

### 3. 后台任务系统 (LocalMainSessionTask)
- session 后台化 → query 继续执行 → 完成时通知用户
- 用户可以前台看，也可以后台跑，完全自主

**我的差距**: 我无法异步执行长时间任务。用户离开=任务停止。

### 4. 技能系统 (skills/)
- `src/skills/bundled/` — 捆绑技能
- `src/skills/mcpSkillBuilders.ts` — MCP 技能构建器
- 技能目录动态发现，无需用户手动指定

**和我的相似处**: 我的 skills/ 目录也是技能动态发现，这方面架构一致。

### 5. Coordinator Mode (多 Agent 编排)
- `feature('COORDINATOR_MODE')` — 多 Agent 协作
- `src/coordinator/coordinatorMode.ts` — 主 Agent 分配任务给子 Agent
- 子 Agent 独立执行，结果汇报

**我的差距**: 我有 subagent 但不自动编排。claude-code 有完整的任务分配框架。

## 可立即适配的部分

1. **自主循环**: 不需要代码，只需要行为改变——收到任务→做完→汇报，不等用户催
2. **权限分层**: 在 SOUL.md 定义白名单操作（git commit/文件读取/内存整理），直接执行
3. **工单驱动**: 工单#002 完成后自动挑下一个，不等待

## 架构级差距（当前环境无法做到）
- 后台异步执行（需要独立运行时）
- 多 Agent 编排调度（需要 coordinator 框架）
- 权限自动分级（需要 AI 分类器服务）
