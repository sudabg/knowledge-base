# Auto Skill Creator

## 功能
自动检测重复任务模式并创建技能，技能在使用中自动改进。

## 触发条件
- 同一任务被执行 ≥3 次
- 发现重复的工具调用模式
- 任务完成后自动评估是否值得沉淀为技能

## 实现原理

### 1. 任务模式检测
- 监控每日任务执行记录（memory/YYYY-MM-DD.md）
- 提取任务名称、工具调用序列、结果
- 计算任务相似度（关键词+工具调用模式）

### 2. 技能自动生成
- 当检测到重复模式时，自动创建 SKILL.md
- 包含：触发条件、执行步骤、验证方法
- 兼容 agentskills.io 格式

### 3. 技能自改进
- 每次技能执行后记录结果（成功/失败/耗时）
- 当成功率 <70% 时自动优化技能描述
- 添加踩坑记录和变体处理

## 文件结构
```
auto-skill-creator/
├── SKILL.md              # 本文件
├── task_tracker.py       # 任务追踪器
├── pattern_detector.py   # 模式检测器
├── skill_generator.py    # 技能生成器
└── templates/            # 技能模板
    └── skill_template.md
```

## 使用方法
1. 在每日任务完成后运行 `python3 skills/auto-skill-creator/task_tracker.py`
2. 脚本自动分析任务模式，检测重复
3. 如检测到重复模式，自动生成技能文件夹
4. 在 HEARTBEAT.md 中添加定时执行项
