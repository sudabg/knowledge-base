#!/usr/bin/env python3
"""
持久化记忆工具 - 参考 Hermes memory_tool.py

功能：
- MEMORY.md + USER.md 持久化
- 条目分隔符 §
- 字符限制
- 文件锁保证并发安全
- 注入扫描（prompt injection 检测）
- add/replace/remove/read 操作
"""

import fcntl
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
MEMORY_DIR = WORKSPACE / "memory"

ENTRY_DELIMITER = "\n§\n"

# 默认字符限制
DEFAULT_MEMORY_CHAR_LIMIT = 5000
DEFAULT_USER_CHAR_LIMIT = 3000

# 注入检测模式
_MEMORY_THREAT_PATTERNS = [
    # Prompt injection
    (r'ignore\s+(all\s+)?(previous|above|prior)\s+instructions', "prompt_injection"),
    (r'ignore\s+all\s+instructions', "prompt_injection"),
    (r'you\s+are\s+now\s+', "role_hijack"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)', "disregard_rules"),
    # Exfiltration
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_curl"),
    (r'wget\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_wget"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass|\.npmrc|\.pypirc)', "read_secrets"),
    # SSH access
    (r'authorized_keys', "ssh_backdoor"),
    (r'\$HOME/\.ssh|\~/\.ssh', "ssh_access"),
]

# 不可见字符检测
_INVISIBLE_CHARS = {
    '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
}


def _scan_memory_content(content: str) -> Optional[str]:
    """扫描记忆内容，检测注入/泄露模式。"""
    # 检查不可见 unicode
    for char in _INVISIBLE_CHARS:
        if char in content:
            return f"Blocked: content contains invisible unicode character U+{ord(char):04X} (possible injection)."

    # 检查威胁模式
    for pattern, pid in _MEMORY_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return f"Blocked: content matches threat pattern '{pid}'."

    return None


