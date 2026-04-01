#!/usr/bin/env python3
"""
技能生成器：从检测到的任务模式自动生成技能文件。
兼容 agentskills.io 格式。
"""

import os
import json
from datetime import datetime
from pathlib import Path
import hashlib

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
TRACKER_FILE = WORKSPACE / ".learnings" / "task_patterns.json"
SKILLS_DIR = WORKSPACE / "skills"
IMPROVEMENT_LOG = WORKSPACE / ".learnings" / "skill_improvements.json"

SKILL_TEMPLATE = """# {skill_name}

## 触发条件
{trigger_description}

## 功能描述
自动执行以下任务模式：{pattern_summary}

## 执行步骤
{steps}

## 验证方法
{verification}

## 踩坑记录
{pitfalls}

## 置信度
{confidence}/10 （基于 {occurrences} 次重复执行）

## 元数据
- 生成时间：{created_at}
- 基于任务：{source_tasks}
- 改进次数：{improvement_count}
- agentskills.io 兼容：是
"""

def load_patterns():
    """加载检测到的任务模式。"""
    if not TRACKER_FILE.exists():
        return []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_skill_name(keywords):
    """从关键词生成技能名称。"""
    # 优先使用高权重关键词
    priority = ["EvoMap", "capsule", "博客", "飞书", "GitHub", "知识库"]
    for kw in priority:
        if kw in keywords:
            return f"auto-{kw.lower()}-helper"

    # 使用前两个关键词
    if len(keywords) >= 2:
        return f"auto-{keywords[0].lower()}-{keywords[1].lower()}"
    elif keywords:
        return f"auto-{keywords[0].lower()}-task"
    return f"auto-task-{datetime.now().strftime('%H%M%S')}"

def generate_steps(task_texts):
    """从任务文本生成执行步骤。"""
    steps = []
    for i, text in enumerate(task_texts[:5], 1):
        steps.append(f"{i}. {text}")
    return "\n".join(steps)

def calculate_confidence(occurrences):
    """计算技能置信度。"""
    if occurrences >= 10:
        return 9
    elif occurrences >= 5:
        return 7
    elif occurrences >= 3:
        return 5
    return 3

def generate_skill(pattern):
    """从模式生成技能内容。"""
    keywords = pattern["keywords"]
    skill_name = generate_skill_name(keywords)
    occurrences = pattern["occurrences"]
    task_texts = pattern["tasks"]

    # 检查是否已存在
    skill_dir = SKILLS_DIR / skill_name
    if skill_dir.exists():
        return None, "技能已存在"

    # 生成技能内容
    content = SKILL_TEMPLATE.format(
        skill_name=skill_name.replace("-", " ").title(),
        trigger_description=f"当用户执行包含关键词 {', '.join(keywords[:5])} 的任务时触发",
        pattern_summary=f"涉及 {', '.join(keywords[:3])} 的重复任务",
        steps=generate_steps(task_texts),
        verification="检查任务执行结果，确认输出符合预期",
        pitfalls="暂无踩坑记录（自动创建，需人工补充）",
        confidence=calculate_confidence(occurrences),
        occurrences=occurrences,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source_tasks=f"{occurrences} 次重复任务",
        improvement_count=0,
    )

    # 创建技能目录
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content, encoding="utf-8")

    # 创建改进记录
    improvement = {
        "skill": skill_name,
        "created_at": datetime.now().isoformat(),
        "improvements": [],
        "success_rate": None,
        "last_used": None,
    }

    return skill_name, improvement

def update_improvement_log(skill_name, improvement):
    """更新技能改进日志。"""
    IMPROVEMENT_LOG.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    if IMPROVEMENT_LOG.exists():
        with open(IMPROVEMENT_LOG, "r", encoding="utf-8") as f:
            logs = json.load(f)

    # 查找或创建记录
    found = False
    for log in logs:
        if log["skill"] == skill_name:
            log.update(improvement)
            found = True
            break

    if not found:
        logs.append(improvement)

    with open(IMPROVEMENT_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def main():
    """主函数：从模式生成技能。"""
    patterns = load_patterns()

    if not patterns:
        print("没有检测到的任务模式。请先运行 task_tracker.py")
        return

    print(f"从 {len(patterns)} 个模式生成技能...")
    generated = 0

    for pattern in patterns:
        skill_name, result = generate_skill(pattern)
        if skill_name:
            update_improvement_log(skill_name, result)
            print(f"  ✅ 创建技能: {skill_name}")
            generated += 1
        else:
            print(f"  ⏭️ 跳过: {result}")

    print(f"\n生成完成：{generated} 个新技能")
    print(f"技能目录: {SKILLS_DIR}")
    print(f"改进日志: {IMPROVEMENT_LOG}")

if __name__ == "__main__":
    main()
