#!/usr/bin/env python3
"""
Prompts Chat — 精选 Prompt 库工具
从 prompts.chat (155K stars) 精选的 23 个高质量 prompt

用法:
  python3 use.py list [category]     — 列出所有/某类别的 prompt
  python3 use.py search <keyword>    — 搜索 prompt
  python3 use.py show <act_name>     — 显示完整 prompt
  python3 use.py random              — 随机展示一个 prompt
"""

import json
import sys
import os
from pathlib import Path

PROMPTS_FILE = Path(__file__).parent / "prompts.json"

def load_prompts():
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_prompts(category=None):
    prompts = load_prompts()
    if category:
        prompts = [p for p in prompts if p['category'] == category]
    
    if not prompts:
        print(f"❌ 未找到类别: {category}")
        available = sorted(set(p['category'] for p in load_prompts()))
        print(f"可用类别: {', '.join(available)}")
        return
    
    print(f"📋 Prompts ({len(prompts)} 个):\n")
    for p in prompts:
        dev = "🔧" if p['for_devs'] else "  "
        print(f"  {dev} [{p['category']}] {p['act']}")
    
    print(f"\n用法: python3 use.py show '<act_name>' 查看完整 prompt")

def search_prompts(keyword):
    prompts = load_prompts()
    keyword_lower = keyword.lower()
    matches = []
    for p in prompts:
        combined = f"{p['act']} {p['prompt']} {p['category']}".lower()
        if keyword_lower in combined:
            matches.append(p)
    
    if not matches:
        print(f"❌ 未找到匹配 '{keyword}' 的 prompt")
        return
    
    print(f"🔍 搜索 '{keyword}' → {len(matches)} 个匹配:\n")
    for p in matches:
        print(f"  [{p['category']}] {p['act']}")
        print(f"    {p['prompt'][:100]}...")
        print()

def show_prompt(act_name):
    prompts = load_prompts()
    matches = [p for p in prompts if p['act'].lower() == act_name.lower()]
    
    if not matches:
        # Fuzzy match
        matches = [p for p in prompts if act_name.lower() in p['act'].lower()]
    
    if not matches:
        print(f"❌ 未找到: {act_name}")
        return
    
    p = matches[0]
    print(f"📝 {p['act']}")
    print(f"   类别: {p['category']} | 类型: {p['type']} | 开发者: {'是' if p['for_devs'] else '否'}")
    print(f"   来源: {p['source']} | 许可: {p['license']}")
    print(f"\n{'─'*60}")
    print(p['prompt'])
    print(f"{'─'*60}")

def random_prompt():
    import random
    prompts = load_prompts()
    p = random.choice(prompts)
    show_prompt(p['act'])

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        category = sys.argv[2] if len(sys.argv) > 2 else None
        list_prompts(category)
    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("用法: python3 use.py search <keyword>")
            sys.exit(1)
        search_prompts(' '.join(sys.argv[2:]))
    elif cmd == 'show':
        if len(sys.argv) < 3:
            print("用法: python3 use.py show <act_name>")
            sys.exit(1)
        show_prompt(' '.join(sys.argv[2:]))
    elif cmd == 'random':
        random_prompt()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
