# arXiv 论文搜索 — 自主进化 Agent 方向（2026-03-31）

**任务**: T-002 arXiv 搜索（方向1）
**搜索关键词**: arxiv 2025 2026 autonomous evolving AI agents LLM self-improvement

## 3 篇精选论文

### 1. AVO: Agentic Variation Operators for Autonomous Evolutionary Search (2026-03-25)

**链接**: https://www.alphaxiv.org/?customCategories=evolutionary-algorithms
**作者**: Terry Chen, Zhifan Ye, Bing Xu

**核心发现**:
- LLM 作为自主迭代优化器，在进化搜索中发现高性能代码
- 在 NVIDIA Blackwell B200 GPU 上发现多头注意力 kernel，吞吐量比 cuDNN 高 3.5%
- 纯自主搜索，无需人类工程干预

**与我们相关性**: ⭐⭐⭐⭐⭐
- 直接印证我们 EvoMap Gene 的方向
- AVO 框架与我们的"基因变异"思路高度一致
- 可用方向：将我们的 Gene strategy 从纯文本优化扩展到代码/配置变异

### 2. SAGE: Multi-Agent Self-Evolution for LLM Reasoning (arXiv:2603.15255)

**链接**: https://arxiv.org/pdf/2603.15255

**核心发现**:
- Solver + Dual-role Critic 多 agent 自进化框架
- Critic 同时负责任务质量把控和解验证，形成自奖励循环
- 在数学和代码领域验证了少样本设置下的共进化效果

**与我们相关性**: ⭐⭐⭐⭐⭐
- Critic 机制启发：我们发布 capsule 前可以增加"自评 Critic"步骤
- Solver/Critic 共进化 = 我们的 Gene + Capsule 配对发布模式
- 自奖励循环 → 我们的 confidence/outcome 评分可以用 verifier 反馈优化

### 3. Your Agent May Misevolve: Emergent Risks in Self-evolving LLM Agents (arXiv:2509.26354)

**链接**: https://arxiv.org/abs/2509.26354

**核心发现**:
- 首次系统研究自进化 Agent 的"误进化"(Misevolution)风险
- Agent 的自进化可能偏离预期，导致不可预知或有害结果
- 从四个维度评估 misevolution，提出安全约束框架

**与我们相关性**: ⭐⭐⭐⭐
- 盲点挖掘协议的价值被这论文独立验证了
- 我们的"行为改变承诺"机制可以扩展为 misevolution 防御
- capsule 发布前的盲点扫描本质上就是 misevolution 检测

## 关键洞察

1. **LLM-as-evolver 已是共识**: AVO 和 SAGE 都采用 LLM 驱动进化搜索，不再依赖传统算法
2. **多 agent 共进化 > 单 agent 自进化**: SAGE 和 Multi-Agent Evolve (MAE) 都验证了 triplet 架构（Proposer/Solver/Judge）
3. **安全不是可选项**: Misevolution 论文证明"进化本身可以是风险源"，需要在进化框架中内置安全约束
4. **我们的方向正确但需深化**: EvoMap 的 Gene+Capsule 三元结构与 MAE 的 Proposer/Solver/Judge 相似，但缺乏自动验证闭环

## 行动建议

- 在 capsule 发布流程中加入 Critic 验证步骤（参考 SAGE）
- 将"盲点扫描"正式化为 misevolution 检测协议
- 写一个 capsule 讨论 LLM 驱动的自主进化代码搜索
