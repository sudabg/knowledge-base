# HEARTBEAT.md — 简化版（2026-03-20 调整后）

## 🔹 看板健康度自检（每次 heartbeat 运行）
- ✅ 执行: `python3 dashboard-health-monitor.py`
- ⚠️ 自动修复: 发现 missing_project_plan / sync_failed / heartbeat_stale 立即自愈
- 📝 记录: `.learnings/dashboard_health.log`
- ⏰ 注意: 不要在此步骤阻塞， failures 会记录但 continue

## 💚 EvoMap 心跳
- ✅ 执行: `python3 autoresearch/adaptive_heartbeat.py`
- ✅ 同步: `python3 autoresearch/sync_dashboard.py`
- ✅ 任务同步: `python3 dashboard/sync_completed_tasks.py`
- 📊 报告: credit_balance, available_tasks
- 💾 写入: `.learnings/last_heartbeat.json`

## 📅 环境健康（每日一次，跳过 if 已检查）
- ✅ 执行: `bash audits/daily-health.sh`
- 📈 分数 < 85 → 记录到 memory/YYYY-MM-DD.md

## 📦 归档（有新完成任务时）
- ✅ `python3 dashboard/archive_completed.py`

## 🦀 EvoMap 进化（有高bounty任务时）
- 🔍 搜 arXiv → 生成 capsule → 发布 → 记录到 StrategyMemory

## 🔄 短期任务进化循环（每次 heartbeat 检查）
- ✅ 执行: `python3 scripts/task_manager.py`
- 功能: 同步完成标记 → 归档项目 → 进化循环生成新任务（三合一）
- 注意: 用 --dry-run 测试，不加参数才写入
- 失败只记录不报错

## 🚫 静默运行规则
- ⏰ **成功时**: 不发送消息到聊天窗口
- ⚠️ **异常时**: 仅报告错误、不一致、修复失败
- 📊 **正常报告**: 每6小时发送一次状态汇总（18:00, 0:00, 6:00, 12:00, 18:00）
- 📱 **手动触发**: 用户询问时才回复

## 📊 状态报告格式
如果需要报告：
```
✅ 心跳与同步完成（时间戳）
✅ EvoMap 状态：Credit=XX, Rep=XX, Tasks=XX
✅ Dashboard 同步：XX 个任务归档
⚠️ 发现问题：问题描述
```

## 🔄 下一次自动报告时间
最近报告: 2026-03-20 18:36
下次报告: 2026-03-20 00:00

* 设置之后请忽略此消息。正常运行时不会在聊天窗发送状态。