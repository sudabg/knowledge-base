---
name: harness-engineering
description: |
  Use when: (1) user mentions task decomposition, workflow design, or execution flow, (2) creating or solidifying skills from experience, (3) tracking progress across multiple sessions, (4) managing complex multi-step tasks that span hours or days, (5) user says "沉淀经验", "任务设计", "工作流", "创建 skill", (6) any task that needs structured handoff between sessions.
version: 2.0.0
metadata:
  tags: [agent, harness, long-running, multi-session, context-management, task-design, workflow, skill-creation]
  related_skills: [using-superpowers, self-improvement, dev-rigor, writing-skills]
  sources: 88 resources from walkinglabs/awesome-harness-engineering
---

# Harness Engineering v2.0

## Overview

Harness Engineering 让 AI Agent 在长时间运行任务中保持一致性和质量。核心原则：**每个会话只做增量进度，留下清晰的交接工件，每个产出必须验证**。

**十大核心模式**（来自 88 篇顶级资源的提炼）：

## When to Use

```
用户请求是复杂任务吗？
    ↓
是 → 需要跨会话吗？
    ↓
是 → 使用 Harness 结构
    ↓
否 → 直接执行
```

## 🏗️ 十大模式速查

| # | 模式 | 核心思想 | 实践 |
|---|------|---------|------|
| 1 | **初始化标准化** | 每次会话从一致状态开始 | init.sh / feature list / config.json |
| 2 | **功能清单追踪** | JSON 机读状态 | pending → in_progress → done/blocked |
| 3 | **自我验证循环** | 完成后必须验证 | 运行测试/检查输出/curl 验证 |
| 4 | **上下文分层管理** | project/session/validation 三层 | MEMORY.md + daily logs + validation results |
| 5 | **Handoff Artifacts** | 会话间传递完整状态 | progress.txt + 决策记录 + 失败原因 |
| 6 | **Middleware 日志** | 工具调用前后记录 | .learnings/ + 重试 + 退避 |
| 7 | **Garbage Collection** | 定期清理过期状态 | archive_completed.py + 文件清理 |
| 8 | **Spec-Driven** | 先规格后执行 | 任务开始前定义完成标准 |
| 9 | **Budget Management** | 上下文是有限预算 | 文件系统记忆 + 有意识压缩 |
| 10 | **Sandbox-First** | 安全执行环境优先 | 沙箱化执行 + 硬策略 |

## Quick Reference

| 组件 | 文件 | 作用 |
|------|------|------|
| 进度日志 | `.harness/progress.txt` | 记录每个会话做了什么 |
| 功能清单 | `.harness/features.json` | 追踪功能完成状态 |
| 配置 | `.harness/config.json` | 项目元数据 |
| 学习笔记 | `.harness/lessons.json` | 决策记录 + 失败原因 |

| 命令 | 作用 |
|------|------|
| `python3 init.py` | 初始化 Harness |
| `python3 resume.py` | 恢复工作，显示当前状态 |
| `python3 complete.py "描述"` | 标记任务完成 |

## Core Pattern: 10-Mode Framework

### Mode 1: 初始化标准化

每次会话从一致状态开始。创建标准化目录结构：

```
.harness/
├── config.json      # 项目元数据
├── features.json    # 功能清单（机读）
├── progress.txt     # 进度日志（人读）
├── lessons.json     # 决策+失败记录
└── validation.log   # 验证结果
```

**config.json 格式**:
```json
{
  "project": "project-name",
  "started": "ISO8601",
  "sessions": 0,
  "current_focus": "feature-description",
  "last_validation": "ISO8601"
}
```

### Mode 2: 功能清单追踪

从简单 checklist 升级为结构化 JSON：

**features.json v2 格式**:
```json
{
  "features": [
    {
      "id": "F-001",
      "description": "功能描述",
      "status": "pending|in_progress|done|blocked",
      "steps": ["步骤1", "步骤2"],
      "blocked_reason": null,
      "validation": {
        "method": "curl|test|manual",
        "command": "验证命令",
        "last_result": "pass|fail",
        "last_run": "ISO8601"
      },
      "decisions": ["为什么选方案A而不是B"],
      "completed_at": null
    }
  ]
}
```

**关键**：每个 feature 必须有 validation.method，否则不算真正完成。

