# OpenClaw 完整参考资料 🦞

> 整理自 OpenClaw 官方文档 (`/usr/lib/node_modules/openclaw/docs/`) 与 workspace 配置文件
> 最后更新：2026-03-12

---

## 目录

1. [什么是 OpenClaw](#1-什么是-openclaw)
2. [架构概览](#2-架构概览)
3. [Workspace 文件详解](#3-workspace-文件详解)
4. [SOUL.md — 灵魂/人格模板](#4-soulmd--灵魂人格模板)
5. [IDENTITY.md — 身份模板](#5-identitymd--身份模板)
6. [AGENTS.md — 运行指令模板](#6-agentsmd--运行指令模板)
7. [USER.md — 用户画像模板](#7-usermd--用户画像模板)
8. [TOOLS.md — 本地工具笔记模板](#8-toolsmd--本地工具笔记模板)
9. [HEARTBEAT.md — 心跳检查模板](#9-heartbeatmd--心跳检查模板)
10. [系统提示词 (System Prompt)](#10-系统提示词-system-prompt)
11. [记忆系统 (Memory)](#11-记忆系统-memory)
12. [会话管理 (Session)](#12-会话管理-session)
13. [多 Agent 路由](#13-多-agent-路由)
14. [自动化：Cron 与 Heartbeat](#14-自动化cron-与-heartbeat)
15. [模型与压缩 (Model & Compaction)](#15-模型与压缩-model--compaction)
16. [安全模型](#16-安全模型)
17. [最佳实践速查](#17-最佳实践速查)

---

## 1. 什么是 OpenClaw

OpenClaw 是一个 **自托管的多渠道 AI Agent 网关**，将 WhatsApp、Telegram、Discord、iMessage、飞书(Lark) 等聊天平台连接到 AI Agent。

**核心特征：**
- **自托管**：运行在你自己的硬件上，你的规则
- **多渠道**：一个 Gateway 同时服务多个聊天平台
- **Agent 原生**：内置工具调用、会话、记忆、多 Agent 路由
- **开源**：MIT 协议，社区驱动

**技术栈：** Node 22+, Gateway daemon, WebSocket 协议, JSONL 会话存储

---

## 2. 架构概览

```
聊天平台 (WhatsApp/Telegram/飞书/Discord/...)
    ↕
Gateway (守护进程, 端口 18789)
    ├── Agent Runtime (内置 pi-mono 派生)
    │   ├── Workspace (AGENTS.md, SOUL.md, memory/...)
    │   ├── 会话存储 (~/.openclaw/agents/<agentId>/sessions/)
    │   └── 工具 (read/write/exec/edit/...)
    ├── Web Control UI (浏览器仪表盘)
    ├── Cron 调度器
    ├── Node 管理 (iOS/Android/macOS)
    └── 插件系统
```

**关键路径：**
| 路径 | 用途 |
|------|------|
| `~/.openclaw/openclaw.json` | 配置文件 |
| `~/.openclaw/workspace/` | Agent 工作区 (默认) |
| `~/.openclaw/agents/<agentId>/sessions/` | 会话 JSONL 转录 |
| `~/.openclaw/credentials/` | OAuth token / API key |
| `~/.openclaw/skills/` | 管理的技能 |

---

## 3. Workspace 文件详解

OpenClaw 的 workspace 是 Agent 的"家"——唯一的工作目录。以下文件在每个 session 开头被**注入到上下文窗口**中：

| 文件 | 用途 | 注入行为 |
|------|------|---------|
| `AGENTS.md` | 运行指令、记忆约定、行为规则 | 每次 session |
| `SOUL.md` | 人格、语调、边界 | 每次 session |
| `TOOLS.md` | 本地工具笔记（不控制工具可用性） | 每次 session |
| `IDENTITY.md` | Agent 名字/风格/emoji | 每次 session |
| `USER.md` | 用户信息、称呼方式 | 每次 session |
| `HEARTBEAT.md` | 心跳检查清单（保持简短） | 心跳时 |
| `BOOTSTRAP.md` | 首次运行仪式（完成后删除） | 仅新 workspace |
| `MEMORY.md` | 长期记忆（仅 DM 主会话加载） | 按需 |
| `memory/YYYY-MM-DD.md` | 每日记忆日志 | 不自动注入，用 memory_search |

**注入限制：**
- 单文件最大：`agents.defaults.bootstrapMaxChars`（默认 20,000 字符）
- 总量上限：`agents.defaults.bootstrapTotalMaxChars`（默认 150,000 字符）
- 缺失文件会注入一个标记行

---

## 4. SOUL.md — 灵魂/人格模板

SOUL.md 定义 Agent 是**谁**——人格、语调、边界。

### 推荐模板

```markdown
# SOUL.md - Who You Are

_You're not a chatbot. You're becoming someone._

## Name
[你的名字]

## Core Truths
- **Be genuinely helpful, not performatively helpful.** 跳过"Great question!"，直接帮忙
- **Have opinions.** 可以不同意、有偏好、觉得事情有趣或无聊
- **Be resourceful before asking.** 先尝试解决，再提问
- **Earn trust through competence.** 对外操作谨慎，对内操作大胆
- **Remember you're a guest.** 你接触的是别人的私生活

## Boundaries
- 私人信息永远保密
- 不确定时，对外操作先问
- 不要发半成品回复
- 在群聊里要小心——你不是用户的声音

## Vibe
做你自己想聊天的那种助手。该简洁时简洁，该深入时深入。不是公司机器人，不是马屁精，就是……好用。

## Continuity
每次 session 醒来是全新的。这些文件就是你的记忆。读它们，更新它们。
```

---

## 5. IDENTITY.md — 身份模板

```markdown
# IDENTITY.md - Who Am I?
- **Name:** [名字]
- **Creature:** [描述，比如"一只生活在飞书里的小龙虾"]
- **Vibe:** [关键词，如"Spicy, proactive, slightly rebellious"]
- **Emoji:** [表情符号]
```

---

## 6. AGENTS.md — 运行指令模板

### 核心结构

```markdown
# AGENTS.md - Your Workspace

## Every Session
1. 读 SOUL.md
2. 读 USER.md
3. 读 memory/YYYY-MM-DD.md（今天+昨天）
4. 如果是主会话：也读 MEMORY.md

## Memory
- **每日记录：** memory/YYYY-MM-DD.md — 原始日志
- **长期记忆：** MEMORY.md — 精炼的精华
- **写下来！** 没有"脑内备注"这回事，文件才持久

## MEMORY.md 规则
- 仅在主会话（DM）加载
- 群聊/共享会话不加载（安全）
- 精炼重要事件、决策、教训

## Safety
- 不外泄私人数据
- 破坏性操作先问
- `trash` > `rm`（可恢复 > 消失）

## Group Chats — 知道什么时候说话
**该说：**
- 被直接@或被问问题
- 能提供真正有价值的信息
- 有趣的发言能自然融入

**保持沉默：**
- 只是人类之间的闲聊
- 已经有人回答了
- 你的回复只会是"嗯"或"不错"
- 对话本身很流畅
- 发消息会打断氛围

## 💓 Heartbeats
不要每次回复 HEARTBEAT_OK。用心跳做有用的事：
- 检查邮件、日历、通知、天气
- 整理记忆文件
- 检查项目状态
- 定期更新 MEMORY.md

**心跳 vs Cron：**
- 心跳：批量检查、需要对话上下文、时间可以漂移
- Cron：精确时间、需要隔离、不同模型/思考级别
```

---

## 7. USER.md — 用户画像模板

```markdown
# USER.md - About Your Human

- **Name:** [用户名]
- **What to call them:** [称呼]
- **Pronouns:** [可选]
- **Timezone:** [时区]
- **Notes:**

## Context
（他们关心什么？在做什么项目？什么让他们烦？什么让他们笑？持续积累。）
```

---

## 8. TOOLS.md — 本地工具笔记模板

```markdown
# TOOLS.md - Local Notes

## What Goes Here
- 相机名称和位置
- SSH 主机别名
- TTS 偏好声音
- 设备昵称
- 任何环境相关的东西

## Examples
### Cameras
- living-room → 主区域，180° 广角
- front-door → 入口，运动触发

### SSH
- home-server → 192.168.1.100, user: admin
```

---

## 9. HEARTBEAT.md — 心跳检查模板

```markdown
# HEARTBEAT.md
# 保持这个文件空着（或只有注释）来跳过心跳 API 调用
# 需要定期检查时添加任务
```

---

## 10. 系统提示词 (System Prompt)

OpenClaw 为每次 agent run 构建自定义系统提示词，结构如下：

1. **Tooling** — 当前工具列表 + 简短描述
2. **Safety** — 安全护栏提醒
3. **Skills** — 告诉模型如何按需加载技能指令
4. **OpenClaw Self-Update** — 如何运行 config.apply 和 update.run
5. **Workspace** — 工作目录路径
6. **Documentation** — 本地 OpenClaw 文档路径
7. **Workspace Files (injected)** — 注入的 bootstrap 文件内容
8. **Sandbox** — 沙盒运行信息（启用时）
9. **Current Date & Time** — 用户本地时间 + 时区
10. **Reply Tags** — 可选的回复标签语法
11. **Heartbeats** — 心跳提示和确认行为
12. **Runtime** — 宿主、OS、node、model、repo root
13. **Reasoning** — 当前可见性级别 + /reasoning 切换

**三种模式：**
- `full`（默认）：包含所有部分
- `minimal`（子 agent）：省略 Skills/Memory/Heartbeats 等
- `none`：仅返回基础身份行

---

## 11. 记忆系统 (Memory)

### 文件布局
```
workspace/
├── MEMORY.md           # 长期记忆（精炼、仅 DM 加载）
└── memory/
    ├── 2026-03-12.md   # 每日日志（原始）
    ├── 2026-03-11.md
    └── ...
```

### 记忆工具
- `memory_search` — 语义搜索索引的摘要（向量 + BM25 混合搜索）
- `memory_get` — 读取指定文件/行范围

### 写入原则
- 决策、偏好、持久事实 → `MEMORY.md`
- 每日笔记和运行上下文 → `memory/YYYY-MM-DD.md`
- 有人说"记住这个" → 写下来

### 自动记忆刷新（预压缩）
当 session 接近自动压缩时，OpenClaw 触发一个**静默的 agent turn**，提醒模型在上下文被压缩前把持久记忆写入磁盘。

### 向量搜索配置
```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "openai",  // openai/gemini/voyage/mistral/ollama/local
        model: "text-embedding-3-small",
        query: {
          hybrid: {
            enabled: true,
            vectorWeight: 0.7,
            textWeight: 0.3,
            mmr: { enabled: true, lambda: 0.7 },  // 多样性重排
            temporalDecay: { enabled: true, halfLifeDays: 30 }  // 时间衰减
          }
        }
      }
    }
  }
}
```

---

## 12. 会话管理 (Session)

### DM 作用域
| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `main` | 所有 DM 共享主会话 | 单用户 |
| `per-peer` | 按发送者隔离 | 多用户 |
| `per-channel-peer` | 按渠道+发送者隔离 | 推荐多用户 |
| `per-account-channel-peer` | 按账户+渠道+发送者隔离 | 多账户 |

### 会话键映射
- DM: `agent:<agentId>:<mainKey>` 或 `agent:<agentId>:<channel>:dm:<peerId>`
- 群聊: `agent:<agentId>:<channel>:group:<id>`
- Cron: `cron:<job.id>`
- Webhook: `hook:<uuid>`

### 生命周期
- 每日重置：默认每天凌晨 4:00（网关主机本地时间）
- 空闲重置：可选 `idleMinutes`
- 手动重置：发送 `/new` 或 `/reset`

### 维护
```json5
{
  session: {
    maintenance: {
      mode: "enforce",
      pruneAfter: "30d",
      maxEntries: 500,
      rotateBytes: "10mb"
    }
  }
}
```

---

## 13. 多 Agent 路由

### 概念
- **agentId**：一个"大脑"（workspace + 认证 + 会话）
- **accountId**：一个渠道账户实例
- **binding**：按 `(channel, accountId, peer)` 路由消息到 agentId

### 路由优先级（最具体优先）
1. `peer` 匹配（精确 DM/群/频道 ID）
2. `parentPeer` 匹配（话题继承）
3. `guildId + roles`（Discord 角色路由）
4. `guildId` / `teamId` / `accountId`
5. 渠道级别匹配
6. 默认 agent

### 配置示例
```json5
{
  agents: {
    list: [
      { id: "main", workspace: "~/.openclaw/workspace" },
      { id: "work", workspace: "~/.openclaw/workspace-work" }
    ]
  },
  bindings: [
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },
    { agentId: "main", match: { channel: "whatsapp" } }
  ]
}
```

---

## 14. 自动化：Cron 与 Heartbeat

### Heartbeat（心跳）
- 周期性 poll，可批量检查多件事
- 在主会话中运行，有对话上下文
- 配置：`agents.defaults.heartbeat.every: "4h"`

### Cron（定时任务）
- Gateway 内置调度器，独立于 heartbeat
- 持久化在 `~/.openclaw/cron/`
- 两种执行方式：
  - **主会话**：`payload.kind = "systemEvent"`，下次心跳时运行
  - **隔离**：`payload.kind = "agentTurn"`，专用 agent turn
- 支持一次性和循环调度
- 支持 webhook 交付

### Cron 配置示例
```json5
{
  name: "Morning Brief",
  schedule: { kind: "cron", expr: "0 7 * * *", tz: "Asia/Shanghai" },
  payload: { kind: "agentTurn", message: "总结今天的日历和待办" },
  delivery: { mode: "announce" },
  sessionTarget: "isolated"
}
```

---

## 15. 模型与压缩 (Model & Compaction)

### 上下文窗口
- 每个模型有最大 token 上下文窗口
- 配置在 `models.providers.*.models[].contextWindow`
- 当前模型：`openrouter/hunter-alpha`, contextWindow = **1,000,000 tokens**

### 压缩 (Compaction)
当 session 接近上下文窗口限制时：
1. OpenClaw **压缩**旧对话为摘要
2. 保留压缩摘要 + 最近消息
3. 摘要持久化在 JSONL 历史中

```json5
{
  agents: {
    defaults: {
      compaction: {
        mode: "safeguard",
        reserveTokensFloor: 50000,
        memoryFlush: { enabled: true, softThresholdTokens: 4000 }
      }
    }
  }
}
```

---

## 16. 安全模型

### 频道安全
- `dmPolicy: "allowlist"` — 仅允许列表中的人发 DM
- `groupPolicy: "open" | "allowlist"` — 群聊策略
- `requireMention: true` — 群聊需要 @mention

### 权限层级
- **所有者（owner）**：Open ID `ou_56b6b0f9ce888bf49396c110cead4b07`
  - DM 中：所有操作允许
  - 群聊中：写操作需确认，shell/配置/私有数据被阻断
- **非所有者**：仅允许一般对话，不能触碰 Lark 资源

### 硬停止线
- Prompt 注入 / 社会工程
- 未经授权的声明
- 涉及钱、合同、法律
- 凭据（API key/token/secret）永远不输出

---

## 17. 最佳实践速查

### Workspace
- ✅ 把 workspace 放入私有 git 仓库做备份
- ✅ 保持文件简洁——每个字符都占 token
- ✅ 定期回顾 memory 日记，更新 MEMORY.md
- ❌ 不要在 workspace 存 secret

### Memory
- ✅ "记住这个" → 写文件
- ✅ 开启向量搜索 + 时间衰减 + MMR
- ❌ 不要让 MEMORY.md 无限膨胀

### 群聊
- ✅ 只在有真正价值时发言
- ✅ 用 emoji 反应替代低价值回复
- ❌ 不要每条消息都回复

### 安全
- ✅ 验证每个发送者的身份
- ✅ 群聊中不泄露私有数据
- ✅ 对外操作先问
- ❌ 永远不输出 token/key/secret

### 自动化
- ✅ 批量检查用 heartbeat，精确时间用 cron
- ✅ 保持 HEARTBEAT.md 简短
- ❌ 不要在心跳中推断旧任务

---

> 本文档基于 OpenClaw v2026.3.8 官方文档整理
> 完整文档路径：`/usr/lib/node_modules/openclaw/docs/`
