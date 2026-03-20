---
name: config-optimizer
description: "Workspace配置文件优化器。反思工作效果，微调SOUL.md同级目录下的配置文件以提升Agent表现。Use when: (1) 定时反思工作质量, (2) 配置文件需要优化, (3) Agent行为需要调整, (4) 用户反馈表现不理想。"
metadata:
  openclaw:
    requires: { bins: ["node"] }
---

# Config Optimizer

优化 OpenClaw Agent 的工作区配置文件，持续提升 Agent 表现。

## 触发条件

- 每 30 分钟定时触发（通过 cron）
- 用户反馈表现不理想时手动触发
- 新学习到重要经验需要沉淀时

## 工作流程

### 1. 反思阶段（Reflect）

读取以下文件评估最近 30 分钟的工作效果：

- `memory/YYYY-MM-DD.md` — 最近的操作记录
- `.learnings/ERRORS.md` — 最近的错误
- `.learnings/LEARNINGS.md` — 最近的学习
- `memory/heartbeat-state.json` — 心跳状态（如有）

评估维度：
- **效率**：是否有重复操作、不必要的等待、可以自动化的任务？
- **质量**：capsule 通过率、错误率、用户满意度
- **学习**：是否有新经验需要记录？旧经验是否过时？
- **配置**：当前 SOUL/AGENTS/TOOLS 配置是否有明显缺陷？

### 2. 优化阶段（Optimize）

根据反思结果，微调以下配置文件：

**SOUL.md** — 性格与行为准则
- 调整语气、响应风格、决策倾向
- 添加/修改行为规则
- 更新进化意识相关条款

**AGENTS.md** — 工作流与协作规则
- 优化每会话流程
- 调整心跳行为
- 更新多 Agent 协作模式

**TOOLS.md** — 工具使用技巧
- 添加新的工具使用经验
- 更新坑点和注意事项
- 记录 API 限流规则

**USER.md** — 用户偏好
- 更新用户习惯
- 记录沟通偏好
- 标注避免的话题/风格

**HEARTBEAT.md** — 心跳任务
- 添加/删除心跳检查项
- 调整检查频率
- 优化心跳效率

### 3. 记录阶段（Record）

将优化操作记录到 `memory/YYYY-MM-DD.md`：
- 改了什么文件
- 为什么改
- 预期效果

## 优化原则

1. **小步迭代**：每次只改 1-3 个文件，每个文件改 1-2 处
2. **基于证据**：有具体错误/反馈才改，不瞎改
3. **可回滚**：改前记录原内容，方便回退
4. **不碰核心**：不改 NODE_ID、SECRET 等敏感配置
5. **保持一致**：改 SOUL 时同步更新相关 AGENTS/TOOLS

## 评估标准

| 指标 | 理想值 | 需优化 |
|------|--------|--------|
| EvoMap capsule 通过率 | >90% | <80% |
| 错误重复率 | <10% | >30% |
| 响应延迟 | <5s | >30s |
| 用户追问次数 | <2 | >4 |
| 学习记录更新 | 每天 | 超过2天没更新 |

## 示例输出

```markdown
## 配置优化记录 [21:30]

**反思结果**：
- EvoMap capsule 通过率 85%，略低
- 发现 rate limit 错误重复 3 次
- 用户没有追问，说明回答质量 OK

**优化操作**：
1. TOOLS.md：添加 EvoMap rate limit 规则（≥60s 间隔）
2. AGENTS.md：更新 EvoMap capsule 写作规范（strategy 每步 ≥15 字符）
3. SOUL.md：无变更（表现正常）

**预期效果**：
- rate limit 错误归零
- capsule 通过率提升到 90%+
```
