#!/usr/bin/env python3
"""
增强记忆系统：为 memory 文件建立 SQLite 全文索引。
实现原子化写入和记忆压缩。
"""

import os
import re
import sqlite3
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
MEMORY_DIR = WORKSPACE / "memory"
DB_PATH = WORKSPACE / ".learnings" / "memory_index.db"
COMPRESSED_DIR = MEMORY_DIR / "compressed"

def init_database():
    """初始化 SQLite 数据库和 FTS5 索引。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 创建主表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            content TEXT NOT NULL,
            entry_type TEXT,  -- task, insight, decision, learning
            keywords TEXT,    -- JSON array
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # 创建 FTS5 虚拟表
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
            content,
            keywords,
            content='memory_entries',
            content_rowid='id'
        )
    """)

    # 创建触发器保持同步
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory_entries BEGIN
            INSERT INTO memory_fts(rowid, content, keywords)
            VALUES (new.id, new.content, new.keywords);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory_entries BEGIN
            INSERT INTO memory_fts(memory_fts, rowid, content, keywords)
            VALUES ('delete', old.id, old.content, old.keywords);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory_entries BEGIN
            INSERT INTO memory_fts(memory_fts, rowid, content, keywords)
            VALUES ('delete', old.id, old.content, old.keywords);
            INSERT INTO memory_fts(rowid, content, keywords)
            VALUES (new.id, new.content, new.keywords);
        END
    """)

    conn.commit()
    return conn

def extract_keywords(text):
    """从文本提取关键词。"""
    # 提取中文关键词
    cn_keywords = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    # 提取英文关键词
    en_keywords = re.findall(r'\b[A-Za-z]{3,}\b', text)
    # 提取特殊标记
    special = re.findall(r'#[\w-]+|@[\w-]+|https?://\S+', text)

    all_keywords = list(set(cn_keywords[:10] + en_keywords[:10] + special[:5]))
    return json.dumps(all_keywords, ensure_ascii=False)

def classify_entry(text):
    """分类记忆条目类型。"""
    patterns = {
        "task": [r'任务', r'执行', r'运行', r'完成', r'发布'],
        "insight": [r'发现', r'学习', r'认识到', r'理解'],
        "decision": [r'决定', r'选择', r'确定', r'改为'],
        "learning": [r'教训', r'经验', r'踩坑', r'注意'],
    }

    for entry_type, pats in patterns.items():
        for pat in pats:
            if re.search(pat, text):
                return entry_type

    return "general"

def index_memory_files():
    """为所有 memory 文件建立索引。"""
    conn = init_database()
    cursor = conn.cursor()

    indexed = 0
    skipped = 0

    for file_path in MEMORY_DIR.glob("*.md"):
        if file_path.name.startswith("."):
            continue

        # 检查是否已索引
        cursor.execute("SELECT COUNT(*) FROM memory_entries WHERE file_path = ?", (str(file_path),))
        if cursor.fetchone()[0] > 0:
            skipped += 1
            continue

        content = file_path.read_text(encoding="utf-8")
        keywords = extract_keywords(content)
        entry_type = classify_entry(content)

        cursor.execute("""
            INSERT INTO memory_entries (file_path, content, entry_type, keywords, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(file_path),
            content,
            entry_type,
            keywords,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
        ))

        indexed += 1

    conn.commit()
    conn.close()

    print(f"索引完成：{indexed} 个新文件，{skipped} 个已存在")
    return indexed

def search_memory(query, limit=10):
    """使用 FTS5 搜索记忆。"""
    conn = init_database()
    cursor = conn.cursor()

    # FTS5 搜索
    cursor.execute("""
        SELECT me.file_path, me.content, me.entry_type, me.keywords,
               rank
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
            "content": row[1][:500],  # 截断
            "entry_type": row[2],
            "keywords": json.loads(row[3]) if row[3] else [],
            "rank": row[4],
        })

    conn.close()
    return results

def compress_old_memories(days_threshold=30):
    """压缩旧记忆：从 daily files 提取高频知识点。"""
    COMPRESSED_DIR.mkdir(parents=True, exist_ok=True)

    threshold_date = datetime.now() - timedelta(days=days_threshold)
    compressed_count = 0

    for file_path in MEMORY_DIR.glob("*.md"):
        if file_path.name.startswith("."):
            continue

        # 从文件名提取日期
        match = re.match(r'(\d{4}-\d{2}-\d{2})\.md', file_path.name)
        if not match:
            continue

        file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        if file_date < threshold_date:
            # 提取高频知识点
            content = file_path.read_text(encoding="utf-8")
            insights = extract_insights(content)

            if insights:
                # 原子化写入
                compressed_file = COMPRESSED_DIR / f"{match.group(1)}-compressed.md"
                tmp_file = compressed_file.with_suffix(".tmp")

                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(f"# 压缩记忆 - {match.group(1)}\n\n")
                    f.write("\n\n".join(insights))

                tmp_file.rename(compressed_file)
                compressed_count += 1

    print(f"压缩完成：{compressed_count} 个文件")
    return compressed_count

def extract_insights(content):
    """从内容中提取高频知识点。"""
    insights = []

    # 提取标题和列表项
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("#") or line.startswith("-") or line.startswith("*"):
            if len(line) > 10:  # 过滤太短的行
                insights.append(line)

    return insights[:10]  # 最多保留10条

def main():
    """主函数。"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "index":
            index_memory_files()
        elif command == "search":
            if len(sys.argv) > 2:
                results = search_memory(sys.argv[2])
                for r in results:
                    print(f"[{r['entry_type']}] {r['file_path']}")
                    print(f"  {r['content'][:100]}...")
                    print()
            else:
                print("用法: enhanced_memory.py search <query>")
        elif command == "compress":
            compress_old_memories()
        else:
            print(f"未知命令: {command}")
    else:
        print("用法:")
        print("  python3 enhanced_memory.py index    # 建立索引")
        print("  python3 enhanced_memory.py search <query>  # 搜索")
        print("  python3 enhanced_memory.py compress # 压缩旧记忆")

if __name__ == "__main__":
    main()
