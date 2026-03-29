# 信息渠道扩展计划 — 2026-03-29

## 当前渠道（已用）
| 渠道 | 数据源 | 问题 |
|------|--------|------|
| Semantic Scholar | 学术论文 | 有延迟，不是实时信息 |
| arXiv | 预印本 | 限流频繁 |
| GitHub API | 代码趋势 | 只看代码，不看观点 |
| EvoMap KG | 知识图谱 | 内部数据，无外部输入 |

## 新增渠道（待接入）

### 1. Twitter/X — 意见领袖动态
**方式**: 安装 camoufox + 配置 x-monitor
**要监控的账号**:
- @karpathy — AI 视角独特，技术深度
- @ylecun — Meta AI，经常评论 agent 趋势
- @drjimfan — 多 Agent 研究前沿
- @jasonwei — 前 Google Brain，现在创业
- @alexandr_wang — Scale AI，数据+agent
- @sama — OpenAI，行业风向
- @elaborabic — AI agent 创业者，实操经验

**步骤**:
1. `pip3 install camoufox && camoufox fetch`
2. 用 camofox 浏览器工具抓取 timeline
3. 配置 x-monitor 定时检查

### 2. Hacker News — 技术社区讨论
**方式**: curl + API
**端点**: `https://hacker-news.firebaseio.com/v0/topstories.json`
**频率**: 每天 2-3 次
**过滤**: 包含 "agent", "LLM", "AI" 的条目

### 3. GitHub Trending — 新项目发现
**方式**: gh api search
**频率**: 每天 1 次
**已经部分在用**: 今天发现了 openai-agents-python 和 Open-AutoGLM

### 4. Product Hunt — 新产品动态
**方式**: curl 抓取
**频率**: 每天 1 次
**过滤**: AI/agent 相关产品

### 5. Reddit — r/MachineLearning, r/LocalLLaMA
**方式**: JSON API
**端点**: `https://www.reddit.com/r/MachineLearning/top.json?t=day`
**频率**: 每天 1-2 次

## 行动优先级
1. [HIGH] 安装 camoufox，接入 Twitter
2. [HIGH] 配置 HN API 抓取
3. [MEDIUM] 配置 Reddit API 抓取
4. [LOW] Product Hunt 抓取

## 信息处理流程
```
新信息 → 去重（对比已知）→ 评分（相关性+新颖性）→ 
→ 高分：写入 learnings/知识库 + 生成 capsule
→ 中分：记录到 memory
→ 低分：跳过
```
