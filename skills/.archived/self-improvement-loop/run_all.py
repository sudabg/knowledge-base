#!/usr/bin/env python3
"""
运行自改进学习闭环的所有组件。
"""

import os
import sys
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def run_enhanced_memory():
    """运行增强记忆系统。"""
    print("=== 增强记忆系统 ===")
    from enhanced_memory import index_memory_files, compress_old_memories

    print("1. 建立索引...")
    indexed = index_memory_files()

    print("2. 压缩旧记忆...")
    compressed = compress_old_memories(days_threshold=30)

    print(f"完成：索引 {indexed} 个文件，压缩 {compressed} 个文件\n")

def run_user_profiler():
    """运行用户画像系统。"""
    print("=== 用户画像系统 ===")
    from user_profiler import analyze_daily_files, get_user_summary

    print("1. 分析对话记录...")
    profile = analyze_daily_files(days=7)

    print("2. 获取画像摘要...")
    summary = get_user_summary()

    print(f"兴趣话题: {', '.join(summary['topics_of_interest'][:5])}")
    print(f"回复风格: {summary['response_style']}")
    print(f"对话次数: {summary['total_conversations']}")
    print()

def run_memory_recall():
    """运行跨会话记忆召回。"""
    print("=== 跨会话记忆召回 ===")
    from memory_recall import generate_recall_report, search_fts5

    print("1. 生成召回报告...")
    report = generate_recall_report()

    print(f"高频知识点: {len(report['high_frequency'])} 个")
    print(f"建议提升: {len(report['suggested_promotions'])} 个")
    print(f"建议归档: {len(report['suggested_archives'])} 个")

    if report['high_frequency']:
        print("\nTop 5 高频知识点:")
        for item in report['high_frequency'][:5]:
            print(f"  - {item['knowledge']} ({item['count']} 次)")

    print()

def main():
    """主函数：运行所有组件。"""
    print("🦞 自改进学习闭环 - 全面运行\n")

    try:
        run_enhanced_memory()
    except Exception as e:
        print(f"增强记忆系统错误: {e}\n")

    try:
        run_user_profiler()
    except Exception as e:
        print(f"用户画像系统错误: {e}\n")

    try:
        run_memory_recall()
    except Exception as e:
        print(f"跨会话记忆召回错误: {e}\n")

    print("✅ 自改进学习闭环运行完成")

if __name__ == "__main__":
    main()
