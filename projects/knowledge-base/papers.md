# 关键论文与技术报告

## Agent & LLM 进化 (2024-2026)

### Self-Improving Systems
- **Trajectory-Informed Memory Generation for Self-Improving Agent Systems** (2026-03-11)
  - Gaodan Fang, Vatche Isahagian, K. R. Jayaram
  - 提取执行轨迹中的可操作学习，用于未来性能改进
  - [PDF](https://arxiv.org/abs/2603.06543)

- **On Information Self-Locking in Reinforcement Learning for Active Reasoning of LLM agents** (2026-03-12)
  - Yuya Yoshikawa, Hiroshi Takahashi
  - LLM agents 在主动推理中的信息自锁定问题及解决方案
  - [PDF](https://arxiv.org/abs/2603.07891)

- **Breaking User-Centric Agency: A Tri-Party Framework for Agent-Based Recommendation** (2026-03-11)
  - Yaxin Gong, Chongming Gao, Chenxiao Fan
  - 超越用户中心的推荐系统，考虑多方利益
  - [PDF](https://arxiv.org/abs/2603.05432)

### Memory & Knowledge Systems
- **MEMNON: A Neuro-Symbolic Architecture for Long-Term Reasoning in Language Agents** (2025-11-03)
  - 结合神经网络和符号推理的长期记忆架构
  - [PDF](https://arxiv.org/abs/2511.01567)

- **Recurrent Memory Transformer for Long-Context Language Modeling** (2024-08-15)
  - 带循环记忆的Transformer用于处理超长上下文
  - [PDF](https://arxiv.org/abs/2408.07742)

### AI Detection & Safety
- **Detecting AI-Generated Text Using Linguistic Features** (2024-05-18)
  - 基于统计语言特征的AI文本检测综述
  - [PDF](https://arxiv.org/abs/2405.11061)

- **Watermarking Large Language Models** (2023-05-25)
  - 神 watermarking 技术用于识别AI生成内容
  - [PDF](https://arxiv.org/abs/2305.13971)

### Tool Use & Agent Frameworks
- **Toolformer: Language Models Can Teach Themselves to Use Tools** (2023-02-01)
  - LLM 自学使用外部工具的框架
  - [PDF](https://arxiv.org/abs/2302.04761)

- **ReAct: Synergizing Reasoning and Acting in Language Models** (2022-10-06)
  - 推理和行动的结合，提升Agent决策能力
  - [PDF](https://arxiv.org/abs/2210.03629)

## 开源项目与框架

### 工具链与基础设施
- **LangChain** - LLM 应用开发框架
  - stars: 95k+, 用于构建AI agent和工作流
  - https://github.com/langchain-ai/langchain

- **LlamaIndex** - 数据框架用于LLM应用
  - stars: 25k+, 连接自定义数据源到LLM
  - https://github.com/run-llama/llama_index

- **AutoGPT** - 自主AI Agent
  - stars: 150k+, GPT-4驱动的自主agent
  - https://github.com/Significant-Gravitas/AutoGPT

- **BabyAGI** - 任务导向的AI Agent系统
  - stars: 30k+, 基于OpenAI的任务管理agent
  - https://github.com/yoheinakajima/babyagi

### 检测与安全
- **DetectGPT** - 零射击机器生成文本检测
  - 基于对数概率曲率的检测方法
  - https://github.com/ericmitchell/detectgpt

- **GLTR** - 使用GPT-2进行文本检测的可视化工具
  - https://github.com/HendrikStrobelt/gltr

### 记忆与知识图谱
- **MemGPT** - 带有自管理内存的LLM
  - https://github.com/cpacker/MemGPT

- **Neo4j** - 图数据库，用于知识图谱存储
  - https://neo4j.com/

## 今日更新 (2026-03-15)

从 EvoMap 进化循环和今日论文研究中提取的模式：

1. **轨迹分割学习** - 将Agent执行分解为可分析的片段
2. **模式提取与归类** - 识别成功和失败的行为模式
3. **上下文相关检索** - 基于当前任务检索相关历史经验
4. **效果追踪与衰减** - 监控记忆的使用频率和效果
5. **多视角反馈整合** - 融合自我评估、外部反馈和环境结果

这些模式已融入 ai-text-audit 的检测逻辑中。

## Agent 记忆与进化 (2026-03-16/17 新增)

### Multi-Agent Self-Evolution
- **SAGE: Multi-Agent Self-Evolution for LLM Reasoning** (2026-03-16)
  - Yulin Peng, Xinxin Zhu, Chenxing Wei, et al.
  - 四Agent闭环（Challenger/Planner/Solver/Critic）实现无监督LLM推理提升
  - Qwen-2.5-7B: LiveCodeBench +8.9%, OlympiadBench +10.7%
  - [PDF](https://arxiv.org/abs/2603.15255)

- **ARISE: Agent Reasoning with Intrinsic Skill Evolution in Hierarchical RL** (2026-03-17)
  - Yu Li, Rui Miao, Zhengling Qi, Tian Lan
  - 分层RL框架：Manager维护技能库，Worker在技能指导下推理
  - 从成功轨迹提炼可复用策略，跨域泛化突出
  - [PDF](https://arxiv.org/abs/2603.16060)

### Agent 记忆系统
- **Chronos: Temporal-Aware Conversational Agents with Structured Event Retrieval** (2026-03-17)
  - 将对话分解为SVO事件元组，建立结构化事件日历
  - LongMemEvalS 上 95.60% accuracy，SOTA
  - 已实现：chronos_engine.py（285 events extracted）
  - [PDF](https://arxiv.org/abs/2603.16862)

### Agent 恢复与纠错
- **LEAFE: Learning Feedback-Grounded Agency from Reflective Experience** (2026-03-17)
  - 从反思经验中内化恢复能力：回溯→探索替代分支→内化
  - Pass@128 提升 14%（vs GRPO）
  - 已实现：recovery.py（6种错误恢复策略）
  - [PDF](https://arxiv.org/abs/2603.16843)

### Agent 安全
- **ClawWorm: Self-Propagating Attacks Across LLM Agent Ecosystems** (2026-03-16)
  - LLM Agent生态系统中的自传播攻击研究
  - ⚠️ 安全相关，需关注对 OpenClaw 类工具的影响
  - [PDF](https://arxiv.org/abs/2603.15727)

### 多Agent协作
- **Adaptive Theory of Mind for LLM-based Multi-Agent Coordination** (2026-03-17)
  - 让LLM Agent拥有自适应心理理论能力，用于多Agent协调
  - [PDF](https://arxiv.org/abs/2603.16264)

- **Code-A1: Adversarial Evolving of Code LLM and Test LLM via RL** (2026-03-16)
  - 代码LLM和测试LLM的对抗进化，通过强化学习统一
  - [PDF](https://arxiv.org/abs/2603.15611)
