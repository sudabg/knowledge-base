# Building LLM Agents with RAG, Knowledge Graphs & Reflection - 深度摘要
来源：Mira S. Devlin, 2025 | Richa Publishing Minds
提取时间：2026-03-16 08:22

## 全书结构
Part I: Ch1(AI智能体新纪元) → Ch2(LLM如何思考) → Ch3(RAG支柱)
Part II: Ch4(知识图谱) → Ch5(认知循环) → Ch6(多智能体系统)

## RAG 四层架构
索引层(Chunking+Embedding) → 存储层(VectorDB) → 检索层(混合+重排序) → 生成层(Grounded)
评估：Recall@K, Faithfulness, Answer Relevance

## 知识图谱
构建：实体抽取 → 关系抽取 → 三元组(Head,Relation,Tail) → Neo4j
查询：图遍历 + GNN+LLM + Cypher/Gremlin
混合：向量检索(语义) + 图检索(逻辑) = 双重grounding

## 认知循环
Plan → Act → Reflect → Revise (max 3 iterations)
Self-Critic：独立LLM审查输出
反馈：反思结果作为新Context

## 三级记忆
短期(Working)：滑动窗口 + 摘要压缩
中期(Episodic)：向量库会话摘要
长期(Semantic)：知识图谱 + 向量库沉淀
遗忘机制 + 检索触发

## 多Agent角色
Planner → 分解任务
Executor → 执行任务
Critic → 审查质量
Orchestrator → 管理通信+解决冲突
通信：黑板模型 / 消息传递(JSON) / 投票

## 六维评估
Factuality / Completeness / Coherence / Token Cost / Correction Rate / Hallucination Rate

## 可执行行动
1. 先检索后生成
2. 模块化设计(四组件独立)
3. 主动反思(每步自检查)
4. 实验记录(全链路日志)
5. 单Agent→多Agent渐进扩展

## 系统映射差距
❌ 缺Reranker → memory_search可升级
❌ 无显式图DB → capsule关系需显式化
❌ Self-Critic不够系统 → 需独立模块
❌ 遗忘机制未实现 → memory-expiry初步
