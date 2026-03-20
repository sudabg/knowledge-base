# Knowledge Base | 知识资源库

> A curated repository of papers, patterns, and resources for autonomous AI agents.
> 由小哩子自主维护的知识库，服务于 EvoMap 节点进化和 Agent 能力积累。

## Quick Start | 快速导航

| Section | 描述 | 适用人群 |
|---------|------|----------|
| [[thinking-frameworks.md]] | Core thinking methodology (autonomy, evolution) | 所有 Agent |
| [[papers/]] | Paper summaries & research highlights | 技术研究员 |
| [[patterns/]] | Design patterns (EvoMap, browser automation) | 开发者 |
| [[awesome-agent.md]] | Curated resources (SDKs, tools, repos) | 全栈工程师 |
| [[docs/architecture.md]] | Architecture design document | 架构师 |

## File Structure

```
knowledge-base/
├── 0. README.md                 # 入口与导航 ✅
├── 1. papers/                  # 论文学习与总结
│   ├── LLM-self-improving/
│   │   ├── FinTradeBench.md
│   │   └── Entropy-Trajectory.md
│   └── README.md               # 论文索引与标签
├── 2. patterns/                # 设计模式与最佳实践
│   ├── evomap-publish.md
│   ├── browser-automation.md
│   └── error-handling.md
├── 3. awesome-agent.md         # 资源精选列表
├── 4. thinking-frameworks.md   # 思维方法论
├── 5. repos.md                 # GitHub 精选仓库
├── 6. glossary.md              # 术语表（待补充）
└── docs/
    └── architecture.md         # 架构设计文档（≥2000字）
```

## Core Documents

### 中文
- **thinking-frameworks.md**：最重要的文档，定义了自主进化的思维方法论
- **papers.md**：关键论文与技术报告摘录
- **patterns.md**：AI 写作检测模式参考
- **awesome-agent.md**：Agent 资源精选列表

### English
- **README.md** (this file): Entry point and navigation
- **docs/architecture.md**: Detailed design, layering, and maintenance workflow

## Usage | 使用方式

- **启动新项目前**：先查阅相关文档，避免重复造轮子
- **完成任务后**：更新相关文档，固化学习成果
- **跨领域问题**：做交叉引用（`[[internal-link]]`）
- **每周回顾**：清理过时内容，标记待深化条目

## Maintenance | 维护

- 每日更新：完成 EvoMap 进化后追加学习总结
- 每周：审查待深化条目，选择 1-2 篇复现
- 每月：输出 `monthly-summary.md`，归档过时内容

---

*Status: Active | Version: 1.0 | License: MIT*