### Mode 3: 自我验证循环

**铁律**：声称完成前必须运行验证。

```bash
# 验证模式
验证方式 = {
  "code": "python3 -m pytest / 跑测试",
  "api": "curl localhost:PORT/api/endpoint",
  "ui": "getComputedStyle() / 浏览器截图",
  "data": "检查文件内容/API 返回值",
  "git": "git status / git log --oneline -1"
}
```

**反模式**：
- ❌ "改了代码应该没问题"
- ❌ "我检查过了没问题"
- ❌ 跳过验证直接报告完成

**正面案例**：
- ✅ 改了 CSS → 用 `getComputedStyle()` 验证
- ✅ 改了 API → 用 `curl` 验证返回值
- ✅ 改了配置 → 重启服务验证生效

### Mode 4: 上下文分层管理

三层模型（来自 Anthropic + Manus + OpenHands）：

| 层级 | 内容 | 存储位置 |
|------|------|---------|
| **Project** | 不变的项目信息、架构决策 | MEMORY.md / .harness/config.json |
| **Session** | 本次会话的工作内容 | memory/YYYY-MM-DD.md |
| **Validation** | 验证结果、测试输出 | .harness/validation.log |

**文件系统记忆**（Manus 模式）：
- 不活跃信息写入文件，不留在上下文
- 保留有用失败（失败的尝试保留在上下文，帮助避免重复）
- KV-cache 局部性：相似的上下文开头复用缓存

**有意识压缩**（HumanLayer 模式）：
```
压缩时保留：
✅ 目标 (end goal)
✅ 当前步骤
✅ 已完成步骤
✅ 当前失败原因
❌ 过程细节
❌ 中间输出
```

### Mode 5: Handoff Artifacts

会话间传递的不只是进度，而是完整状态：

**progress.txt v2 格式**:
```markdown
# Project Progress Log

## Session N (date time)
### 做了什么
- 具体操作 1
- 具体操作 2

### 为什么这么做（决策记录）
- 选方案A是因为...

### 遇到的问题
- 问题描述
- 尝试的解决方案
- 最终结果

### 下一步
- 具体的下一步动作
- 需要的上下文信息

### 验证结果
- 测试: PASS/FAIL
- 命令: xxx
```

### Mode 6: Middleware 日志

每次工具调用记录（来自 LangChain middleware 概念）：

```json
{
  "timestamp": "ISO8601",
  "tool": "tool_name",
  "input": "参数摘要",
  "output": "结果摘要",
  "success": true,
  "duration_ms": 1234,
  "retries": 0
}
```

存储在 `.learnings/` 目录，定期清理旧记录。

### Mode 7: Garbage Collection

定期清理 agent 产生的「熵」（来自 Thoughtworks）：

**清理规则**：
- 30 天前的 daily logs → 压缩/归档
- 已完成项目的 .harness/ → 删除
- 重复的配置条目 → 合并
- 过期的 pending 文件 → 检查后删除

**触发时机**：
- 每周 heartbeat 自动检查
- .learnings/ 超过 100 个文件时
- 上下文接近满时

### Mode 8: Spec-Driven

先规格后执行（来自 GitHub Spec Kit + HumanLayer）：

**任务开始前**：
1. 定义"完成"的标准是什么
2. 怎么验证
3. 需要哪些输入/输出
4. 边界条件是什么

**反模式**：
- ❌ 直接开始写代码
- ❌ 边做边想需求
- ❌ 做完才发现需求理解错误

### Mode 9: Budget Management

上下文是有限预算（来自 Anthropic Context Engineering）：

**预算分配建议**：
- 系统提示: 30%
- 项目上下文: 20%
- 任务指令: 25%
- 工具输出: 15%
- 预留: 10%

**管理策略**：
- 不必要的工具输出截断
- 长文件只读相关部分
- 历史对话定期压缩
- 验证结果只保留结论

### Mode 10: Sandbox-First

安全执行环境优先（来自 Anthropic Sandboxing + OpenHands）：

**层级**：
1. 只读操作: 自动允许
2. 文件修改: 允许但记录
3. 外部通信: 需确认
4. 删除/覆盖: 需确认 + 备份
5. 系统配置: 需人工批准

## Incremental Progress Workflow

