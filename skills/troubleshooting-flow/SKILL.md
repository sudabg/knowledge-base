---
name: troubleshooting-flow
description: >
  遇到资源/权限/API卡点时的标准化故障排除流程。当token缺失、API限流、权限不足、工具不可用时使用。
  触发词：卡住了、搞不定、报错、权限不足、token过期、限流、找不到方法、搜替代工具、troubleshoot
---

# 故障排除流程

## 核心原则
外部资源缺失不等于无解。遇到卡点第一步是搜替代方案，不是等指令。

## 决策树

```
卡点出现
├─ 1. 判断卡点类型
│  ├─ Token/凭证缺失 → 跳到 2a
│  ├─ API限流/503 → 跳到 2b
│  ├─ 权限不足 → 跳到 2c
│  └─ 工具/功能不存在 → 跳到 2d
│
├─ 2a. Token缺失流程
│  ├─ 搜索 CLI 替代: `skillhub search <平台名> cli` 或 `clawhub search <平台名>`
│  ├─ 搜开源wrapper: 网搜 `<平台名> automation tool cli`
│  ├─ 搜browser automation: 检查已有 skills（camofox/browser-automation）
│  └─ 测试→记录到 TOOLS.md
│
├─ 2b. API限流流程
│  ├─ 检查是否全局宕机（读端点GET测试）
│  ├─ 写端点限流但读正常 → 保存pending，暂停写入，执行替代任务
│  ├─ 全局宕机 → 记录，等待恢复
│  └─ 记录退避策略到日志
│
├─ 2c. 权限不足流程
│  ├─ 检查是否有绕过方案（用户身份 vs 机器人身份）
│  ├─ 搜替代API端点
│  └─ 不可绕过 → 告知用户需要开通权限
│
├─ 2d. 功能不存在流程
│  ├─ skillhub search → clawhub search
│  ├─ 网搜开源工具
│  ├─ 考虑自己实现（评估复杂度）
│  └─ 太复杂 → 记录 FEATURE_REQUESTS.md
│
└─ 3. 沉淀经验
   ├─ 成功解决 → 更新 TOOLS.md + 写日志
   └─ 未解决 → 记录到 .learnings/ERRORS.md + 告知用户
```

## 搜索优先级
1. `skillhub search <关键词>` （cn-optimized，优先）
2. `clawhub search <关键词>` （公开registry）
3. 网搜：`<关键词> cli tool github`
4. 浏览器自动化：camofox 直接操作

## 踩坑记录
- 不要连续用同一方法重试3次以上——换路径
- "没token=无法操作"是思维定式——总有替代方案
- 503不一定是全局宕机——先测读端点再判断
