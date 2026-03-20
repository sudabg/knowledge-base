---
name: dev-rigor
description: Use when implementing features, fixing bugs, or claiming work is complete. Enforces systematic debugging, test-first development, and evidence-before-claims. Inspired by Superpowers (obra/superpowers, 89K⭐).
---

# Dev Rigor — 开发严谨性

> "完成任务 ≠ 完成工作。验证、归档、同步才是真正的完成。"

## Three Iron Laws

```
1. NO FIXES WITHOUT ROOT CAUSE FIRST
2. NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST  
3. NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION
```

## Phase 1: Systematic Debugging

**When:** Any bug, test failure, unexpected behavior, or error.

**铁律：不找到根因，不许修。**

```
1. READ error messages completely (stack traces, line numbers, codes)
2. REPRODUCE consistently (exact steps, every time)
3. CHECK recent changes (git diff, commits, config, deps)
4. GATHER evidence at component boundaries (log in/out at each layer)
5. ISOLATE which component fails (binary search)
6. THEN — and only then — propose a fix
```

**红旗（立即停止）：**
- 想说"应该可以了"但没跑验证
- 已经试了3个修复都没解决 → 回到根因调查
- "看起来简单" → 简单bug也有根因
- 时间紧迫 → 系统化比乱试快

## Phase 2: Test-First Development

**When:** 实现任何新功能或修复bug。

**铁律：没有失败的测试，不许写生产代码。**

```
RED   → 写一个会失败的测试，证明问题存在
GREEN → 写最少的代码让测试通过
REFACTOR → 清理，保持测试通过
```

**Agent适用的简化版：**
1. 先定义"成功"的可验证标准（命令输出、文件存在、状态码）
2. 写验证脚本/命令，确认当前不满足标准
3. 实现功能
4. 跑验证，确认满足标准
5. 如果跳过了第2步 → 从头来过

## Phase 3: Verification Before Completion

**When:** 声称任何工作完成、修复、或通过之前。

**铁律：没有新鲜验证证据，不许说完成。**

```
Gate Function:
1. IDENTIFY: 什么命令证明这个声明？
2. RUN: 执行完整命令（新鲜、完整）
3. READ: 完整输出，检查退出码，数失败数
4. VERIFY: 输出确认声明了吗？
   - NO → 说实话，带证据
   - YES → 声明 + 附证据
5. ONLY THEN → 说完成
```

**常见声明 vs 需要的证据：**

| 声明 | 需要 | 不够 |
|------|------|------|
| 测试通过 | 测试命令输出：0 failures | 上次跑的、"应该通过" |
| 构建成功 | 构建命令：exit 0 | Linter通过 |
| Bug已修复 | 复现原始症状：通过 | 改了代码、假设修复 |
| 任务完成 | VCS diff 显示变更 | Agent报告"成功" |
| 需求满足 | 逐行检查清单 | 测试通过 |

**红旗词汇 — 立即停止：**
- "应该"、"可能"、"看起来"
- 在验证前表达满意（"完美！"、"搞定！"、"Done！"）
- 要提交/推送/PR但没跑验证
- 相信Agent的成功报告
- "就这一次不验证"

## Integration with My Workflow

### EvoMap Capsule 发布
1. 写capsule前：定义质量标准（≥500字、confidence ≥0.85、引用论文）
2. 发布前：自评分数，不达标重写
3. 发布后：确认返回auto_promoted，记录到StrategyMemory

### 代码项目（autoevolve, ai-text-audit等）
1. 改代码前：写测试/验证命令，确认当前失败
2. 改代码：最小改动让测试通过
3. 改完后：跑完整测试套件，附输出作为证据

### Bug修复
1. 先复现bug（写能触发bug的命令/脚本）
2. 调查根因（读错误、查最近改动、加日志）
3. 修复
4. 跑复现命令，确认不再触发
5. 说"修复了" + 附证据

## 与复利思维的关系

严谨性是复利的基础。
- 每个验证让下一个bug更少
- 每个测试让下一次重构更安全
- 每个根因分析让下一次调试更快

跳过验证 = 借高利贷，省5分钟，还2小时。
