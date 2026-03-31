# HEARTBEAT.md — 后台模式（2026-03-29 调度改造）

## ⚡ 核心原则
心跳不再是"每小时的主角"，而是后台轻量检查。
每次心跳只做必须的维护，其余时间全部用于高通量任务执行。

## 📋 后台检查清单（≤2 分钟完成）

### 1. EvoMap 心跳（静默）
```bash
python3 scripts/evomap_a2a.py heartbeat 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'OK credit={d.get(\"credit_balance\",0)} tasks={len(d.get(\"available_tasks\",[]))}')
except: print('FAIL')
"
```
- 成功 → 记录到 `.learnings/heartbeat_state.json`，不输出
- 失败 → 记录错误计数，连续 3 次才报告

### 2. Pending capsule 发布（有则执行）
```bash
for f in .learnings/pending_capsule*.json; do
  [ -f "$f" ] && python3 scripts/evomap_a2a.py publish --bundle "$f" 2>&1 | grep -q "ok\|auto_promoted" && rm "$f"
done
```
- 成功 → 删除 pending 文件
- 失败 → 保留，下次重试，不阻塞

### 3. 任务队列推进
- 如果当前有高通量任务在执行 → 跳过，不打断
- 如果空闲 → 从 `memory/long-term-goals.md` 检查今日目标完成情况，优先推进长期目标

### 4. 长期目标推进（每日至少1次）
- 读取 `memory/long-term-goals.md`
- 检查今日是否为目标做了贡献
- 如果没有 → 立即执行一个推进动作
- 记录结果

### 4. 每日博客写作（每日 1 次，晚间）
- 条件：今日有质量≥8的任务 + 距上次发文≥1天
- 流程：
  1. 读取 `memory/YYYY-MM-DD.md` 筛选高质量任务
  2. 用 `blog-writer` skill 的选题策略选题
  3. 写 Markdown 文章到 `blog/posts/YYYY-MM-DD-slug.md`
  4. 运行 `python3 blog/generate.py` 生成静态页面
  5. 验证 `curl -s http://localhost:8081/ | head -5`
- 如果今日无合适选题 → 跳过，不强写

### 5. 环境健康（每日 1 次）
- 仅在每日首次心跳时运行 `bash audits/daily-health.sh`
- 其他时间跳过

### 6. 自改进学习闭环（每日 1 次，晚间）
```bash
python3 skills/self-improvement-loop/run_all.py
```
- 运行增强记忆系统（建立索引、压缩旧记忆）
- 运行用户画像系统（分析对话、更新画像）
- 运行跨会话记忆召回（高频知识点提升、低价值内容归档）
- 结果记录到 `.learnings/self_improvement.json`

### 7. 技能自动发现（每日 1 次，晚间）
```bash
python3 skills/auto-skill-creator/task_tracker.py
python3 skills/auto-skill-creator/skill_generator.py
```
- 检测重复任务模式（≥3次相似任务）
- 自动生成新技能到 skills/ 目录
- 结果记录到 `.learnings/task_patterns.json`

### 8. 上下文压缩（每日 1 次，晚间）
```bash
python3 skills/self-improvement-loop/context_compressor.py compress
```
- 压缩 30 天前的记忆文件
- 生成最近 7 天的上下文摘要
- 结果记录到 `.learnings/context_cache/`

### 9. Hermes 集成监控（全天，每小时 1 次）
```bash
python3 skills/self-improvement-loop/monitor.py check
```
- 检查模块导入状态
- 测试功能可用性
- 运行单元测试
- 记录健康日志
- 发现问题立即优化

## 🚫 不再做的事
- 不再每次心跳都跑 task_manager.py
- 不再每次心跳都跑 sync_dashboard.py
- 不再每次心跳都跑 sync_completed_tasks.py
- 不再每次心跳都输出详细报告

## 📊 状态报告
- 每 6 小时汇总一次（或任务完成时批量汇报）
- 异常时立即报告
- 正常运行时完全静默

## 🔄 自动触发
当 HEARTBEAT.md 被读取时，执行上述后台检查。
如无异常，回复 HEARTBEAT_OK。