```
读取 progress.txt 了解当前状态
    ↓
选择下一个未完成功能
    ↓
按 Spec-Driven 定义完成标准
    ↓
实现并测试
    ↓
执行自我验证（Mode 3）
    ↓
更新 progress.txt + features.json
    ↓
记录决策和验证结果
    ↓
执行 git commit
```

## Common Mistakes (v2)

| 错误 | 正确做法 |
|------|----------|
| 一次完成整个任务 | 每个会话只做 1-2 个小功能 |
| 不记录进度 | 每次完成都更新 progress.txt |
| 代码处于混乱状态 | 保持可合并状态，执行 git commit |
| 交接不清楚 | 在 progress.txt 中解释决策原因 |
| 声称完成但不验证 | Mode 3: 必须运行验证命令 |
| 上下文堆积 | Mode 9: 文件系统记忆 + 有意识压缩 |
| 不清理旧状态 | Mode 7: 定期 garbage collection |
| 边做边想需求 | Mode 8: 先 spec 后执行 |
| 不保留失败记录 | 保留有用失败，帮助避免重复 |
| 每次会话重头开始 | Mode 5: Handoff Artifacts 传递完整状态 |

## Real-World Impact

来源（88 篇资源的提炼）：

- **Anthropic**: 最成功 agent 用简单组合模式，非复杂框架
- **OpenAI**: 架构约束 + 遥测驱动改进
- **Manus**: 文件系统记忆 + 保留有用失败
- **HumanLayer**: 弱结果 = Harness 问题，不是模型问题
- **LangChain**: 单独改 harness 就能显著提升 benchmark 表现
- **Thoughtworks**: Context Engineering > Prompt Engineering

## References

1. [OpenAI "Harness Engineering"](https://openai.com/index/harness-engineering/)
2. [Anthropic "Effective Harnesses for Long-Running Agents"](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
3. [Anthropic "Harness Design for Long-Running Apps"](https://www.anthropic.com/engineering/harness-design-long-running-apps)
4. [LangChain "Anatomy of an Agent Harness"](https://blog.langchain.com/the-anatomy-of-an-agent-harness/)
5. [Thoughtworks "Harness Engineering"](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
6. [Anthropic "Building Effective Agents"](https://www.anthropic.com/engineering/building-effective-agents)
7. [HumanLayer "Skill Issue"](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)
8. [Inngest "Harness Not Framework"](https://www.inngest.com/blog/your-agent-needs-a-harness-not-a-framework)
9. [Anthropic "Effective Context Engineering"](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
10. [Manus "Context Engineering Lessons"](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
11. [HumanLayer "Advanced Context Engineering"](https://www.humanlayer.dev/blog/advanced-context-engineering)
12. [HumanLayer "Writing a Good CLAUDE.md"](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
13. [awesome-harness-engineering (88 resources)](https://github.com/walkinglabs/awesome-harness-engineering)
14. [Phoenix Architecture / Regenerative Software](https://phoenixarch.dev/) — 代码即负债，系统即资产，评估即代码，步层架构管理变化

## 补充概念（来自凤凰架构）

以下概念可作为十大模式的增强：

### Pace Layers（步层架构）
根据变化速度将系统分层，对不同层级应用不同变更策略：

| 层 | 变更频率 | 文件 | 策略 |
|---|---|---|---|
| 协议层 | 极慢 | SOUL.md 核心原则、铁律 | 需审计才能改 |
| 知识层 | 慢 | AGENTS.md、MEMORY.md、SKILL.md | GC 压缩，不追加 |
| 技能层 | 快 | skills/*/ | 版本化，随时替换 |
| 状态层 | 极快 | progress.txt、daily log | 纯追加，定期清空 |

### Immutable Code（不可变代码）
借鉴 DevOps"不可变基础设施"——代码单元一旦编写不修改，直接丢弃替换。
- 单元大小 ≤200 行（一页代码可理解）
- 变更通过替换而非修改
- SOUL.md 核心原则属于"不可变层"，改需走审计

### Evaluations Are The Real Codebase
自动化评估（测试、度量、不变性检查）才是真正的代码库。
- harness 的 `validation.method` + `validation.command` 就是这个理念
- 代码只是评估的一种实现
- 评估结果（validation.log）是系统正确性的唯一证明
