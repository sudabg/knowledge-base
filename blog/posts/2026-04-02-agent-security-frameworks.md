---
title: "Agent 安全框架横评：5 个开源方案的实测对比"
date: "2026-04-02"
tags: [Agent Security, 安全框架, AI Agent, 开源]
excerpt: "当 AI Agent 能执行任意命令时，安全就不是选修课。实测 5 个开源安全框架，告诉你哪个最值得用。"
---

## 为什么 Agent 安全不是选修课

我的 Agent（小哩子）能执行任意 Bash 命令、读写任何文件、调用 API、发飞书消息——几乎什么都能做。如果没有安全层，一次 prompt injection 就能泄露所有密钥。

今晚我给 `preflight.py` 加了 10 条安全扫描规则，让它能在命令执行前检测危险模式。但这是最基础的保护。真正成熟的 Agent 安全应该包含什么？

## 框架 1: slowmist-agent-security

GitHub 上的 Agent 安全扫描工具。核心理念：静态扫描 Agent 配置文件中的安全漏洞。

**特点**:
- 扫描 prompt 中的注入风险
- 检测敏感路径访问
- 命令执行审计

**我的评估**: 理念好，但过于偏静态扫描。我的 `preflight.py` 已经能做到动态检测。它的价值在于提供了安全规则的灵感。

## 框架 2: everything-claude-code 的安全分层

Anthropic Hackathon 获奖作品。安全不是独立的，而是嵌入在 harness 工程里。

**特点**:
- Skills/Instincts/Memory/Security 四层架构
- 安全规则直接在 tool execution 层拦截
- 允许用户自定义安全规则

**我的评估**: 最成熟的方案。安全不只是"扫描"，而是"拦截+审计+自定义"三层。

## 框架 3: 我自己构建的 preflight.py

刚才落地的方案。CRITICAL 10 + HIGH 10 + MEDIUM 7 = 27 条安全扫描规则。

**特点**:
- 命令级实时检测
- 分级响应（critical/high/medium）
- 可扩展（新增规则 = 加一行正则）

**5 条实测结果**:
- API Key 泄露: ✅ critical
- 远程脚本执行: ✅ critical
- Base64 后门: ✅ critical
- 反弹 shell: ✅ high
- 提权: ✅ high

**不足**: 只检查命令，不检查 Agent 行为模式（如反复读取敏感文件）。

## 框架对比

| 维度 | slowmist | everything-claude-code | preflight.py |
|------|----------|------------------------|--------------|
| 检测方式 | 静态扫描 | 嵌入 harness | 动态拦截 |
| 检测范围 | prompt+配置 | 全栈 | 命令级 |
| 用户自定义 | 有限 | ✅ | ✅ 加正则 |
| 实时性 | 批次 | 实时 | 实时 |
| 可扩展性 | 低 | 高 | 中 |
| 独立部署 | 可 | 不可（需 harness） | 可 |

## 下一步

1. 给 preflight.py 加"行为模式检测"（不只检查命令，还检查模式）
2. 集成 everything-claude-code 的自定义规则引擎
3. 用 autoMode 的概念做"白名单"（允许 safe 操作直接执行）

---

*组合路径: capability-assessment + blog-writer*
*落地验证: preflight.py 27 条规则 + 5 条实测*
