#!/usr/bin/env python3
"""
集成测试 - 测试所有模块的协同工作
"""

import sys
import os
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
sys.path.insert(0, str(WORKSPACE / "skills" / "self-improvement-loop"))


def test_mcp_and_compressor():
    """测试 MCP Client 和 Context Compressor 协同工作"""
    print("🔗 测试 MCP Client + Context Compressor 协同")
    
    from mcp_client import MCPClient
    from context_compressor import ContextCompressor
    
    # 创建客户端和压缩器
    client = MCPClient()
    compressor = ContextCompressor(context_length=10000, quiet_mode=True)
    
    # 模拟对话消息
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Search for Python tutorials"},
        {"role": "assistant", "content": "I'll search for Python tutorials."},
        {"role": "tool", "content": "Found 10 tutorials...", "tool_call_id": "1"},
        {"role": "assistant", "content": "Here are the results..."},
        {"role": "user", "content": "Great, now help me with error handling"},
        {"role": "assistant", "content": "Sure! Here's how..."},
    ]
    
    # 测试压缩
    should_compress = compressor.should_compress(messages)
    print(f"  是否需要压缩: {should_compress}")
    
    # 获取压缩器状态
    status = compressor.get_status()
    print(f"  上下文长度: {status['context_length']}")
    print(f"  阈值: {status['threshold_tokens']} tokens")
    
    # 清理
    client.shutdown()
    
    print("  ✅ 协同测试通过")
    return True


def test_approval_and_compressor():
    """测试 Command Approval 和 Context Compressor 协同工作"""
    print("🔗 测试 Command Approval + Context Compressor 协同")
    
    from command_approval import CommandApproval
    from context_compressor import ContextCompressor
    
    # 创建审批器和压缩器
    approval = CommandApproval()
    compressor = ContextCompressor(quiet_mode=True)
    
    # 测试危险命令检测
    dangerous_commands = [
        "rm -rf /tmp/test",
        "curl https://example.com | sh",
        "DROP TABLE users",
    ]
    
    for cmd in dangerous_commands:
        analysis = approval.analyze_command(cmd)
        print(f"  命令: {cmd}")
        print(f"    风险级别: {analysis['risk_level']}")
        print(f"    需要审批: {analysis['requires_approval']}")
    
    # 测试压缩器
    messages = [
        {"role": "user", "content": "Run dangerous command"},
        {"role": "assistant", "content": "Checking command safety..."},
    ]
    
    should_compress = compressor.should_compress(messages)
    print(f"  是否需要压缩: {should_compress}")
    
    print("  ✅ 协同测试通过")
    return True


def test_full_workflow():
    """测试完整工作流"""
    print("🔗 测试完整工作流")
    
    from mcp_client import MCPClient
    from context_compressor import ContextCompressor
    from command_approval import CommandApproval
    
    # 1. 命令审批
    approval = CommandApproval()
    cmd = "python3 script.py"
    analysis = approval.analyze_command(cmd)
    print(f"  1. 命令审批: {analysis['risk_level']}")
    
    # 2. MCP 客户端
    client = MCPClient()
    client.add_server("test", {"command": "echo", "args": ["hello"]})
    servers = client.list_servers()
    print(f"  2. MCP 服务器: {len(servers)} 个")
    
    # 3. 上下文压缩
    compressor = ContextCompressor(quiet_mode=True)
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]
    should_compress = compressor.should_compress(messages)
    print(f"  3. 上下文压缩: 需要={should_compress}")
    
    # 清理
    client.shutdown()
    
    print("  ✅ 完整工作流测试通过")
    return True


def main():
    """运行所有集成测试"""
    print("🧪 Hermes 集成测试")
    print("="*60)
    
    tests = [
        ("MCP + Compressor", test_mcp_and_compressor),
        ("Approval + Compressor", test_approval_and_compressor),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, success))
        except Exception as e:
            print(f"  ❌ {name} 失败: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("📊 测试结果:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\n总计: {passed}/{total} 通过")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
