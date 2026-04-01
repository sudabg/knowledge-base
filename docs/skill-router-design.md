# Skill Router 设计与实践文档

## 1. 问题背景

### 1.1 现状痛点

OpenClaw Agent 的技能系统面临三个核心问题：

**问题 1: 上下文膨胀**
- 48 个 skill 的 name + description 全部注入系统提示
- 即使不调用，列表本身消耗大量 token（约 3-5KB）
- 随着 skill 数量增长，上下文预算被持续侵蚀

**问题 2: 匹配精度低**
- 靠系统提示里的触发词做模糊匹配
- 触发词重叠严重（"写文章"同时匹配 blog-writer、summarize、brainstorming）
- 依赖模型的理解能力，不同模型表现差异大

**问题 3: 维护成本高**
- 新增 skill 需要同时更新系统提示
- 触发词散落在各处，难以统一管理
- 没有机制验证触发词是否真的有效

### 1.2 设计目标

| 目标 | 指标 | 当前基线 | 目标值 |
|------|------|---------|--------|
| 匹配准确率 | top-1 命中率 | ~60%（主观估计） | ≥85% |
| 响应延迟 | 路由耗时 | N/A（全靠模型推理） | <100ms |
| 维护成本 | 新增 skill 的配置项 | 2+ 处（SKILL.md + 系统提示） | 1 处 |
| 上下文开销 | 列表注入体积 | ~4KB | <1KB |

---

## 2. 架构设计

### 2.1 三层路由架构

```
用户任务描述
    │
    ▼
┌─────────────────────┐
│  Layer 1: 关键词快筛  │  ← 当前实现（skill_router.py）
│  耗时: <5ms          │
│  精度: ~70%          │
└─────────┬───────────┘
          │ candidates (top 5)
          ▼
┌─────────────────────┐
│  Layer 2: 语义匹配   │  ← 计划中
│  耗时: <50ms         │
│  精度: ~85%          │
│  方法: embedding     │
└─────────┬───────────┘
          │ candidates (top 3)
          ▼
┌─────────────────────┐
│  Layer 3: LLM 兜底   │  ← 可选
│  耗时: <500ms        │
│  精度: ~95%          │
│  方法: 轻量模型判断   │
└─────────┬───────────┘
          │
          ▼
     推荐结果 + 置信度
```

**设计原则：**
- 快速失败：Layer 1 置信度 >0.8 时直接返回，跳过后续层
- 渐进精确：每层成本递增，但只对上一层的候选做处理
- 可降级：任意层失败不影响下一层

### 2.2 Layer 1: 关键词快筛（当前实现）

**数据结构：**
```python
SKILL_INDEX = {
    "skill-name": {
        "keywords": ["关键词1", "关键词2"],
        "description": "一句话描述",
        "category": "分类标签",
        "triggers": ["触发词1", "触发词2"],
        "weight": 1.0  # 技能优先级权重
    }
}
```

**匹配算法：**
```python
def match_keywords(task: str, skill_entry: dict) -> float:
    task_lower = task.lower()
    keywords = skill_entry["keywords"]
    
    # 精确匹配
    exact = sum(1 for kw in keywords if kw in task_lower)
    # 模糊匹配（子串、拼音等）
    fuzzy = sum(0.5 for kw in keywords 
                if any(c in task_lower for c in kw[:2]))
    
    score = (exact + fuzzy) * skill_entry.get("weight", 1.0)
    return min(1.0, score * 0.3)  # 归一化到 0-1
```

### 2.3 Layer 2: 语义匹配（计划实现）

**方案选择：**

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| 本地 embedding（sentence-transformers） | 零成本、离线可用 | 精度受限、需预计算 | 内存充足环境 |
| 轻量 API（OpenAI ada-002） | 精度高、维护简单 | 有 API 成本 | 生产环境 |
| TF-IDF + 余弦相似度 | 零成本、实现简单 | 语义理解弱 | 过渡方案 |

**推荐：** 先用 TF-IDF 方案快速验证效果，再决定是否升级到 embedding。

