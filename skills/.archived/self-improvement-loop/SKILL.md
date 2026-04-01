# Self-Improvement Loop

## 功能
实现自改进学习闭环：增强记忆、用户画像、跨会话记忆召回。

## 核心组件

### 1. 增强记忆系统 (enhanced_memory.py)
- FTS5 索引：为 memory 文件建立 SQLite 全文索引
- 原子化写入：先写 tmp 再 rename，防止数据丢失
- 记忆压缩：定期从 daily files 提取高频知识点

### 2. 用户画像系统 (user_profiler.py)
- 结构化用户信息：从对话中提取偏好、习惯、需求模式
- 画像更新：每次对话后自动更新
- 存储位置：memory/user_profile.json

### 3. 跨会话记忆召回 (memory_recall.py)
- FTS5 + 语义搜索双重召回
- 高频知识点自动提升到 MEMORY.md
- 低价值内容自动归档到 archive.md

## 文件结构
```
self-improvement-loop/
├── SKILL.md              # 本文件
├── enhanced_memory.py    # 增强记忆系统
├── user_profiler.py      # 用户画像系统
├── memory_recall.py      # 跨会话记忆召回
└── templates/            # 模板文件
    └── user_profile_template.json
```

## 使用方法
1. 增强记忆：python3 skills/self-improvement-loop/enhanced_memory.py
2. 用户画像：python3 skills/self-improvement-loop/user_profiler.py
3. 记忆召回：python3 skills/self-improvement-loop/memory_recall.py
4. 全部运行：python3 skills/self-improvement-loop/run_all.py
