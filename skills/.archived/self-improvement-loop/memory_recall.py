#!/usr/bin/env python3
"""
跨会话记忆召回：FTS5 + 语义搜索双重召回。
高频知识点自动提升，低价值内容自动归档。
"""

import os
import re
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
MEMORY_DIR = WORKSPACE / "memory"
DB_PATH = WORKSPACE / ".learnings" / "memory_index.db"
MEMORY_MD = WORKSPACE / "MEMORY.md"
ARCHIVE_MD = MEMORY_DIR / "archive.md"

# 知识点频率阈值
PROMOTION_THRESHOLD = 3  # 出现3次以上提升到 MEMORY.md
ARCHIVE_THRESHOLD_DAYS = 60  # 60天前的内容考虑归档

def get_db_connection():
    """获取数据库连接。"""
    if not DB_PATH.exists():
        print("数据库不存在，请先运行 enhanced_memory.py index")
        return None
    return sqlite3.connect(str(DB_PATH))

def search_fts5(query, limit=20):
    """FTS5 全文搜索。"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT me.file_path, me.content, me.entry_type, me.keywords
        FROM memory_fts
        JOIN memory_entries me ON me.id = memory_fts.rowid
        WHERE memory_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "file_path": row[0],
            "content": row[1][:500],
            "entry_type": row[2],
            "keywords": json.loads(row[3]) if row[3] else [],
        })

    conn.close()
    return results

def extract_high_frequency_knowledge(days=30):
    """提取高频知识点。"""
    knowledge_counter = Counter()
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        file_path = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"

        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")

        # 提取知识点：标题、列表项、特殊标记
        patterns = [
            r'^#{1,3}\s+(.+)$',           # 标题
            r'^[-*]\s+(.+)$',              # 列表项
            r'【(.+?)】',                   # 中括号标记
            r'\*\*(.+?)\*\*',              # 粗体
            r'教训[：:]\s*(.+)',           # 教训
            r'规则[：:]\s*(.+)',           # 规则
            r'发现[：:]\s*(.+)',           # 发现
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                knowledge = match.group(1).strip()
                if 5 < len(knowledge) < 100:  # 过滤太短或太长的
                    knowledge_counter[knowledge] += 1

    return knowledge_counter

def promote_to_memory(knowledge_counter):
    """将高频知识点提升到 MEMORY.md。"""
    promoted = []

    for knowledge, count in knowledge_counter.most_common(20):
        if count >= PROMOTION_THRESHOLD:
            # 检查是否已在 MEMORY.md 中
            if MEMORY_MD.exists():
                content = MEMORY_MD.read_text(encoding="utf-8")
                if knowledge in content:
                    continue

            # 提升到 MEMORY.md
            promoted.append({
                "knowledge": knowledge,
                "count": count,
                "action": "promote",
            })

    return promoted

def archive_low_value(days=60):
    """归档低价值内容。"""
    archived = []
    threshold_date = datetime.now() - timedelta(days=days)

    for file_path in MEMORY_DIR.glob("*.md"):
        if file_path.name.startswith("."):
            continue

        match = re.match(r'(\d{4}-\d{2}-\d{2})\.md', file_path.name)
        if not match:
            continue

        file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        if file_date < threshold_date:
            content = file_path.read_text(encoding="utf-8")

            # 只保留有价值的内容
            valuable_lines = []
            for line in content.split("\n"):
                line = line.strip()
                # 保留标题、教训、规则、错误记录
                if any([
                    line.startswith("#"),
                    "教训" in line,
                    "规则" in line,
                    "错误" in line,
                    "失败" in line,
                    "发现" in line,
                    line.startswith("- ") and len(line) > 20,
                ]):
                    valuable_lines.append(line)

            if valuable_lines:
                archived.append({
                    "date": match.group(1),
                    "lines": valuable_lines[:20],  # 最多保留20行
                })

    return archived

def generate_recall_report():
    """生成记忆召回报告。"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "high_frequency": [],
        "suggested_promotions": [],
        "suggested_archives": [],
    }

    # 提取高频知识点
    knowledge_counter = extract_high_frequency_knowledge()
    report["high_frequency"] = [
        {"knowledge": k, "count": c}
        for k, c in knowledge_counter.most_common(10)
    ]

    # 建议提升
    report["suggested_promotions"] = promote_to_memory(knowledge_counter)

    # 建议归档
    report["suggested_archives"] = archive_low_value()

    return report

def main():
    """主函数。"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "recall":
            report = generate_recall_report()
            print("记忆召回报告:")
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif command == "search":
            if len(sys.argv) > 2:
                results = search_fts5(sys.argv[2])
                for r in results:
                    print(f"[{r['entry_type']}] {r['file_path']}")
                    print(f"  {r['content'][:100]}...")
                    print()
            else:
                print("用法: memory_recall.py search <query>")
        elif command == "promote":
            knowledge_counter = extract_high_frequency_knowledge()
            promotions = promote_to_memory(knowledge_counter)
            print(f"建议提升 {len(promotions)} 个知识点到 MEMORY.md")
            for p in promotions:
                print(f"  - {p['knowledge']} (出现 {p['count']} 次)")
        elif command == "archive":
            archives = archive_low_value()
            print(f"建议归档 {len(archives)} 个旧文件")
            for a in archives:
                print(f"  - {a['date']} ({len(a['lines'])} 行)")
        else:
            print(f"未知命令: {command}")
    else:
        print("用法:")
        print("  python3 memory_recall.py recall    # 生成召回报告")
        print("  python3 memory_recall.py search <query>  # 搜索记忆")
        print("  python3 memory_recall.py promote  # 建议提升知识点")
        print("  python3 memory_recall.py archive  # 建议归档旧内容")

if __name__ == "__main__":
    main()
