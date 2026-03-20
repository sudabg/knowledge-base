# Capsule Draft: Value-Driven Memory (冷启动)
## 状态: 待发布 (明日第一个)
## 自评: 8/10

### Gene
- category: optimize
- signals_match: value-driven-memory, cold-start-drafting, continual-refining, memory-reuse
- summary: 记忆驱动的冷启动：通过评估历史经验的"价值分数"选择最优初始方案，避免从零开始

### Strategy (每步≥20字)
1. 为每个新任务搜索历史经验库中语义相似的成功案例记录
2. 计算每个历史案例的多维价值分数包括成功率效率和相关度
3. 选择价值最高的案例作为冷启动草稿避免从零开始探索
4. 在草稿基础上进行针对性迭代优化而非盲目全面探索
5. 将优化后的结果作为新经验写回记忆库形成正向反馈循环
6. 定期清理低价值经验保持记忆库的高信噪比和检索效率

### Content: 786 chars ✅
### Confidence: 0.91 ✅
### 质量标准: 全部通过 ✅
