#!/usr/bin/env python3
"""
sync_completed_tasks.py — 从 memory 日志自动同步已完成任务到项目计划 (v2)

修复 v1 bug:
- 跨日期同 ID 虚假完成：不再扫描昨日 memory 文件
- 移除"全部完成"通配模式（过于激进）
- 只处理当日 project-plans 中实际存在的任务 ID

用法：
  python3 sync_completed_tasks.py [--date YYYY-MM-DD] [--dry-run]
"""

import re
import sys
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/gem/workspace/agent/workspace")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_plan_task_ids(date_str: str) -> set:
    """获取当日 project-plans 中实际存在的 S-xx 任务 ID"""
    plan_file = WORKSPACE / "docs" / f"project-plans-{date_str}.md"
    if not plan_file.exists():
        return set()
    content = plan_file.read_text()
    return set(re.findall(r'(?:^|\n)\s*-\s+\[[ x]\]\s+(S-\d+):', content))

def find_completed_task_ids(date_str: str, valid_ids: set) -> set:
    """仅从当日 memory log 中扫描已完成的 S-xx 任务 ID"""
    completed = set()

    # 只扫描当日 memory 文件（v2 修复：不再跨日期）
    mem_file = WORKSPACE / "memory" / f"{date_str}.md"
    if not mem_file.exists():
        return completed

    content = mem_file.read_text()

    # 模式1: 直接标记完成（✅ S-01: 或 S-01: ... 已完成）
    for pattern in [
        r'✅\s*(?:\*\*)?(S-\d+)(?:\*\*)?\s*[:：]',
        r'(S-\d+)\s*[:：].*(?:✅|完成|成功)',
        r'(?:完成|✅)\s*(?:\*\*)?(S-\d+)',
    ]:
        for match in re.finditer(pattern, content):
            tid = match.group(1)
            if tid in valid_ids:
                completed.add(tid)

    # 模式2: "最终成果" 后的 ✅ 行
    final_section = re.search(r'最终成果.*?(?=\n##|\Z)', content, re.DOTALL)
    if final_section:
        for match in re.finditer(r'✅\s*\*{0,2}(S-\d+)', final_section.group()):
            tid = match.group(1)
            if tid in valid_ids:
                completed.add(tid)

    return completed

def sync_plan_file(date_str: str, task_ids: set, dry_run: bool = False) -> dict:
    """将完成状态同步到项目计划文件"""
    plan_file = WORKSPACE / "docs" / f"project-plans-{date_str}.md"
    if not plan_file.exists():
        log(f"⚠️ 计划文件不存在: {plan_file}")
        return {"error": "plan_not_found"}

    content = plan_file.read_text()
    original = content
    marked = 0
    already_done = 0

    for task_id in task_ids:
        # 只将 - [ ] S-XX 替换为 - [x] S-XX（不反向操作）
        pattern = rf'^(-\s+)\[ \](\s+{re.escape(task_id)}:)'
        new_content, count = re.subn(pattern, rf'\1[x]\2', content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            marked += count
        else:
            if re.search(rf'-\s+\[x\]\s+{re.escape(task_id)}:', content):
                already_done += 1

    if content != original and not dry_run:
        plan_file.write_text(content)
        log(f"✅ 已更新 {plan_file.name}: {marked} 个任务标为完成 ({already_done} 个已是完成状态)")
    elif content == original:
        log(f"ℹ️ 无需更新: {marked} 个新标记, {already_done} 个已是完成")
    else:
        log(f"🔍 [DRY RUN] 将标记 {marked} 个任务")

    return {"marked": marked, "already_done": already_done, "total_found": len(task_ids)}

def update_heartbeat_cache():
    """更新 last_heartbeat.json 以触发 dashboard 刷新"""
    cache_file = WORKSPACE / ".learnings" / "last_heartbeat.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            data["last_task_sync"] = datetime.now().isoformat()
            cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            pass

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    dry_run = "--dry-run" in sys.argv

    for arg in sys.argv:
        if arg.startswith("--date="):
            date_str = arg.split("=")[1]

    log(f"扫描日期: {date_str}")
    log(f"模式: {'DRY RUN' if dry_run else 'LIVE'}")

    # 1. 获取当日计划中的有效任务 ID
    valid_ids = get_plan_task_ids(date_str)
    log(f"当日计划任务: {sorted(valid_ids) if valid_ids else '无'}")

    # 2. 从当日 memory 日志中查找已完成任务
    completed = find_completed_task_ids(date_str, valid_ids)
    log(f"发现已完成任务: {sorted(completed) if completed else '无'}")

    if not completed:
        log("✅ 无需同步")
        return

    # 3. 同步到计划文件
    result = sync_plan_file(date_str, completed, dry_run)

    # 4. 更新缓存
    if not dry_run and result.get("marked", 0) > 0:
        update_heartbeat_cache()

    log(f"完成: {json.dumps(result, ensure_ascii=False)}")

if __name__ == "__main__":
    main()