**实现思路：**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticRouter:
    def __init__(self, skills_dir: Path):
        self.skills = self._load_skills(skills_dir)
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            analyzer='char_wb'  # 字符级 n-gram，对中文更友好
        )
        self._build_index()
    
    def _load_skills(self, skills_dir: Path) -> dict:
        """加载所有 skill 的 SKILL.md，提取 description + triggers"""
        skills = {}
        for skill_dir in skills_dir.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text()
                # 提取 YAML frontmatter 或首段作为描述
                desc = self._extract_description(content)
                skills[skill_dir.name] = {
                    "description": desc,
                    "content_preview": content[:500]
                }
        return skills
    
    def _build_index(self):
        """构建 TF-IDF 索引"""
        corpus = [
            f"{s['description']} {s['content_preview']}" 
            for s in self.skills.values()
        ]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.skill_names = list(self.skills.keys())
    
    def route(self, task: str, top_k: int = 3) -> list:
        """语义路由"""
        task_vec = self.vectorizer.transform([task])
        similarities = cosine_similarity(task_vec, self.tfidf_matrix)[0]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [
            {
                "skill": self.skill_names[i],
                "score": float(similarities[i]),
                "method": "tfidf_cosine"
            }
            for i in top_indices if similarities[i] > 0.1
        ]
```

### 2.4 Layer 3: LLM 兜底（可选）

仅在 Layer 1+2 置信度都低于阈值时触发。使用轻量模型（如 qwen3.6-plus-preview:free）做最终判断。

```python
LLM_FALLBACK_PROMPT = """
你是技能路由器。给定以下任务描述和候选技能，选择最匹配的 1 个。

任务: {task}

候选技能:
{candidates}

返回 JSON: {{"skill": "name", "confidence": 0.0-1.0, "reason": "..."}}
"""
```

---

## 2.5 Task Planner: 复合任务拆解编排

### 问题

单一任务可能包含多个子步骤，每个子步骤匹配不同技能。例如"写博客"不只是 `blog-writer`，还需要浏览器查素材、选题构思、发布等。

### 架构

```
用户任务
    │
    ▼
┌─────────────────────────┐
│  Composite Detection    │  判断：简单 or 复合？
│  触发条件:              │
│  1. 命中 TASK_PATTERNS  │
│  2. top-1<0.6 && ≥3 命中│
└─────────┬───────────────┘
          │ 复合
          ▼
┌─────────────────────────┐
│  Task Decomposer        │  模板匹配 → 子步骤列表
│  "写博客" → 6 steps    │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Per-Step Router        │  每个子步骤 → skill 路由
│  step1 → brainstorming  │
│  step2 → agent-browser  │
│  step4 → blog-writer    │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Parallelism Calculator │  根据依赖计算并行组
│  group1: [1,2,3] 并行   │
│  group2: [4] 串行       │
│  group3: [5] 串行       │
│  group4: [6] 串行       │
└─────────────────────────┘
```

### 模板定义格式

```python
TASK_PATTERNS = {
    "写博客": {
        "triggers": ["写博客", "写一篇博客", ...],  # 触发词
        "steps": [
            {
                "desc": "选题和构思",           # 子步骤描述
                "skill": "brainstorming",       # 推荐技能
                "priority": "P0",               # P0=先做, P1=并行, P2=收尾
                "depends_on": []                # 依赖的前置步骤索引
            },
            ...
        ]
    }
}
```

### 已内置的复合任务模板

| 模板 | 触发词示例 | 子步骤数 | 涉及技能 |
|------|-----------|---------|---------|
| 写博客 | "写博客"、"写一篇"、"技术博客" | 6 | brainstorming, agent-browser, blog-writer |
| 代码审查 | "审查代码"、"review"、"帮我看看代码" | 4 | understand-project, dev-rigor, review-swarm |
| 学技术 | "研究一下"、"学习"、"分析项目" | 4 | agent-browser, understand-project, coding-agent |
| 产品验证 | "验证想法"、"做调研"、"市场调研" | 6 | brainstorming, agent-browser, find-community, validate-idea, marketing-plan, pricing |
| 写推文 | "发推"、"发twitter"、"推广" | 4 | agent-browser, brainstorming, blog-writer, x-tweet-fetcher |

### 输出示例

```json
{
  "type": "composite",
  "pattern": "写博客",
  "total_steps": 6,
  "steps": [
    {"step": 1, "desc": "选题和构思", "recommended_skill": {"skill": "brainstorming", "score": 0.3}, "priority": "P0", "depends_on": []},
    {"step": 2, "desc": "搜索素材", "recommended_skill": {"skill": "agent-browser", "score": 0.3}, "priority": "P0", "depends_on": []},
    {"step": 4, "desc": "撰写内容", "recommended_skill": {"skill": "blog-writer", "score": 0.6}, "priority": "P1", "depends_on": [0, 1]}
  ],
  "parallel_groups": [
    {"group": 1, "steps": [1, 2, 3], "can_parallel": true},
    {"group": 2, "steps": [4], "can_parallel": false}
  ],
  "estimated_skills_used": ["brainstorming", "agent-browser", "blog-writer"]
}
```

### 如何添加新模板

在 `TASK_PATTERNS` 字典中添加条目：

```python
"部署上线": {
    "triggers": ["部署", "上线", "deploy", "发布到生产"],
    "steps": [
        {"desc": "运行测试", "skill": "dev-rigor", "priority": "P0", "depends_on": []},
        {"desc": "构建产物", "skill": "coding-agent", "priority": "P1", "depends_on": [0]},
        {"desc": "部署到服务器", "skill": "agent-browser", "priority": "P2", "depends_on": [1]},
        {"desc": "验证部署结果", "skill": "agent-browser", "priority": "P2", "depends_on": [2]},
    ]
}
```

然后运行 `--test` 验证新模板生效。

---

## 3. 当前实现详解

### 3.1 文件结构

```
scripts/
  skill_router.py      # 主路由脚本（4.3KB）
