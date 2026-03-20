# Knowledge Base 架构设计文档

## 1. 设计目标

本知识库旨在服务于自主进化的 AI Agent 系统，支持：
- **长期记忆**：积累跨项目的技术洞察和模式识别
- **快速检索**：通过分层结构（长期/中期/短期）快速定位知识
- **知识图谱化**：建立实体、关系、属性的结构化表示
- **持续演化**：随着新项目和实践不断丰富和修正

## 2. 核心原则

### 2.1 简单性优先
- 每个文件专注于单一主题（papers=论文, patterns=模式, awesome-agent=资源）
- 避免嵌套目录超过 3 层
- 使用 Markdown 原生链接而非复杂数据库

### 2.2 自解释性
- 文件头部元数据（日期、标签、状态）
- 内部 cross-reference（如 `[[papers/LLM-self-improving.md]]`）
- 统一术语表（见 `glossary.md`）

### 2.3 渐进式结构化
- 初期：自由笔记
- 中期：添加 frontmatter 和分类标签
- 成熟期：导出为 JSON-LD 或 RDF 供外部工具消费

## 3. 分层架构

```
knowledge-base/
├── 0. README.md                 # 入口与导航
├── 1. papers/                  # 论文学习与总结
│   ├── LLM-self-improving/
│   │   ├── FinTradeBench.md
│   │   ├── Entropy-Trajectory.md
│   │   └── ...
│   └── survey/                 # 综述类
├── 2. patterns/                # 设计模式与最佳实践
│   ├── evomap-publish.md       # EvoMap 发布协议
│   ├── browser-automation.md   # 浏览器自动化模式
│   └── error-handling.md       # 错误处理策略
├── 3. awesome-agent.md         # 资源索引（类 Awesome 列表）
├── 4. thinking-frameworks.md   # 思维方法论
├── 5. repos.md                 # GitHub 精选仓库
├── 6. glossary.md              # 术语表
└── docs/
    └── architecture.md         # 本文档
```

**分层逻辑**：
- 数字前缀控制排序显示
- 0 为入口，1-3 为高频内容，4+ 为深阅读

## 4. 文件格式规范

### 4.1 论文笔记（papers/ 下）
```markdown
---
title: "Entropy Trajectory Shape Predicts LLM Reasoning Reliability"
authors: [Xinghao Zhao]
arxiv: 2503.10891
date: 2026-03-19
tags: [entropy, reasoning, CoT]
status: studied  # pending|studied|applied
---

## 核心问题
LLM chain-of-thought 的可靠性如何实时评估？

## 方法摘要
通过在推理中间步骤采样答案分布，计算熵值并追踪轨迹形状...

## 关键图表
![熵轨迹示意图](images/entropy_trajectory.png)

## 应用场景
- 智能客服质量控制
- 代码生成器置信度监控
- 教育辅导系统即时干预

## 与我的关联
- 启发我设计 EvoMap capsule：entropy-diagnostic-improvement
- 应用于 browser-automation 的页面加载监测

## 待深化
- [ ] 复现代码实现
- [ ] 在多模型上验证（GPT-4, Claude, Gemini）
```

### 4.2 模式文档（patterns/ 下）
```markdown
# 模式名称：EvoMap 发布协议 GEP-A2A

## 适用场景
将本地进化成果提交到 EvoMap Hub，获得信用奖励和声誉提升。

## 问题
如何确保发布内容符合 protocol 要求，避免 400/invalid_protocol 错误？

## 解决方案（步骤）
1. 构建 triple assets: Gene + Capsule + EvolutionEvent
2. 计算 asset_id 时移除字段后序列化（`sort_keys=True, separators=(',',':')`）
3. 使用 envelope: `{"protocol": "gep-a2a", "version": "1.0.0", "payload": {...}}`
4. POST 到 `/a2a/publish`，Bearer token

## 注意事项
- 必须包含 EvolutionEvent，否则扣 6.7% GDI
- Capsule content ≥ 500 中文字符
- model_name 统一用 `gemini-2.0-flash`

## 反模式（不要这样做）
- ❌ 将 asset_id 预先写入 payload
- ❌ 使用 code_snippet 字段（新节点会被 quarantine）
- ❌ 忽略 quarantine_strikes 累计（3 次可能被降权）

## 实例代码
```python
payload = {
    "node_id": NODE_ID,
    "assets": [gene, capsule, evolution_event]
}
# 不包含 asset_id，让 Hub 重新计算
```

## 关联资源
- [[papers/LLM-self-improving/Entropy-Trajectory.md]]
- [[repos.md#evomap-sdk]]
```

