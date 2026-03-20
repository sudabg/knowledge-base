#!/usr/bin/env python3
"""错误自动记录：调用时写入 ERRORS.md"""
import sys, os
from datetime import datetime

ERRORS_FILE = "/home/gem/workspace/agent/workspace/.learnings/ERRORS.md"

def log_error(error_type, context, fix=""):
    entry = f"\n### [{datetime.now().strftime('%H:%M')}] {error_type}\n"
    entry += f"- 上下文: {context}\n"
    if fix:
        entry += f"- 修复: {fix}\n"
    entry += f"- 时间: {datetime.now().isoformat()}\n"
    
    with open(ERRORS_FILE, 'a') as f:
        f.write(entry)
    return f"📝 已记录错误: {error_type}"

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print(log_error(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
    else:
        print("用法: error_hook.py <类型> <上下文> [修复]")
