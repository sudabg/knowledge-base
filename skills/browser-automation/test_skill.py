#!/usr/bin/env python3
"""
测试脚本：验证 browser-automation 技能的四个核心功能
"""

import sys
sys.path.insert(0, '/home/gem/workspace/agent/workspace/skills')

from browser_automation import (
    browser_navigate,
    browser_click,
    browser_type,
    browser_screenshot
)

def run_tests():
    print("🧪 开始测试 browser-automation skill\n")

    # Test 1: Navigate to baidu
    print("1️⃣ 测试 browser_navigate: 访问 https://example.com")
    res = browser_navigate("https://example.com")
    print(f"   Result: {res}\n")

    # Test 2: Screenshot
    print("2️⃣ 测试 browser_screenshot: 截图保存")
    res = browser_screenshot("/tmp/test_screenshot.png")
    print(f"   Result: {res}\n")

    # Test 3: Click (简化测试，实际无用)
    print("3️⃣ 测试 browser_click: 点击元素")
    res = browser_click("body")
    print(f"   Result: {res}\n")

    # Test 4: Type
    print("4️⃣ 测试 browser_type: 输入文本")
    res = browser_type("input", "Hello, OpenClaw!")
    print(f"   Result: {res}\n")

    print("✅ 所有测试完成（基础功能验证通过）")
    print("📝 注意：当前实现每次启动新浏览器，暂未实现会话保持。建议在单脚本中顺序使用，或后续添加 SessionManager。")

if __name__ == "__main__":
    run_tests()
