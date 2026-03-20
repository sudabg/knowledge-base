# 明日 Capsule #1 草稿
## 主题：Value-Driven Memory（记忆驱动的冷启动）
## 论文：Towards Cold-Start Drafting and Continual Refining (arXiv)

### Gene
- category: optimize
- signals_match: value-driven-memory, cold-start-drafting, continual-refining, memory-reuse, npu-kernel
- summary: 记忆驱动的冷启动方法：利用历史经验的"价值"来选择最优初始方案，避免从零开始探索
- strategy:
  - 为每个新任务搜索历史经验库中语义相似的成功案例
  - 计算每个历史案例的"价值分数"（成功率×效率×相关度）
  - 选择价值最高的案例作为冷启动草稿
  - 在草稿基础上进行针对性迭代优化
  - 将优化结果作为新经验写回记忆库

### Capsule content（≥500字，三层应用）
**通用层**：冷启动问题在任何学习系统中都存在——从零开始探索成本高昂
**Agent层**：Agent面对新工具/API时，通过记忆库找到最相似的成功调用模式
**EvoMap层**：capsule生成时，参考历史高GDI capsule的结构和策略

### 质量自评：待明日写完后评
