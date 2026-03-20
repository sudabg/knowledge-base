# 网络超时与重试

处理网络不稳定和API超时

## GitHub push超时重试
- **来源**: 实测经验
- **状态**: verified
- **用途**: 网络慢时设yieldMs=55000，用gh auth setup-git替代token认证
- **置信度**: high

## EvoMap心跳限流
- **来源**: 2026-03-17
- **状态**: verified
- **用途**: HTTP 429时等retry_after_ms（通常5分钟）
- **置信度**: high

## GitHub代理加速
- **来源**: TOOLS.md
- **状态**: verified
- **用途**: https://ghfast.top/前缀加速clone/push
- **置信度**: high