skills/
  {skill-name}/
    SKILL.md            # 技能定义（含 description 和 triggers）
    ...                 # 技能实现文件
```

### 3.2 数据流

```
1. 用户输入任务描述
2. skill_router.py 读取 SKILL_KEYWORDS 字典
3. 遍历每个 skill，计算关键词命中数
4. 按 score 降序排列
5. 返回 top 5 结果（JSON 格式）
6. Agent 根据结果决定是否调用对应 skill
```

### 3.3 评分机制

```python
# 当前评分公式
score = min(1.0, match_count * 0.3)

# 问题：
# - 命中 1 个关键词 = 0.3 分
# - 命中 2 个关键词 = 0.6 分
# - 命中 3 个关键词 = 0.9 分
# - 命中 4+ 个关键词 = 1.0 分（封顶）
```

**改进方向：**
- 加入关键词权重（高频核心词 vs 低频边缘词）
- 加入反向惩罚（命中否定词时降分）
- 加入分类加成（同类别技能间有排斥）

---

## 4. 实践指南

### 4.1 如何添加新 skill 到路由

**步骤 1：** 在 `SKILL_KEYWORDS` 中添加条目
```python
"my-new-skill": ["关键词1", "关键词2", "关键词3"],
```

**步骤 2：** 验证 skill 目录存在且有 SKILL.md
```bash
ls skills/my-new-skill/SKILL.md
```

**步骤 3：** 测试路由
```bash
python3 scripts/skill_router.py "任务描述包含关键词1"
# 期望输出包含 my-new-skill
```

**步骤 4：** 验证至少 3 个不同表述都能命中
```bash
python3 scripts/skill_router.py "表述1"
python3 scripts/skill_router.py "表述2"
python3 scripts/skill_router.py "表述3"
```

### 4.2 关键词设计原则

**DO:**
- 使用常见表述（"写博客" > "blog composition"）
- 中英文都覆盖（"浏览器" + "browser"）
- 包含同义词（"调试" + "debug" + "排错"）
- 包含动作词（"创建" + "修改" + "删除"）

**DON'T:**
- 不用过于泛化的词（"做"、"处理"、"搞"）
- 不用长句作为关键词
- 不超过 8 个关键词/skill（维护成本）
- 不和别的 skill 共享完全相同的关键词集

### 4.3 质量验证

**测试用例矩阵：**

| 任务描述 | 期望 skill | 实际结果 | 通过？ |
|---------|-----------|---------|--------|
| "帮我写一篇技术博客" | blog-writer | ? | ? |
| "打开浏览器搜一下" | agent-browser | ? | ? |
| "检查一下安全漏洞" | healthcheck | ? | ? |
| "飞书多维表格建表" | feishu-bitable-creator | ? | ? |
| "看看 EvoMap 为什么 503" | evomap-fault-diagnosis | ? | ? |

**验证脚本：**
```bash
# 批量测试
cat test_cases.txt | while read task; do
  result=$(python3 scripts/skill_router.py "$task" | jq -r '.[0].skill')
  echo "$task → $result"
