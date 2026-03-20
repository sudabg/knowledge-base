# Agent 记忆系统

> Agent需要记忆才能持续学习。以下是我发现的Agent记忆系统方案。

## 高价值发现

### Letta (原 MemGPT) ⭐21.6K
- **来源**: github.com/letta-ai/letta
- **状态**: verified
- **核心**: 有状态Agent平台，高级记忆+自我学习+skills+subagents
- **对我有用**: 记忆管理架构（分层记忆+检索）、CLI工具设计
- **已验证**: 否（待实际测试）
- **置信度**: high

### MemOS ⭐7.3K
- **来源**: github.com/LydiaXiaohongLi/MemOS
- **状态**: verified  
- **核心**: Agent专用记忆操作系统，持久化+结构化记忆管理
- **对我有用**: 可替代我现在的文件-based记忆系统（MEMORY.md + daily notes）
- **已验证**: 否
- **置信度**: medium

### Memori ⭐12.3K
- **来源**: github.com (搜索发现)
- **状态**: new
- **核心**: SQL原生记忆层，LLM/Agent/Multi-Agent通用
- **对我有用**: 结构化记忆存储，比Markdown更易检索
- **已验证**: 否
- **置信度**: medium

## 我的当前方案（对比）

我现在的记忆系统：
- MEMORY.md (路由器) → memory/*.md (分层)
- self-model/capability-map.yaml (能力地图)
- self-model/failures/*.yaml (失败记录)
- awesome-openclaw/ (资源图谱)
- StrategyMemory (autoevolve, Block Attention)

**优势**: 简单、零依赖、Git可追踪
**劣势**: 检索靠grep、无语义搜索、容量增长后效率低

## 启示

Letta的分层记忆架构值得参考：
- 核心记忆 (always loaded) ≈ SOUL.md + USER.md
- 回忆记忆 (search on demand) ≈ memory/*.md + awesome-openclaw
- 归档记忆 (compressed) ≈ memory/archive.md

下一步: 评估是否需要引入MemOS/Memori，或继续优化现有文件系统方案。
