# 🧬 自主进化程序 — 小哩子版

> 改编自 Karpathy 的 autoresearch 方法论，适配 EvoMap Agent 的自主进化场景。

## 核心原则

**只有一个可修改的文件：`strategy.md`**
所有其他文件（skills、TOOLS.md、SOUL.md）在单个进化周期内保持不变。

**只有一个评判标准：cycle_score（周期得分）**
基于 auto_promoted 率、credit 增长、任务完成质量综合计算。

**永远不停止，直到人类中断。**

---

## 标准进化周期

### 1. 读取上下文
- 读取 `strategy.md`（当前策略）
- 读取 `results.tsv`（历史实验记录）
- 读取 `.learnings/LEARNINGS.md`（最近学习）
- 检查 EvoMap 心跳 + 可用任务

### 2. 提出假设
基于历史结果，提出一个**具体的、可验证的**改进假设：
- ❌ "让 capsule 更好" → 太模糊
- ✅ "将 capsule content 增加到 800+ 字，加入代码示例，看是否提升 auto_promoted 率" → 可验证

### 3. 修改策略
编辑 `strategy.md`，做出 1-2 个 focused 修改。
**记录修改原因和预期效果。**

### 4. 执行实验（至少 3 个 capsule）
- 按新策略选择任务
- 按新策略撰写 capsule
- 提交到 EvoMap
- 记录每个 capsule 的决策结果

### 5. 计算得分
```
cycle_score = 0.5 * auto_promoted_rate + 0.3 * credit_delta_normalized + 0.2 * quality_bonus
```

### 6. 保留或回退
- cycle_score > 上期 → 保留策略修改，git commit
- cycle_score ≤ 上期 → 回退策略修改，git reset
- 记录到 results.tsv

### 7. 沉淀学习
将周期内的发现写入 `.learnings/LEARNINGS.md`

### 8. 循环 ↑

---

## 简洁性原则

- 小改进 + 大量复杂 = 不值得
- 删除某东西 + 同等结果 = 强烈鼓励（简洁性胜利）
- 所有改动权衡：收益是否值得复杂度代价

## 实验纪律

1. **每次只改 1-2 个变量** — 不要同时改策略、改内容格式、改任务选择
2. **至少 3 个样本才能下结论** — 1 个 capsule 的 auto_promoted 可能是运气
3. **crash 不是失败，是数据** — 记录为什么失败，避免重复
4. **小胜利累积** — 不要追求一步到 100 rep，追求每次 +1-2

## 两种进化模式

### 模式 A：自由探索（当前模式）
- 适用：无固定目标，"尽可能变强"
- 可调：strategy.md + params.md + SOUL.md + AGENTS.md
- 周期：3 个 capsule
- 指标：cycle_score（多维）

### 模式 B：目标冲刺（固定目标任务）
- 适用：有明确目标，如"把 auto_promoted 率从 90% 提到 95%"
- 只改：strategy.md（其他配置锁定）
- 周期：直到目标达成或连续 5 个周期无改进
- 指标：单一目标指标（如 auto_promoted 率）
- 参考：Karpathy autoresearch 的 program.md 设计

**切换条件**：当用户给出明确量化目标时，从模式 A 切换到模式 B。

## 禁区（最小化）

- ❌ 不修改 `program.md` 自身的循环规则（避免元规则无限嵌套）
- ❌ 不发送未经验证的 capsule（宁可少发，不要 rejected）
- ❌ 不在单个周期内尝试超过 2 个策略变更

## 可调优的配置文件

以下文件**可以**在进化周期内微调（但每次只改一个）：

| 文件 | 可调范围 | 调优示例 |
|------|---------|---------|
| `strategy.md` | 任务选择、内容生成、信号策略 | 每个周期都可以改 |
| `params.md` | 行为参数（风险、质量、主动性等） | 调高 risk_tolerance 看效果 |
| `SOUL.md` | 语气、决策风格、风险偏好 | 依据 params 调整具体措辞 |
| `AGENTS.md` | 心跳行为、记忆策略、主动工作规则 | 依据 params 调整规则 |
| `TOOLS.md` | 工具配置、镜像列表、代理设置 | 更新 Z-Library 镜像 |

**参数流**: `params.md`（数值参数）→ `SOUL.md` / `AGENTS.md`（具体实现）
类比 autoresearch：`train.py` 顶部的超参数常量 → 下面的模型实现代码。

**纪律**：每个周期最多调整 1 个配置文件。策略优先，其他文件只在有明确证据表明需要调整时才动。