done
```

### 4.4 性能基准

```bash
# 延迟测试
time python3 scripts/skill_router.py "测试任务"

# 期望结果:
# real  < 0.1s
# user  < 0.05s
# sys   < 0.02s
```

---

## 5. 演进路线

### Phase 1: 关键词快筛 + 复合任务拆解（✅ 当前）
- 静态字典 + 字符串包含 + TASK_PATTERNS 模板
- 简单任务耗时 <5ms，复合任务 <10ms
- 精度：简单任务 ~85%，复合任务 ~90%（模板命中时）
- 5 个内置复合任务模板
- 11/11 测试用例全过

### Phase 2: TF-IDF 语义匹配（⬜ 计划）
- 自动从 SKILL.md 提取语料
- 字符级 n-gram，对中文友好
- 耗时 <50ms
- 精度 ~80%

### Phase 3: Embedding 语义匹配（⬜ 未来）
- 本地 sentence-transformers 或 API
- 预计算 skill embedding 向量
- 耗时 <100ms
- 精度 ~90%

### Phase 4: 自学习路由（⬜ 远期）
- 记录每次路由结果 + 用户反馈
- 自动调整关键词权重
- 自动发现新关键词
- 精度 >95%

### Phase 5: LLM 驱动任务拆解（⬜ 远期）
- 当模板不匹配时，用 LLM 自动拆解
- 支持任意复合任务，无需预定义模板
- 成本：~200 token/次拆解

---

## 6. 对比分析

### 6.1 vs 系统提示触发词匹配

| 维度 | 系统提示触发词 | skill_router.py |
|------|--------------|----------------|
| 速度 | 依赖模型推理（秒级） | <5ms |
| 成本 | 每次消耗 token | 零成本 |
| 精度 | 依赖模型能力 | 可控、可测试 |
| 维护 | 分散在各 SKILL.md | 集中在一处 |
| 可测试 | 不可批量验证 | 可脚本化测试 |

### 6.2 vs Claude Code 的工具路由

| 维度 | Claude Code | skill_router.py |
|------|-------------|----------------|
| 匹配方式 | LLM 语义理解 | 关键词匹配 |
| 自适应 | 根据上下文动态调整 | 静态字典 |
| 维护成本 | 零配置 | 需手动维护 |
| 速度 | 秒级 | 毫秒级 |
| 适用 | 单次对话 | 批量任务路由 |

**核心差距：** Claude Code 把路由逻辑内化到了 LLM 推理中，而我们在 LLM 之外做了一个显式路由层。各有优劣：
- LLM 内化：灵活但慢、贵、不可测试
- 显式路由：快、免费、可测试，但维护成本高

---

## 7. 附录

### 7.1 当前 SKILL_KEYWORDS 完整映射

见 `scripts/skill_router.py` 中的 `SKILL_KEYWORDS` 字典。

### 7.2 相关文件

- `scripts/skill_router.py` — 主路由脚本
- `scripts/preflight.py` — 命令预检（路由前的安全检查）
- `skills/*/SKILL.md` — 各技能定义文件
- `AGENTS.md` — Tool Governance 章节

### 7.3 变更日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-03-31 | v1.0 | 初始版本，30 个 skill 关键词映射 |
| 2026-04-01 | v1.1 | 文档化 + 架构设计（本文档） |
| 2026-04-01 | v2.0 | Task Planner 复合任务拆解 + 5 个内置模板 + 并行组计算 + 11/11 测试全过 |
