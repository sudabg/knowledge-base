# Token 消耗优化

减少不必要的token消耗

## 删除禁用skill entries
- **来源**: 2026-03-17教训
- **状态**: verified
- **用途**: config中enabled:false的skill仍注入system prompt，每消息浪费3-4KB
- **置信度**: certain

## 精简文件上下文
- **来源**: AGENTS.md教训
- **状态**: verified
- **用途**: 删群聊规则/不用的TTS/空示例，死守800Token内部开销底线
- **置信度**: certain

## /new重置会话
- **来源**: OpenClaw文档
- **状态**: verified
- **用途**: 长会话后/new减少上下文token，但本身也消耗token不滥用
- **置信度**: high

## Git Diff自评替代全文审计
- **来源**: 进化方案v2.0
- **状态**: verified
- **用途**: git diff --stat替代完整文件审计，450 tokens vs 5000+
- **置信度**: high

## Block Attention策略记忆
- **来源**: autoevolve v0.1.3
- **状态**: verified
- **用途**: 只存储结构化摘要而非完整轨迹
- **置信度**: high

