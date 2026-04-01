#!/usr/bin/env python3
"""
Hermes 集成监控脚本
全天监控集成能力的效果，发现问题及时优化
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
MONITOR_LOG = WORKSPACE / ".learnings" / "hermes_monitor.json"

# 添加模块路径
sys.path.insert(0, str(WORKSPACE / "skills" / "self-improvement-loop"))


def test_imports():
    """测试所有模块导入"""
    results = {}
    
    try:
        from mcp_client import MCPClient
        results["mcp_client"] = {"status": "ok", "error": None}
    except Exception as e:
        results["mcp_client"] = {"status": "error", "error": str(e)}
    
    try:
        from context_compressor import ContextCompressor
        results["context_compressor"] = {"status": "ok", "error": None}
    except Exception as e:
        results["context_compressor"] = {"status": "error", "error": str(e)}
    
    try:
        from command_approval import CommandApproval
        results["command_approval"] = {"status": "ok", "error": None}
    except Exception as e:
        results["command_approval"] = {"status": "error", "error": str(e)}
    
    try:
        from memory_tool import MemoryStore
        results["memory_tool"] = {"status": "ok", "error": None}
    except Exception as e:
        results["memory_tool"] = {"status": "error", "error": str(e)}
    
    return results


def test_functionality():
    """测试功能可用性"""
    results = {}
    
    # 测试 MCP Client
    try:
        from mcp_client import MCPClient
        client = MCPClient()
        client.add_server("test", {"command": "echo", "args": ["hello"]})
        servers = client.list_servers()
        client.shutdown()
        results["mcp_client"] = {
            "status": "ok",
            "servers": len(servers),
            "error": None
        }
    except Exception as e:
        results["mcp_client"] = {"status": "error", "error": str(e)}
    
    # 测试 Context Compressor
    try:
        from context_compressor import ContextCompressor
        compressor = ContextCompressor(quiet_mode=True)
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        should_compress = compressor.should_compress(messages)
        status = compressor.get_status()
        results["context_compressor"] = {
            "status": "ok",
            "should_compress": should_compress,
            "context_length": status["context_length"],
            "error": None
        }
    except Exception as e:
        results["context_compressor"] = {"status": "error", "error": str(e)}
    
    # 测试 Command Approval
    try:
        from command_approval import CommandApproval
        approval = CommandApproval()
        analysis = approval.analyze_command("rm -rf /tmp/test")
        results["command_approval"] = {
            "status": "ok",
            "risk_level": analysis["risk_level"],
            "requires_approval": analysis["requires_approval"],
            "error": None
        }
    except Exception as e:
        results["command_approval"] = {"status": "error", "error": str(e)}
    
    return results


def run_unit_tests():
    """运行单元测试"""
    results = {}
    
    # 测试 MCP Client
    import subprocess
    test_file = WORKSPACE / "skills" / "self-improvement-loop" / "test_mcp_client.py"
    if test_file.exists():
        proc = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            cwd=str(test_file.parent)
        )
        results["mcp_client"] = {
            "passed": proc.returncode == 0,
            "output": proc.stdout[-200:] if proc.stdout else "",
            "error": proc.stderr[-200:] if proc.stderr else ""
        }
    
    # 测试 Context Compressor
    test_file = WORKSPACE / "skills" / "self-improvement-loop" / "test_context_compressor.py"
    if test_file.exists():
        proc = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            cwd=str(test_file.parent)
        )
        results["context_compressor"] = {
            "passed": proc.returncode == 0,
            "output": proc.stdout[-200:] if proc.stdout else "",
            "error": proc.stderr[-200:] if proc.stderr else ""
        }
    
    return results


def check_integration_health():
    """检查集成健康状态"""
    print("🔍 Hermes 集成健康检查")
    print("="*60)
    
    # 1. 测试导入
    print("\n📦 模块导入测试:")
    imports = test_imports()
    for module, result in imports.items():
        status = "✅" if result["status"] == "ok" else "❌"
        error = f" ({result['error']})" if result["error"] else ""
        print(f"  {status} {module}{error}")
    
    # 2. 测试功能
    print("\n⚙️ 功能测试:")
    functionality = test_functionality()
    for module, result in functionality.items():
        status = "✅" if result["status"] == "ok" else "❌"
        error = f" ({result['error']})" if result["error"] else ""
        print(f"  {status} {module}{error}")
    
    # 3. 运行单元测试
    print("\n🧪 单元测试:")
    unit_tests = run_unit_tests()
    for module, result in unit_tests.items():
        status = "✅" if result["passed"] else "❌"
        print(f"  {status} {module}")
    
    # 4. 汇总
    print("\n📊 汇总:")
    total_modules = len(imports)
    healthy_modules = sum(1 for r in imports.values() if r["status"] == "ok")
    print(f"  健康模块: {healthy_modules}/{total_modules}")
    
    # 5. 记录日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "imports": imports,
        "functionality": functionality,
        "unit_tests": {k: v["passed"] for k, v in unit_tests.items()},
        "healthy_modules": healthy_modules,
        "total_modules": total_modules,
    }
    
    # 读取现有日志
    logs = []
    if MONITOR_LOG.exists():
        try:
            with open(MONITOR_LOG, "r") as f:
                logs = json.load(f)
        except Exception:
            pass
    
    # 添加新日志
    logs.append(log_entry)
    
    # 保留最近 100 条
    logs = logs[-100:]
    
    # 保存日志
    MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(MONITOR_LOG, "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"\n📝 日志已保存到: {MONITOR_LOG}")
    
    return healthy_modules == total_modules


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            success = check_integration_health()
            sys.exit(0 if success else 1)
        
        elif command == "log":
            if MONITOR_LOG.exists():
                with open(MONITOR_LOG, "r") as f:
                    logs = json.load(f)
                print("最近的监控日志:")
                for log in logs[-5:]:
                    print(f"  {log['timestamp']}: {log['healthy_modules']}/{log['total_modules']} 健康")
            else:
                print("暂无监控日志")
        
        elif command == "status":
            imports = test_imports()
            print("当前状态:")
            for module, result in imports.items():
                status = "✅" if result["status"] == "ok" else "❌"
                print(f"  {status} {module}")
        
        else:
            print(f"未知命令: {command}")
    else:
        print("Hermes 集成监控 - 用法:")
        print("  monitor.py check   # 运行健康检查")
        print("  monitor.py log     # 查看监控日志")
        print("  monitor.py status  # 查看当前状态")


if __name__ == "__main__":
    main()
