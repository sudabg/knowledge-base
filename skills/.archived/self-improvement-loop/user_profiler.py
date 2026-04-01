#!/usr/bin/env python3
"""
用户画像系统：从对话中提取偏好、习惯、需求模式。
构建跨会话的深度用户模型。
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
MEMORY_DIR = WORKSPACE / "memory"
PROFILE_FILE = MEMORY_DIR / "user_profile.json"

# 用户画像模板
PROFILE_TEMPLATE = {
    "user_id": "一条明",
    "created_at": None,
    "last_updated": None,
    "preferences": {
        "communication_style": {
            "preferred_language": "zh",
            "response_style": "concise",  # concise | detailed
            "emoji_usage": "moderate",    # none | light | moderate | heavy
            "format_preference": "structured",  # freeform | structured | mixed
        },
        "topics_of_interest": [],
        "tools_used": [],
        "time_patterns": {
            "active_hours": [],
            "preferred_meeting_times": [],
        },
    },
    "work_patterns": {
        "common_tasks": [],
        "project_focus": [],
        "decision_style": "data_driven",  # intuitive | data_driven | collaborative
    },
    "learning_style": {
        "prefers_examples": True,
        "prefers_explanations": True,
        "prefers_visuals": False,
        "attention_span": "medium",  # short | medium | long
    },
    "feedback_history": {
        "positive_signals": [],
        "negative_signals": [],
        "suggestions": [],
    },
    "interaction_stats": {
        "total_conversations": 0,
        "total_messages": 0,
        "avg_response_length": 0,
        "topics_frequency": {},
    },
}

def load_profile():
    """加载用户画像。"""
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return PROFILE_TEMPLATE.copy()

def save_profile(profile):
    """原子化保存用户画像。"""
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = PROFILE_FILE.with_suffix(".tmp")

    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    tmp_file.rename(PROFILE_FILE)

def analyze_conversation(content):
    """分析对话内容，提取用户特征。"""
    features = {
        "topics": [],
        "preferences": {},
        "feedback_signals": [],
    }

    # 提取话题
    topic_patterns = {
        "EvoMap": r'EvoMap|capsule|进化',
        "GitHub": r'GitHub|PR|commit|仓库',
        "飞书": r'飞书|文档|日历|多维表格',
        "博客": r'博客|文章|发布|写作',
        "技术": r'Python|代码|脚本|开发|技术',
        "学习": r'学习|论文|阅读|研究|理解',
        "项目": r'项目|任务|计划|目标|进度',
        "部署": r'部署|服务器|Docker|容器|运行',
    }

    for topic, pattern in topic_patterns.items():
        if re.search(pattern, content):
            features["topics"].append(topic)

    # 提取反馈信号
    if re.search(r'好|不错|满意|👍|✅|赞', content):
        features["feedback_signals"].append("positive")
    if re.search(r'差|不行|问题|❌|错误|失败', content):
        features["feedback_signals"].append("negative")

    # 提取偏好
    if re.search(r'简洁|精简|短一点|简短', content):
        features["preferences"]["response_style"] = "concise"
    if re.search(r'详细|完整|深入|全面|具体', content):
        features["preferences"]["response_style"] = "detailed"

    return features

def update_profile(profile, features):
    """根据分析结果更新用户画像。"""
    if not profile["created_at"]:
        profile["created_at"] = datetime.now().isoformat()

    profile["last_updated"] = datetime.now().isoformat()

    # 更新话题
    for topic in features["topics"]:
        if topic not in profile["preferences"]["topics_of_interest"]:
            profile["preferences"]["topics_of_interest"].append(topic)

    # 更新话题频率
    for topic in features["topics"]:
        if topic not in profile["interaction_stats"]["topics_frequency"]:
            profile["interaction_stats"]["topics_frequency"][topic] = 0
        profile["interaction_stats"]["topics_frequency"][topic] += 1

    # 更新反馈信号
    for signal in features["feedback_signals"]:
        key = "positive_signals" if signal == "positive" else "negative_signals"
        profile["feedback_history"][key].append({
            "timestamp": datetime.now().isoformat(),
            "context": ", ".join(features["topics"]),
        })

    # 更新偏好
    if "response_style" in features["preferences"]:
        profile["preferences"]["communication_style"]["response_style"] = features["preferences"]["response_style"]

    return profile

def analyze_daily_files(days=7):
    """分析最近N天的记忆文件。"""
    profile = load_profile()
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        file_path = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"

        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            features = analyze_conversation(content)
            profile = update_profile(profile, features)

    save_profile(profile)
    return profile

def get_user_summary():
    """获取用户画像摘要。"""
    profile = load_profile()

    summary = {
        "topics_of_interest": profile["preferences"]["topics_of_interest"][:10],
        "response_style": profile["preferences"]["communication_style"]["response_style"],
        "total_conversations": profile["interaction_stats"]["total_conversations"],
        "top_topics": sorted(
            profile["interaction_stats"]["topics_frequency"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5],
    }

    return summary

def main():
    """主函数。"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "analyze":
            profile = analyze_daily_files()
            print(f"用户画像已更新: {PROFILE_FILE}")
            print(f"兴趣话题: {', '.join(profile['preferences']['topics_of_interest'][:10])}")
            print(f"回复风格: {profile['preferences']['communication_style']['response_style']}")
        elif command == "summary":
            summary = get_user_summary()
            print("用户画像摘要:")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(f"未知命令: {command}")
    else:
        print("用法:")
        print("  python3 user_profiler.py analyze  # 分析并更新画像")
        print("  python3 user_profiler.py summary  # 获取画像摘要")

if __name__ == "__main__":
    main()
