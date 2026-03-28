---
name: capability-assessment
description: "Automated resource capability assessment and integration. Use when: (1) Resource exploration discovers new GitHub projects or papers, (2) User asks to evaluate external tools against current capabilities, (3) HEARTBEAT runs and finds new discoveries in awesome-openclaw/discovered/, (4) User says '研究一下这些新发现' or '对比一下谁优谁劣'. Fetches external project details, compares with current harness, makes adopt/reject decisions, implements high-value integrations, logs learnings."
---

# Capability Assessment Skill

将「发现新资源 → 对比评估 → 整合精华」的流程自动化。

## 触发条件

| 场景 | 触发方式 |
|------|---------|
| 资源探索发现新项目 | HEARTBEAT 中自动检测 `awesome-openclaw/discovered/YYYY-MM-DD.md` |
| 用户手动要求 | "研究一下这些新发现" / "对比谁优谁劣" / "整合到 harness" |
| 定期审查 | 每周一次，检查 discovered/ 目录有无未处理的发现 |

## 流程概览

```
发现报告 → 深度阅读外部项目 → 维度对比表 → adopt/reject/defer 决策 → 落地执行 → 记录学习
```

## Step 1: 读取发现报告

```bash
# 找到最新的未处理发现报告
ls -t awesome-openclaw/discovered/*.md | head -1
```

解析报告中的项目列表：名称、GitHub URL、一句话描述。

## Step 2: 深度阅读外部项目

对每个有价值（置信度 high）的项目：

1. **Fetch README**: 用 `curl -sL --max-time 10 "https://ghfast.top/https://raw.githubusercontent.com/<owner>/<repo>/main/README.md"`
2. **提取核心信息**:
   - 目录结构（如果有）
   - 核心设计理念
   - 与我方系统的潜在重合点
3. **检查代码**: 只 fetch 核心文件（1-2 个），不全量 clone

## Step 3: 维度对比表

对每个项目，按以下维度对比：

| 维度 | 外部项目 | 我方系统 | 胜者 |
|------|---------|---------|------|
| 架构设计 | ... | ... | 🏆 ... |
| 核心功能 A | ... | ... | |
| 核心功能 B | ... | ... | |
| 可操作性 | ... | ... | |

用 COMMUNICATION.md 风格写：不用华丽辞藻，用数据说话，正向陈述。

## Step 4: 三档决策

每个外部资源必须做出明确决策：

| 决策 | 含义 | 后续动作 |
|------|------|---------|
| **ADOPT** | 直接吸取，需要代码变更 | 创建/修改文件，执行落地 |
| **ACKNOWLEDGE** | 概念认同，不需要代码 | 记录到 LEARNINGS.md，不加文件 |
| **REJECT** | 放弃，不兼容或无价值 | 记录理由，不执行 |

### 决策规则

- 对方有、我方没有的**架构级优势** → ADOPT
- 对方有、我方有替代方案的 → ACKNOWLEDGE（不重复实现）
- 对方依赖特定生态（如 VS Code、Claude Code）→ REJECT
- 对方概念与我方重合但无增量 → ACKNOWLEDGE

## Step 5: 落地执行

仅对 ADOPT 决策执行：
1. 创建新文件或修改现有文件
2. 更新 SOUL.md/TOOLS.md/AGENTS.md 的引用
3. 做语法验证（py_compile）

## Step 6: 记录学习

使用 self-improvement skill 格式，每个项目一条 LEARNINGS 条目：
- `LRN-YYYYMMDD-XXX` 格式
- 包含对比摘要、决策、盲点扫描
- ADOPT 的项目标记 `Status: promoted`

## Step 7: 盲点扫描

完成后执行 6 点扫描（从 axioms/M01）：
1. 这次整合引入了什么新复杂性？
2. 对方的积累年限 vs 我的——深度差距在哪？
3. 我创建的文件是否真的会被用到？
4. 有没有成功陷阱（照搬了不适合我的东西）？
5. 上次整合后实际效果如何？
6. 下次整合应该关注什么方向？

## 输出格式

```markdown
## 🧬 资源能力评估 — YYYY-MM-DD

### 📊 对比矩阵

| 项目 | 决策 | 理由 |
|------|------|------|
| project-a | ADOPT | 架构级优势，直接吸取 |
| project-b | ACKNOWLEDGE | 概念重合，不加代码 |
| project-c | REJECT | VS Code 生态，不兼容 |

### ✅ 已落地
- 文件名: 变更描述

### 📝 学习记录
- LRN-YYYYMMDD-XXX: 一句话摘要

### ⚠️ 盲点
- 发现 1: 行动承诺
```

## 使用方式

### 手动触发（对话中）
```
用户: 研究一下这些新发现，对比一下谁优谁劣
→ 读取 discovered/ 最新报告
→ 执行 Step 1-7
→ 输出评估报告
```

### 自动触发（HEARTBEAT）
在 HEARTBEAT.md 中添加：
```markdown
## 📊 资源能力评估（发现新项目时）
- ✅ 检查: `ls -t awesome-openclaw/discovered/*.md | head -1`
- ✅ 如果有未处理的发现报告（无对应 LEARNINGS 条目），执行 capability-assessment skill
- ✅ 输出: 评估报告写入 memory/YYYY-MM-DD.md
```

## 注意事项

- 每次评估 3-5 个项目，不要一次评估太多
- ADOPT 的数量不超过 2 个/次，避免引入过多变更
- fetch 外部项目时用 ghfast.top 代理（axiom: TOOLS.md 中有记录）
- 评估表用中文写，但技术术语保留英文
- COMMUNICATION.md 规则必须遵守：禁用破折号、禁用华丽辞藻
