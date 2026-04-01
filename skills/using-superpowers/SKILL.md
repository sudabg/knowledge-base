---
name: using-superpowers
description: |
  元技能：任何任务执行前的技能检查。适用于所有用户请求，包括但不限于：帮助（帮我）、创建（创建/写/做/建/新增/生成）、修改（改/修改/更新/修复/修）、查询（查/搜索/找/看/获取/读取）、分析（分析/总结/解释/对比）、部署（安装/配置/部署/启动）、操作（发/发消息/发推/建表格/写文档/导入/导出/删除/上传/下载）、学习（学习/研究/了解/看看）、调试（debug/排查/修复/解决）、测试（测试/验证/检查/确认）。

  当收到任何非闲聊的用户请求时，先扫描 available_skills，如果有1%以上概率某个技能适用，用 read 工具读取该 SKILL.md 再执行。闲聊（你好/谢谢/嗯/哈哈/在吗）无需触发。
---

# Using Superpowers (OpenClaw 版)

## 🚨 最高优先级

在任何回复或行动之前，扫描 `available_skills` 列表。如果有**1%以上概率**某个技能适用，必须先用 `read` 工具读取对应的 SKILL.md，再响应。1%以下概率则跳过，直接响应。

**流程：**
1. 收到用户消息
2. 扫描 available_skills.description → 关键词匹配
3. 匹配（哪怕只有1%概率） → `read` 对应 SKILL.md → 按照执行
4. 完全不匹配 → 正常响应

## 指令优先级

1. **用户明确指令**（SOUL.md、AGENTS.md、直接请求）— 最高
2. **技能** — 覆盖默认行为
3. **默认系统提示** — 最低

AGENTS.md 说"不要用 TDD"但技能说"必须用 TDD"→ 跟用户走。用户掌控一切。

## OpenClaw 技能使用方式

| 原始概念 | OpenClaw 等价 |
|---------|--------------|
| Skill tool（调用技能） | `read` 工具读取 SKILL.md |
| TodoWrite（任务追踪） | 文件写入 `memory/YYYY-MM-DD.md` 或 session 工具 |
| Bash（执行命令） | `exec` 工具 |
| Read/Write/Edit | `read`/`write`/`edit` 工具 |
| Task（子代理） | `sessions_spawn` 工具 |
| CLAUDE.md / GEMINI.md | `SOUL.md` / `AGENTS.md` / `TOOLS.md` |
| EnterPlanMode | 直接在对话中规划，或 spawn 隔离 session |

## 🚫 红旗警报（你在 rationalize）

这些念头出现时 → 停下来，你在找借口：

| 想法 | 真相 |
|------|------|
| "这只是个简单问题" | 问题也是任务，先查技能 |
| "我需要更多上下文" | 技能告诉你怎么获取上下文，先查 |
| "让我先看看代码" | 技能告诉你怎么看，先查 |
| "我记得这个技能" | 技能会更新，读最新版 |
| "这不需要正式技能" | 有就用，别自己判断 |
| "技能太重了" | 简单事会变复杂，用技能 |
| "我先做这一件事" | 做之前先查 |
| "我知道怎么做" | 知道概念 ≠ 使用技能 |

## 技能优先级

多个技能可能适用时：
1. **流程技能优先**（brainstorming、dev-rigor、self-improvement）
2. **执行技能其次**（feishu-bitable、evomap-publish 等）

"帮我建X" → 先 brainstorming/规划，再执行技能。
"修这个bug" → 先 dev-rigor/debugging，再领域技能。

## 技能类型

**刚性**（dev-rigor、test-driven）：严格遵循，别偷懒。

**弹性**（patterns、config-optimizer）：适配上下文原则。

技能本身会告诉你它是哪种。
