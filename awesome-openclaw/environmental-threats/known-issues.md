# 已知环境威胁 🚨

## Threat 1: 禁用 Skill Entries 注入
- **发现日期**: 2026-03-17
- **症状**: 每条消息多烧 3-4KB tokens
- **原因**: `skills.entries` 中 `enabled: false` 的 skill 仍被注入 system prompt
- **修复**: `config.patch: {"skills":{"entries":{}}}`
- **状态**: ✅ 已修复
- **验证**: `grep -c "enabled: false" openclaw.json` 应返回 0

## Threat 2: GitHub Token 过期
- **发现日期**: 2026-03-14
- **症状**: `git push` 报 "Authentication failed"
- **原因**: 内嵌 token 过期
- **修复**: `gh auth setup-git` 后重试
- **状态**: ✅ 已有解决方案
- **频率**: 约每周一次

## Threat 3: EvoMap 心跳限流
- **发现日期**: 2026-03-17
- **症状**: HTTP 429 from heartbeat API
- **原因**: 心跳间隔 < 5 分钟
- **修复**: 等待 retry_after_ms 后重试
- **状态**: ⚠️ 需要遵守间隔
- **影响**: 节点 last_seen 仍然正常，不影响在线状态

## Threat 4: pyproject.toml build-backend 错误
- **发现日期**: 2026-03-17
- **症状**: `pip install -e .` 报 BackendUnavailable
- **原因**: `setuptools.backends._legacy:_Backend` 不存在
- **修复**: 改为 `setuptools.build_meta`
- **状态**: ✅ 已修复
- **影响范围**: autoevolve, evomap-sdk 等自建 Python 包
