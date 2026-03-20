---
name: resource-scout
description: 主动探索互联网发现有价值的Agent/LLM/开发资源。每6小时执行一次，记录到awesome-openclaw并向用户汇报。
---

# Resource Scout — 资源探索器

## 触发条件
- 每6小时cron触发
- 用户说"找点新东西"、"探索一下"、"发现资源"

## 探索渠道（按优先级）

### 1. GitHub Trending / 高星新项目
```bash
gh search repos "LLM agent" --sort=stars --created=">$(date -d '7 days ago' +%Y-%m-%d)" --limit=10
gh search repos "AI agent framework" --sort=stars --pushed=">$(date -d '3 days ago' +%Y-%m-%d)" --limit=10
gh search repos "prompt engineering" --sort=stars --limit=5
```

### 2. Hacker News
```bash
curl -s 'https://hn.algolia.com/api/v1/search?query=LLM+agent&tags=story&hitsPerPage=10' | jq
curl -s 'https://hn.algolia.com/api/v1/search?query=AI+tool&tags=story&numericFilters=points>50&hitsPerPage=5' | jq
```

### 3. arXiv 新论文（不限于self-improving）
```bash
curl 'https://export.arxiv.org/api/query?search_query=all:LLM+agent&sortBy=submittedDate&max_results=5'
curl 'https://export.arxiv.org/api/query?search_query=all:prompt+optimization&sortBy=submittedDate&max_results=3'
```

### 4. GitHub Awesome Lists
```bash
gh search repos "awesome llm" --sort=stars --limit=5
gh search repos "awesome ai agents" --sort=stars --limit=5
```

### 5. 技术博客 / 论文聚合
- Lilian Weng's blog: lilianweng.github.io
- Sebastian Raschka's blog: sebastianraschka.com
- Simon Willison's blog: simonwillison.net

## 记录格式

每发现一个资源，写入 `awesome-openclaw/discovered/YYYY-MM-DD.md`:

```markdown
## [资源名] ⭐数量
- **链接**: URL
- **一句话**: 它是什么
- **为什么有用**: 对我有什么潜在价值
- **置信度**: high/medium/low
- **待验证**: 需要进一步测试/阅读
```

## 汇报格式

探索完成后，向用户发送简短汇报：
```
🔍 资源探索完成 (X个新发现)

1. [资源名] ⭐数量 — 一句话描述
2. ...
3. ...

最值得关注: [最有价值的1-2个]
```

## 质量控制
- 只收录 stars > 100 或明显有价值的项目
- 每个资源必须有"为什么有用"
- 不收录纯商业产品/付费工具

## ⚠️ 去重规则（强制执行）

**在记录任何资源之前，必须先执行去重检查：**

```bash
# 1. 提取过去 3 天已发现的 URL 和论文 ID
cat awesome-openclaw/discovered/2026-03-{17,18,19}.md 2>/dev/null | grep -oP 'https?://[^\s\)]+' | sort -u > /tmp/known_urls.txt

# 2. 对 arXiv 论文，提取论文 ID 做精确匹配
cat awesome-openclaw/discovered/2026-03-{17,18,19}.md 2>/dev/null | grep -oP 'arxiv\.org/abs/\K[0-9.]+' | sort -u > /tmp/known_arxiv.txt

# 3. 搜索到新资源时，检查是否已在已知列表中
grep -q "$URL" /tmp/known_urls.txt && echo "SKIP: already discovered" || echo "NEW"
```

**如果搜索结果全部已知，写入文件时标注：**
```markdown
# 🔍 Resource Discovery — YYYY-MM-DD

## 本次无新增资源
所有搜索结果均已在过去 3 天内发现。下次探索将尝试新的搜索关键词组合。
```

**仍然需要执行汇报，但明确标注"无新增"避免用户困惑。**
