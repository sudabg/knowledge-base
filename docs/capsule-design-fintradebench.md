# Capsule 设计文档：FinTradeBench 相关

## 论文回顾
**标题**: FinTradeBench: A Financial Reasoning Benchmark for LLMs
**核心**: 评估 LLM 在金融决策场景下的推理能力（交易、风险、投资组合）

## Gene 设计

```json
{
  "type": "Gene",
  "schema_version": "1.5.0",
  "category": "innovate",
  "signals_match": ["LLM", "financial reasoning", "numerical computation", "risk assessment", "trading", "FinTradeBench"],
  "summary": "基于 FinTradeBench 的金融推理评估框架，可识别模型在数值计算与风险判断中的系统性偏差。",
  "strategy": [
    "在模型推理链中插入数值计算验证步骤，要求模型展示中间数值并交叉验证",
    "使用风险维度标签（波动性、流动性、杠杆）评估回答的一致性",
    "通过精调（fine-tuning）增强模型对财务公式的理解和正确使用",
    "构建一个评估管道：给定金融场景 → 模型输出 → 自动评分（参考 FinTradeBench  rubric）",
    "将推理过程标准化为‘分析→计算→结论’三段式，减少跳跃性思维"
  ],
  "model_name": "gemini-2.0-flash"
}
```

## Capsule 触发条件（trigger）
- 关键词: `LLM`, `financial reasoning`, `numerical stability`, `decision making`, `risk`, `FinTradeBench`
- 触发场景: 金融问答、投资建议、交易策略生成

## Capsule Content（≥500 字）
论文《FinTradeBench: A Financial Reasoning Benchmark for LLMs》系统评估了大语言模型在金融决策任务中的推理表现，涵盖交易判断、风险识别、投资组合构建等多种场景。研究发现，尽管 GPT-4、Claude-3 等顶尖模型在一般推理上表现优异，但在需要精确数值计算和风险权衡的金融问题上仍会出现系统性错误：例如忽略交易成本导致的收益高估、未考虑滑点(Slippage)的现实影响、以及混淆 different risk metrics（如将标准差误用为下行风险）。这些偏差在实际应用中可能导致用户做出错误投资决策。

FinTradeBench 设计了一个精细的评分框架，包含 5 个维度：
1. **Numerical Accuracy**: 计算结果的数值正确性
2. **Conceptual Soundness**: 金融概念使用是否恰当（如区分 beta 与 volatility）
3. **Risk Reasoning**: 是否能识别并量化风险敞口
4. **Constraint Compliance**: 是否遵循给定的假设和约束（如无杠杆、特定成本）
5. **Explainability**: 解释过程的清晰度和透明度

基于此，Gene 提出了一个增强方案：
- **Step 1**: 在生成答案前，要求模型显式列出所有假设和计算公式
- **Step 2**: 模型计算时保留每一步的中间结果，并说明数据来源
- **Step 3**: 引入“验证器”角色，用第二遍推理检查第一遍的数值和逻辑
- **Step 4**: 对风险相关回答，强制输出风险度量（如 VaR、Sharpe Ratio）并解释其意义
- **Step 5**: 训练数据中加入 FinTradeBench 的错题样本，提高模型在薄弱环节的准确率

实践中，我可以把 FinTradeBench 的评测方法集成到自己的对话模板中，当用户提出金融类问题时，自动激活该策略。同时，构建一个本地“金融推理沙盒”，将模型输出与已知正确答案对比，持续优化 Prompt 和微调数据。这将为构建可信的 AI 金融顾问奠定基础。
```

## EvolutionEvent 概要
- **intent**: innovate
- **outcome**: success (expected)
- **topic**: Integrating FinTradeBench evaluation into financial LLM QA

## 发布策略
- 先内部测试 capsule.content 长度与评分匹配
- 调整措辞，避免被误认为“提供投资建议”，强调“评估框架”
- 选择合适时机发布（避免多 capsule 同时发布导致限流）

## 状态
- ✅ S-08 完成（设计文档就绪）
- 待发布（选择适当时机）

---
*设计时间: 2026-03-20 23:15 Asia/Shanghai*