class MemoryStore:
    """持久化记忆存储。"""

    def __init__(
        self,
        memory_char_limit: int = DEFAULT_MEMORY_CHAR_LIMIT,
        user_char_limit: int = DEFAULT_USER_CHAR_LIMIT,
    ):
        self.memory_entries: List[str] = []
        self.user_entries: List[str] = []
        self.memory_char_limit = memory_char_limit
        self.user_char_limit = user_char_limit
        # 冷冻快照（系统提示用）
        self._system_prompt_snapshot: Dict[str, str] = {"memory": "", "user": ""}

    @staticmethod
    @contextmanager
    def _file_lock(path: Path):
        """文件锁，保证并发安全。"""
        lock_path = path.with_suffix(path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = open(lock_path, "w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

    @staticmethod
    def _path_for(target: str) -> Path:
        """获取目标文件路径。"""
        if target == "user":
            return MEMORY_DIR / "USER.md"
        return MEMORY_DIR / "MEMORY.md"

    @staticmethod
    def _read_file(path: Path) -> List[str]:
        """从文件读取条目。"""
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return []
        # 按分隔符分割
        entries = [e.strip() for e in content.split(ENTRY_DELIMITER) if e.strip()]
        return entries

    @staticmethod
    def _write_file(path: Path, entries: List[str]):
        """写入条目到文件。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = ENTRY_DELIMITER.join(entries)
        # 原子写入
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, delete=False, suffix=".tmp"
        ) as f:
            f.write(content)
            tmp_path = Path(f.name)
        tmp_path.replace(path)

    def load_from_disk(self):
        """从磁盘加载条目。"""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

        self.memory_entries = self._read_file(self._path_for("memory"))
        self.user_entries = self._read_file(self._path_for("user"))

        # 去重（保持顺序）
        self.memory_entries = list(dict.fromkeys(self.memory_entries))
        self.user_entries = list(dict.fromkeys(self.user_entries))

        # 捕获冷冻快照
        self._system_prompt_snapshot = {
            "memory": self._render_block("memory", self.memory_entries),
            "user": self._render_block("user", self.user_entries),
        }

    def _reload_target(self, target: str):
        """重新从磁盘加载目标。"""
        fresh = self._read_file(self._path_for(target))
        fresh = list(dict.fromkeys(fresh))
        self._set_entries(target, fresh)

    def save_to_disk(self, target: str):
        """保存到磁盘。"""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._write_file(self._path_for(target), self._entries_for(target))

    def _entries_for(self, target: str) -> List[str]:
        """获取目标条目。"""
        if target == "user":
            return self.user_entries
        return self.memory_entries

    def _set_entries(self, target: str, entries: List[str]):
        """设置目标条目。"""
        if target == "user":
            self.user_entries = entries
        else:
            self.memory_entries = entries

    def _char_count(self, target: str) -> int:
        """计算目标字符数。"""
        entries = self._entries_for(target)
        if not entries:
            return 0
        return len(ENTRY_DELIMITER.join(entries))

    def _char_limit(self, target: str) -> int:
        """获取目标字符限制。"""
        if target == "user":
            return self.user_char_limit
        return self.memory_char_limit

    def _render_block(self, target: str, entries: List[str]) -> str:
        """渲染记忆块（用于系统提示）。"""
        if not entries:
            return ""
        label = "USER" if target == "user" else "MEMORY"
        content = ENTRY_DELIMITER.join(entries)
        return f"<{label}>\n{content}\n</{label}>"

    def get_system_prompt_snapshot(self) -> Dict[str, str]:
        """获取系统提示快照。"""
        return self._system_prompt_snapshot.copy()

    # =========================================================================
    # 核心操作
    # =========================================================================

    def add(self, target: str, content: str) -> Dict[str, Any]:
        """添加新条目。"""
        content = content.strip()
        if not content:
            return {"success": False, "error": "Content cannot be empty."}

        # 安全扫描
        scan_error = _scan_memory_content(content)
        if scan_error:
            return {"success": False, "error": scan_error}

        with self._file_lock(self._path_for(target)):
            self._reload_target(target)

            entries = self._entries_for(target)
            limit = self._char_limit(target)

            # 拒绝重复
            if content in entries:
                return self._success_response(target, "Entry already exists (no duplicate added).")

            # 检查限制
            new_entries = entries + [content]
            new_total = len(ENTRY_DELIMITER.join(new_entries))

            if new_total > limit:
                current = self._char_count(target)
                return {
                    "success": False,
                    "error": (
                        f"Memory at {current:,}/{limit:,} chars. "
                        f"Adding this entry ({len(content)} chars) would exceed the limit. "
                        f"Replace or remove existing entries first."
                    ),
                    "current_entries": entries,
                    "usage": f"{current:,}/{limit:,}",
                }

            entries.append(content)
            self._set_entries(target, entries)
            self.save_to_disk(target)

        return self._success_response(target, "Entry added.")

    def replace(self, target: str, old_text: str, new_content: str) -> Dict[str, Any]:
        """替换条目（子串匹配）。"""
        old_text = old_text.strip()
        new_content = new_content.strip()
        if not old_text:
            return {"success": False, "error": "old_text cannot be empty."}
        if not new_content:
            return {"success": False, "error": "new_content cannot be empty. Use 'remove' to delete entries."}

        # 安全扫描
        scan_error = _scan_memory_content(new_content)
        if scan_error:
            return {"success": False, "error": scan_error}

        with self._file_lock(self._path_for(target)):
            self._reload_target(target)

            entries = self._entries_for(target)
            matches = [(i, e) for i, e in enumerate(entries) if old_text in e]

            if len(matches) == 0:
                return {"success": False, "error": f"No entry matched '{old_text}'."}

            if len(matches) > 1:
                unique_texts = set(e for _, e in matches)
                if len(unique_texts) > 1:
                    previews = [e[:80] + ("..." if len(e) > 80 else "") for _, e in matches]
                    return {
                        "success": False,
                        "error": f"Multiple entries matched '{old_text}'. Be more specific.",
                        "matches": previews,
                    }

            idx = matches[0][0]
            limit = self._char_limit(target)

            # 检查限制
            test_entries = entries.copy()
            test_entries[idx] = new_content
            new_total = len(ENTRY_DELIMITER.join(test_entries))

            if new_total > limit:
                return {
                    "success": False,
                    "error": (
                        f"Replacement would put memory at {new_total:,}/{limit:,} chars. "
                        f"Shorten the new content or remove other entries first."
                    ),
                }

            entries[idx] = new_content
            self._set_entries(target, entries)
            self.save_to_disk(target)

        return self._success_response(target, "Entry replaced.")

    def remove(self, target: str, old_text: str) -> Dict[str, Any]:
        """删除条目（子串匹配）。"""
        old_text = old_text.strip()
        if not old_text:
            return {"success": False, "error": "old_text cannot be empty."}

        with self._file_lock(self._path_for(target)):
            self._reload_target(target)

            entries = self._entries_for(target)
            matches = [(i, e) for i, e in enumerate(entries) if old_text in e]

            if len(matches) == 0:
                return {"success": False, "error": f"No entry matched '{old_text}'."}

            if len(matches) > 1:
                unique_texts = set(e for _, e in matches)
                if len(unique_texts) > 1:
                    previews = [e[:80] + ("..." if len(e) > 80 else "") for _, e in matches]
                    return {
                        "success": False,
                        "error": f"Multiple entries matched '{old_text}'. Be more specific.",
                        "matches": previews,
                    }

            idx = matches[0][0]
            entries.pop(idx)
            self._set_entries(target, entries)
            self.save_to_disk(target)

        return self._success_response(target, "Entry removed.")

    def read(self, target: str) -> Dict[str, Any]:
        """读取所有条目。"""
        with self._file_lock(self._path_for(target)):
            self._reload_target(target)
            entries = self._entries_for(target)

        return self._success_response(target, f"{len(entries)} entries.")

    def _success_response(self, target: str, message: str) -> Dict[str, Any]:
        """成功响应。"""
        entries = self._entries_for(target)
        return {
            "success": True,
            "message": message,
            "entries": entries,
            "usage": f"{self._char_count(target):,}/{self._char_limit(target):,}",
        }


# ---------------------------------------------------------------------------
# 全局实例
# ---------------------------------------------------------------------------

_store: Optional[MemoryStore] = None


def get_store() -> MemoryStore:
    """获取全局记忆存储实例。"""
    global _store
    if _store is None:
        _store = MemoryStore()
        _store.load_from_disk()
    return _store


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """主函数。"""
    import sys

    store = get_store()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "add":
            if len(sys.argv) > 3:
                target = sys.argv[2]
                content = " ".join(sys.argv[3:])
                result = store.add(target, content)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("Usage: memory_tool.py add <memory|user> <content>")

        elif command == "replace":
            if len(sys.argv) > 4:
                target = sys.argv[2]
                old_text = sys.argv[3]
                new_content = " ".join(sys.argv[4:])
                result = store.replace(target, old_text, new_content)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("Usage: memory_tool.py replace <memory|user> <old_text> <new_content>")

        elif command == "remove":
            if len(sys.argv) > 3:
                target = sys.argv[2]
                old_text = " ".join(sys.argv[3:])
                result = store.remove(target, old_text)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("Usage: memory_tool.py remove <memory|user> <old_text>")

        elif command == "read":
            if len(sys.argv) > 2:
                target = sys.argv[2]
                result = store.read(target)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("Usage: memory_tool.py read <memory|user>")

        elif command == "status":
            print("Memory Status:")
            print(f"  MEMORY.md: {store._char_count('memory'):,}/{store.memory_char_limit:,} chars")
            print(f"  USER.md: {store._char_count('user'):,}/{store.user_char_limit:,} chars")
            print(f"  Entries: memory={len(store.memory_entries)}, user={len(store.user_entries)}")

        else:
            print(f"Unknown command: {command}")
    else:
        print("Memory Tool - Usage:")
        print("  memory_tool.py add <memory|user> <content>      # Add entry")
        print("  memory_tool.py replace <memory|user> <old> <new> # Replace entry")
        print("  memory_tool.py remove <memory|user> <old>        # Remove entry")
        print("  memory_tool.py read <memory|user>                # Read entries")
        print("  memory_tool.py status                            # Show status")


if __name__ == "__main__":
    main()
