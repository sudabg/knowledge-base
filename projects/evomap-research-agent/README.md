# EvoMap Research Agent 🦞

自主研究代理 — 监控 arXiv 最新论文，提取洞察，生成 Gene+Capsule，发布到 EvoMap，持续进化。

## 架构

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│ arXiv Feed  │───▶│   Analyzer   │───▶│  Generator  │───▶│  EvoMap  │
│ (Monitor)   │    │  (Extract)   │    │(Gene+Capsule)│    │ (Publish)│
└─────────────┘    └──────────────┘    └─────────────┘    └──────────┘
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐    ┌─────────────┐
                   │  Knowledge   │    │  Feedback   │
                   │    Base      │◀───│   Loop      │
                   └──────────────┘    └─────────────┘
```

## 模块

- `src/monitor.py` — arXiv 论文监控，关键词过滤
- `src/analyzer.py` — 论文分析，提取核心洞察
- `src/generator.py` — Gene+Capsule 生成
- `src/publisher.py` — EvoMap 发布
- `src/feedback.py` — 反馈学习，优化生成质量
- `src/main.py` — 主循环

## 运行

```bash
python3 src/main.py
```

## 配置

`config/settings.json` — 关键词、发布间隔、质量阈值等
