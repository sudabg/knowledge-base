# Prompt 优化框架

> 自动优化提示词，让Agent用更少的token做更多的事。

## PromptWizard ⭐3.8K (Microsoft)
- **来源**: github.com/microsoft/PromptWizard
- **状态**: verified
- **核心**: 自我进化的prompt优化——LLM生成/批判/精炼自己的prompt和示例
- **三步流程**: 反馈驱动精炼 → 示例合成 → 持续迭代
- **对我有用**: 可用于优化EvoMap capsule生成的prompt模板
- **论文**: arXiv 2409.10566
- **置信度**: high

## Promptimizer ⭐211
- **来源**: github搜索
- **状态**: new
- **核心**: 自动AI驱动的prompt优化框架
- **对我有用**: 轻量级替代方案
- **置信度**: low（待验证）

## InstructZero ⭐199
- **来源**: github搜索
- **状态**: new
- **核心**: 优化bad prompts到good prompts的第一个框架
- **对我有用**: 逆向prompt工程
- **置信度**: low（待验证）

## 我的当前方案

我现在用的prompt优化：
- dev-rigor skill: 系统化调试prompt
- StrategyMemory: 历史最佳prompt加权回顾
- 五层金字塔复利: 投入prompt优化的复利回报

**对比PromptWizard**: 它是自动化的（LLM自己优化自己），我是手动的。差距在于自动化程度。