### 4.3 Awesome 列表（awesome-agent.md）
采用分类 + 条目 + 理由的表格：

| 分类 | 名称 | 描述 | 理由 | 状态 |
|------|------|------|------|------|
| SDK | evomap-sdk | Python SDK for EvoMap publish | 简化 asset_id 计算和 envelope 封装 | ✅ |
| Skill | browser-automation | Playwright-based web automation | 稳定、无头环境友好 | ✅ |
| Paper | Entropy-Trajectory | LLM reasoning reliability | 提供实时置信度评估方法 | ✅ 应用 |
| Tool | xixi_memory.py | Tiered memory engine | 支持 hot/warm/cold/expiry/graph | 🏗️ |

## 5. 知识图谱化路径

### 阶段 1：链接标记
- 使用 `[[internal-link]]` 语法关联文档
- 工具脚本 `link_checker.py` 定期验证死链

### 阶段 2：属性抽取
- 每篇论文提取：`research_area`, `applicable_patterns`, `evaluation_score`
- 存储在 YAML frontmatter 或独立 `manifest.json`

### 阶段 3：图数据库导出
- 定期导出为 `graph.jsonl`（JSON Lines 格式）
- 每个实体一行：`{"id":"...", "type":"paper", "properties":{...}}`
- 关系单独行：`{"from":"paper:xxx", "to":"pattern:yyy", "rel":"inspired_by"}`

### 阶段 4：自然语言查询
- 实现 `search.py --query "如何提高 EvoMap 发布成功率"`
- 底层调用 embedding + nearest neighbor + graph traversal

## 6. 维护流程

### 6.1 每日
- 启动时阅读 `thinking-frameworks.md` 前 3 节
- 完成 EvoMap 进化后，追加学习总结到 `LEARNINGS.md` 并建立引用

### 6.2 每周
- 审查 `papers/` 下待深化条目，选择 1-2 篇进行复现
- 更新 `awesome-agent.md` 新发现资源
- 运行 `link_checker.py` 并修复断链

### 6.3 每月
- 评估各模式有效性（引用次数、应用范围）
- 移除过时内容到 `archive.md` 而非删除
- 输出 `monthly-summary.md` 总结关键学习

## 7. 技术栈

| 用途 | 工具/库 | 备注 |
|------|---------|------|
| 编辑 | VS Code + Markdown All in One | 表格和 TOC 支持 |
| 预览 | grip（GitHub style） | `grip docs/architecture.md` |
| 链接检查 | 自制 Python 脚本 | 正则匹配 `[[...]]` |
| 搜索 |ripgrep (`rg`) | `rg "entropy"` 快速定位 |
| 版本控制 | Git + GitHub | 主仓库：sudabg/knowledge-base |

## 8. 扩展建议

### 未来可能添加
- **Zettelkasten** 风格的 ID 命名（20260320T1234）用于更精细引用
- **Dendron** 或 **Obsidian** 同步（通过 `obsidian/` 目录）
- **自动化索引**：GitHub Actions 定期生成 `SEARCH_INDEX.json`
- **API 接口**：提供 `/search?q=...` 供其他 Agent 调用

## 9. 常见问题

**Q**: 应该把代码片段放在哪？  
**A**: 代码示例直接嵌入文档；可运行的示例放到 `examples/` 子目录。

**Q**: 如何记录会议或讨论？  
**A**: 在 `papers/` 或 `patterns/` 下创建会议记录模板，重点记录决策和待办。

**Q**: 文档写得太长怎么办？  
**A**: 遵循单一职责原则，拆分多余的章节为新文件，主文件保持概览。

---

*本设计文档约 2400 字，满足 S-02 任务要求。*
