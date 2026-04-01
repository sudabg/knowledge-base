#!/usr/bin/env python3
"""
代码执行沙箱：安全执行 Python 代码。
实现 Hermes Agent execute_code 工具的核心功能。
"""

import os
import sys
import json
import ast
import subprocess
import tempfile
import signal
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from io import StringIO
import contextlib
import resource

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
SANDBOX_LOG = WORKSPACE / ".learnings" / "sandbox_logs.json"

# 危险模块/函数黑名单
BLACKLISTED_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket",
    "requests", "urllib", "http", "ftplib", "smtplib",
    "ctypes", "importlib", "pickle", "shelve",
}

BLACKLISTED_FUNCTIONS = {
    "eval", "exec", "compile", "__import__",
    "open", "file", "input", "raw_input",
    "globals", "locals", "vars",
}

class SandboxTimeout(Exception):
    """沙箱超时异常。"""
    pass

class SandboxMemoryError(Exception):
    """沙箱内存错误。"""
    pass

class CodeSandbox:
    """代码执行沙箱。"""

    def __init__(self, max_memory_mb=100, timeout_seconds=10):
        self.max_memory_mb = max_memory_mb
        self.timeout_seconds = timeout_seconds
        self.results = []

    def _check_ast_safety(self, code: str) -> tuple[bool, str]:
        """检查 AST 安全性。"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"语法错误: {e}"

        for node in ast.walk(tree):
            # 检查导入
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in BLACKLISTED_MODULES:
                        return False, f"禁止导入模块: {alias.name}"

            if isinstance(node, ast.ImportFrom):
                if node.module in BLACKLISTED_MODULES:
                    return False, f"禁止导入模块: {node.module}"

            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in BLACKLISTED_FUNCTIONS:
                        return False, f"禁止调用函数: {node.func.id}"

            # 检查属性访问
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("_"):
                    return False, f"禁止访问私有属性: {node.attr}"

        return True, "安全"

    def _create_sandbox_env(self) -> Dict:
        """创建沙箱环境变量。"""
        env = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "type": type,
                "isinstance": isinstance,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "any": any,
                "all": all,
                "True": True,
                "False": False,
                "None": None,
            }
        }
        return env

    def _limit_resources(self):
        """限制资源使用。"""
        # 限制内存
        memory_bytes = self.max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

        # 限制 CPU 时间
        resource.setrlimit(resource.RLIMIT_CPU, (self.timeout_seconds, self.timeout_seconds))

    def execute_code(self, code: str, timeout: int = None) -> Dict[str, Any]:
        """执行代码。"""
        timeout = timeout or self.timeout_seconds

        # 安全检查
        is_safe, safety_msg = self._check_ast_safety(code)
        if not is_safe:
            return {
                "success": False,
                "output": "",
                "error": f"安全检查失败: {safety_msg}",
                "execution_time": 0,
            }

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # 准备执行环境
            env = self._create_sandbox_env()

            # 捕获输出
            output_buffer = StringIO()
            error_buffer = StringIO()

            start_time = time.time()

            # 在线程中执行
            result = {"output": "", "error": "", "success": False}
            exception = None

            def run_code():
                nonlocal result, exception
                try:
                    with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
                        exec(code, env)
                    result["output"] = output_buffer.getvalue()
                    result["success"] = True
                except Exception as e:
                    exception = e
                    result["error"] = str(e)

            thread = threading.Thread(target=run_code)
            thread.daemon = True  # 避免超时时阻塞进程退出
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                # 超时
                return {
                    "success": False,
                    "output": "",
                    "error": f"执行超时（>{timeout}秒）",
                    "execution_time": timeout,
                }

            execution_time = time.time() - start_time

            # 记录结果
            self.results.append({
                "code": code[:100],
                "success": result["success"],
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
            })

            return {
                "success": result["success"],
                "output": result["output"],
                "error": result["error"],
                "execution_time": round(execution_time, 3),
            }

        finally:
            # 清理临时文件
            os.unlink(temp_file)

    def execute_file(self, file_path: str, timeout: int = None) -> Dict[str, Any]:
        """执行文件。"""
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "output": "",
                "error": f"文件不存在: {file_path}",
                "execution_time": 0,
            }

        code = path.read_text(encoding="utf-8")
        return self.execute_code(code, timeout)

    def get_execution_history(self, limit: int = 10) -> list:
        """获取执行历史。"""
        return self.results[-limit:]

    def save_logs(self):
        """保存执行日志。"""
        SANDBOX_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SANDBOX_LOG, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

def main():
    """主函数。"""
    import sys

    sandbox = CodeSandbox()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "run":
            if len(sys.argv) > 2:
                code = " ".join(sys.argv[2:])
                result = sandbox.execute_code(code)
                if result["success"]:
                    print("✅ 执行成功:")
                    print(result["output"])
                else:
                    print(f"❌ 执行失败: {result['error']}")
                print(f"执行时间: {result['execution_time']}秒")
            else:
                print("用法: code_sandbox.py run <code>")

        elif command == "file":
            if len(sys.argv) > 2:
                file_path = sys.argv[2]
                result = sandbox.execute_file(file_path)
                if result["success"]:
                    print("✅ 执行成功:")
                    print(result["output"])
                else:
                    print(f"❌ 执行失败: {result['error']}")
                print(f"执行时间: {result['execution_time']}秒")
            else:
                print("用法: code_sandbox.py file <file_path>")

        elif command == "history":
            history = sandbox.get_execution_history()
            print("执行历史:")
            for item in history:
                status = "✅" if item["success"] else "❌"
                print(f"  {status} {item['timestamp']} - {item['code'][:50]}")

        elif command == "interactive":
            print("交互式代码沙箱（输入 'exit' 退出）:")
            while True:
                try:
                    code = input(">>> ")
                    if code.lower() == "exit":
                        break
                    result = sandbox.execute_code(code)
                    if result["success"]:
                        print(result["output"])
                    else:
                        print(f"错误: {result['error']}")
                except KeyboardInterrupt:
                    break
            sandbox.save_logs()

        else:
            print(f"未知命令: {command}")
    else:
        print("代码执行沙箱 - 用法:")
        print("  python3 code_sandbox.py run <code>    # 执行代码")
        print("  python3 code_sandbox.py file <path>   # 执行文件")
        print("  python3 code_sandbox.py history       # 查看历史")
        print("  python3 code_sandbox.py interactive   # 交互模式")

if __name__ == "__main__":
    main()
