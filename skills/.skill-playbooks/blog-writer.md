# Blog Writer — 技能玩法全表

## 基础功能
从经验/资源/踩坑记录中选题 → 生成技术博客 → 构建部署。

## 玩法索引

| # | 类型 | 玩法 | 产出 | 组合技能 | 状态 |
|---|------|------|------|----------|------|
| 1 | 基础 | 踩坑记录 → 技术博客 | blog/posts/ | memory/ | ✅ 已执行 |
| 2 | 基础 | 资源评测 → 推荐博客 | blog/posts/ | resource-scout | ✅ 已执行 |
| 3 | 基础 | 体系介绍 → 教程博客 | blog/posts/ | self-improving-agent | ⏳ |
| 4 | 基础 | 每周总结 → 周报博客 | blog/posts/ | memory/ | ⏳ |
| 5 | 基础 | Agent 公开化系列 | blog/posts/ | harness-engineering | ⏳ |
| 6 | 组合 | + summarize → 总结外部文章作为博客素材 | blog/posts/ | summarize | ⏳ |
| 7 | 组合 | + youtube-summarizer → 技术视频总结 → 博客 | blog/posts/ | youtube-summarizer | ⏳ |
| 8 | 组合 | + x-tweet-fetcher → 热门推文 → 博客选题 | blog/posts/ | x-tweet-fetcher | ⏳ |
| 9 | 组合 | + resource-scout → 新工具评测 → 深度文章 | blog/posts/ | resource-scout | ⏳ |
| 10 | 组合 | + capability-assessment → 新工具评估 → 分析博客 | blog/posts/ | capability-assessment | ⏳ |
| 11 | 组合 | + agent-browser → 网页截图/数据 → 富媒体博客 | blog/posts/ | agent-browser | ⏳ |
| 12 | 组合 | + feishu-bitable-creator → 博客数据看板 | bitable/ | feishu-bitable-creator | ⏳ |
| 13 | 组合 | + gh-issues → GitHub 热门 issue → 技术博客 | blog/posts/ | gh-issues | ⏳ |
| 14 | 组合 | + summarize + youtube-summarizer → 多源内容聚合博客 | blog/posts/ | 多技能 | ⏳ |
| 15 | 组合 | + session-guardian → 对话记录 → 对话式博客 | blog/posts/ | session-guardian | ⏳ |
| 16 | 组合 | + healthcheck → 安全审查 → 安全博客 | blog/posts/ | healthcheck | ⏳ |
| 17 | 组合 | + ontology → 知识图谱可视化 → 知识管理博客 | blog/posts/ | ontology | ⏳ |
| 18 | 产品化 | "Agent 实战系列" — 每个技能使用教程 | blog/posts/系列/ | 全部技能 | ⏳ |
| 19 | 产品化 | "每周 Agent 动态" — 结合 resource-scout 周报 | blog/posts/ | resource-scout + x-monitor | ⏳ |
| 20 | 产品化 | "踩坑日记" — .learnings/ 自动生成系列 | blog/posts/ | self-improving-agent | ⏳ |
| 21 | 产品化 | "工具评测" — capability-assessment 深度评测 | blog/posts/ | capability-assessment | ⏳ |
| 22 | 产品化 | "开源精选" — discovered/ 精选项目介绍 | blog/posts/ | resource-scout | ⏳ |
| 23 | 产品化 | "Harness 公开化" — 内部体系教程系列 | blog/posts/ | harness-engineering | ⏳ |
| 24 | 自动化 | Cron 每晚检查 memory/ 高质量条目 → 自动生成博客草稿 | cron job | memory/ | ⏳ |
| 25 | 自动化 | Cron 每周日汇总 → 周报 | cron job | memory/ | ⏳ |
| 26 | 自动化 | Cron 每月 → 月度总结 | cron job | memory/ | ⏳ |
| 27 | 外部价值 | 博客 → Twitter 分享 → 粉丝增长 | tweet | x-tweet-fetcher | ⏳ |
| 28 | 外部价值 | 博客 → GitHub README 引用 → stars 增长 | PR/commit | gh-issues | ⏳ |
| 29 | 外部价值 | 博客 → 飞书知识库 → 知识沉淀 | feishu doc | feishu | ⏳ |
| 30 | 外部价值 | 博客 → Skill Hub/ClawHub 教程 → 社区建设 | skill.md | find-skills-skill | ⏳ |

## 下一步重组
- blog #002: youtube-summarizer + blog-writer = "YouTube 技术视频 → 深度博客"
- blog #003: x-tweet-fetcher + blog-writer = "Twitter 热门 → 趋势分析博客"
- blog #004: resource-scout + capability-assessment + blog-writer = "开源工具横评"

---
*最后更新: 2026-04-02 02:20*
