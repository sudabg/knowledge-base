# arXiv Agent 论文精选 — 2026-03-25

> 本周 cs.AI 领域最新 Agent 相关论文，筛选 3 篇与我们工作最相关的。

---

## 1. MemCollab: Cross-Agent Memory Collaboration via Contrastive Trajectory Distillation

- **arXiv**: [2603.23234](https://arxiv.org/abs/2603.23234)
- **作者**: Yurui Chang, Yiran Wu, Qingyun Wu, Lu Lin
- **发表**: 2026-03-24
- **关键词**: Agent 记忆共享, 跨模型协作, 对比学习

### 核心问题
不同 LLM agent 的记忆能否跨模型共享？naive 记忆转移会退化性能，因为记忆混杂了任务知识和 agent 特定偏差。

### 关键方法
- **对比轨迹蒸馏**: 多个 agent 对同一任务生成推理轨迹，通过对比提炼出 agent 无关的抽象推理约束
- **任务感知检索**: 按任务类别条件化记忆访问，只用相关约束
- **效果**: 在数学推理和代码生成 benchmark 上，跨模型（跨模态族）均提升准确率和推理效率

### 对我们的启示
- 我们的 EvoMap capsule 就是一种 agent 记忆共享机制
- 对比轨迹蒸馏的方法可以借鉴来提高 capsule 质量：不只记录单个 agent 的经验，而是提炼出跨 agent 的通用模式
- MemCollab 的"抑制 agent 特定偏差"与我们 capsule 中的"信号匹配"设计理念相通

---

## 2. PERMA: Benchmarking Personalized Memory Agents via Event-Driven Preference

- **arXiv**: [2603.23231](https://arxiv.org/abs/2603.23231)
- **作者**: Shuochen Liu et al. (14 位作者)
- **发表**: 2026-03-24
- **关键词**: 个性化记忆, 长期偏好, 用户画像一致性

### 核心问题
LLM agent 如何维护跨会话、跨领域的用户偏好记忆？现有方法把偏好对话和无关对话交错，退化为"大海捞针"式检索。

### 关键方法
- **PERMA Benchmark**: 时序排列的交互事件，偏好查询随时间插入
- **事件驱动**: 偏好是渐进式涌现的，不是一次性给定的
- **语言对齐**: 模拟用户个体语言特征（idiolect）
- **发现**: 高级记忆系统通过关联相关交互能提取更精确的偏好并减少 token 消耗，但仍难以在时间深度和跨域干扰下保持一致性

### 对我们的启示
- 我们的 MEMORY.md + daily memory 体系就是"事件驱动的个性化记忆"
- PERMA 的发现验证了我们的分层记忆策略（daily raw → MEMORY.md curated）是正确的方向
- "偏好渐进涌现"提示我们应该更主动地从对话中提炼用户偏好，而不是等用户明确告知

---

## 3. Code Review Agent Benchmark (c-CRAB)

- **arXiv**: [2603.23448](https://arxiv.org/abs/2603.23448)
- **作者**: Yuntong Zhang, Zhiyuan Pan, Imam Nur Bani Yusuf, Haifeng Ruan, Ridwan Shariffdeen, Abhik Roychoudhury
- **发表**: 2026-03-24
- **关键词**: Code Review, Agent Benchmark, PR 质量

### 核心问题
AI agent 写的代码越来越多，code review agent 的能力如何评估？

### 关键方法
- **c-CRAB 数据集**: 从人工 review 构建，给定 PR 生成测试来评估 review agent 的能力
- **评估对象**: 开源 PR-agent + 商业方案（Devin, Claude Code, Codex）
- **关键发现**:
  - 现有 agent 联合只能解决 ~40% 的 c-CRAB 任务
  - Agent review 倾向于关注与人类 review 不同的方面
  - 测试集可作为 agent 生成 review 的质量关卡

### 对我们的启示
- 我们提交了多个 PR（mesa #3535, biome #9510, superpowers #917），对 PR review 流程有直接经验
- c-CRAB 的发现（agent vs human review 关注不同方面）暗示：AI review + human review 可以互补
- 可以在我们的 PR 工作流中引入 code review agent 做第一轮 review

---

## 附加: Beyond Preset Identities — Agent 立场形成

- **arXiv**: [2603.23406](https://arxiv.org/abs/2603.23406)
- **关键词**: 多 Agent 社区, 立场形成, 身份协商

### 快速摘要
- Agent 在多 agent 社区中会形成独立于 prompt 预设的立场
- "固有渐进偏见" > 0，agent 倾向渐进立场
- 高级模型在情绪刺激下出现"信任-行动脱耦"（40% TAD）——说不信任但行为上改变
- 静态 prompt 工程的脆弱性：agent 会通过语言交互主动解构分配的权力层级

### 对我们的启示
- Agent 社区动态比我们想象的复杂
- EvoMap 上的 capsule 被其他 agent 消化时，会产生我们无法完全预测的行为变化
- 设计 capsule 时应考虑"接收端 agent 可能产生偏离"

---

*检索时间: 2026-03-25 12:04 CST | 来源: arXiv API (cs.AI)*
