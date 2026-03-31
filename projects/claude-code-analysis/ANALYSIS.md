# Claude Code 源码结构分析

## 仓库信息
- **主仓库**: instructkr/claude-code (13.6K⭐, 20.4K fork, MIT)
- **镜像源**: g1thubX/claude-code (0⭐, 新 fork)
- **泄露背景**: 2026-03-31, npm source map 暴露
- **规模**: ~1900+ TypeScript 源文件
- **分支**: main (已重写为 Python 3 版本)

## 核心架构

### 1. Tool 系统 (src/tools/)
设计模式: ABC + registry 装饰器注册

```typescript
// 伪代码
abstract class Tool {
  name: string
  inputSchema: JSONSchema
  async execute(params): Promise<ToolResult>
}

@tool("bash")
class BashTool extends Tool { ... }
```

内置工具分类:
- **文件操作**: `FileReadTool`, `FileWriteTool`, `GlobTool`, `GrepTool`
- **任务管理**: `TaskCreateTool`, `TaskGetTool`, `TaskUpdateTool`, `TaskStopTool`
- **Agent 系统**: `AgentTool`, `TeamCreateTool`, `TeamDeleteTool`
- **服务集成**: `WebSearchTool`, `MCPTool`, `McpAuthTool`
- **辅助工具**: `BriefTool`, `SleepTool`, `ScheduleCronTool`, `SendMessageTool`

### 2. QueryEngine (src/query_engine.py)
- 工具选择: 语义匹配 + 参数推断
- 上下文窗口: sliding window + LRU 缓存
- 失败恢复: 重试 +备选工具

### 3. 技能系统 (src/skills/)
- `coordinatorMode.ts` — 技能编排
- `bundledSkills.ts` — 内置技能包
- `loadSkillsDir.ts` — 动态加载外部技能

### 4. 会话管理 (src/)
- `sessionHistory.ts` — 持久化历史
- `context/` — 上下文构建
- `stats.tsx` — 会话统计

### 5. 服务层 (src/services/)
- `api/claude.ts` — API 封装
- `mcp/` — MCP 服务器连接
- `tokenEstimation.ts` — token 计数

## OpenClaw vs Claude Code 对比

| 能力维度 | Claude Code | OpenClaw |
|---|---|---|
| 安全隔离 | sandbox 执行 | 规则引擎 + 沙箱 |
| 工具生态 | 40+ 轻量工具 | 飞书集成 + 自定义 |
| 知识管理 | 会话历史即记忆 | ✅ Skill Bank + EvoMap |
| 长期记忆 | ❌ 无 | ✅ 分层压缩记忆 |
| 评估机制 | QA 循环 | ✅ 独立评估者 (Mode 11) |
| 知识图谱 | ❌ 无 | ✅ EvoMap 进化市场 |
| 技能复用 | 简单注册 | ✅ 双粒度 (task+step) |

## OpenClaw 已超越点

1. **知识图谱** - EvoMap 闭环进化
2. **技能库** - D2Skill 双粒度设计
3. **记忆压缩** - 跨会话记忆管理
4. **质量验证** - Harness Engineering 14 模式

## 可借鉴之处

1. **Artifact 作为一级公民**
   - Claude Code 把产物(artifact)抽象为服务
   - OpenClaw 可考虑：`services/artifact.py`

2. **Context 滑动窗口策略**
   - 重要性权重 + LRU
   - 可改进记忆压缩算法

3. **服务解耦**
   - Dashboard/Refresh 独立服务
   - OpenClaw 已有的 `dashboard/` 可参考扩展

## 局限

- 无长期进化机制（OpenClaw 已领先）
- 知识图谱能力缺失
- 技能系统较简单

## 结论

Claude Code 胜在简洁专注，OpenClaw 已完成知识管理/记忆/进化能力超越。

下一步: 考虑引入 artifact 服务化设计 + context 滑动窗口优化。
