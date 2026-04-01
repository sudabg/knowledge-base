#!/usr/bin/env python3
"""
单元测试 - MCP Client
测试 mcp_client_v2.py 的所有功能
"""

import sys
import os
import json
import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client_v2 import (
    MCPClient,
    MCPServerTask,
    _build_safe_env,
    _sanitize_error,
    _SAFE_ENV_KEYS,
    _CREDENTIAL_PATTERN,
)


class TestSecurityHelpers(unittest.TestCase):
    """测试安全辅助函数"""

    def test_build_safe_env(self):
        """测试环境变量过滤"""
        # 设置一些测试环境变量
        os.environ["PATH"] = "/usr/bin"
        os.environ["HOME"] = "/home/user"
        os.environ["SECRET_KEY"] = "secret123"
        os.environ["XDG_CONFIG_HOME"] = "/home/user/.config"
        
        env = _build_safe_env()
        
        # 应该包含安全变量
        self.assertIn("PATH", env)
        self.assertIn("HOME", env)
        self.assertIn("XDG_CONFIG_HOME", env)
        
        # 不应该包含不安全变量
        self.assertNotIn("SECRET_KEY", env)

    def test_build_safe_env_with_user_env(self):
        """测试带用户环境变量的过滤"""
        user_env = {"MY_VAR": "my_value"}
        env = _build_safe_env(user_env)
        
        self.assertIn("MY_VAR", env)
        self.assertEqual(env["MY_VAR"], "my_value")

    def test_sanitize_error(self):
        """测试凭证剥离"""
        # GitHub PAT
        error = "Error: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = _sanitize_error(error)
        self.assertNotIn("ghp_", sanitized)
        self.assertIn("[REDACTED]", sanitized)

        # OpenAI key
        error = "Error: sk-1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = _sanitize_error(error)
        self.assertNotIn("sk-", sanitized)

        # Bearer token
        error = "Error: Bearer abc123def456"
        sanitized = _sanitize_error(error)
        self.assertNotIn("Bearer abc123", sanitized)


class TestMCPServerTask(unittest.TestCase):
    """测试 MCP 服务器任务"""

    def test_init(self):
        """测试初始化"""
        config = {"command": "npx", "args": ["-y", "test-server"]}
        server = MCPServerTask("test", config)
        
        self.assertEqual(server.name, "test")
        self.assertEqual(server.config, config)
        self.assertFalse(server._connected)
        self.assertIsNone(server._error)

    def test_is_http(self):
        """测试 HTTP 传输检测"""
        # Stdio 传输
        config = {"command": "npx", "args": ["-y", "test-server"]}
        server = MCPServerTask("test", config)
        self.assertFalse(server.is_http())

        # HTTP 传输
        config = {"url": "https://example.com/mcp"}
        server = MCPServerTask("test", config)
        self.assertTrue(server.is_http())


class TestMCPClient(unittest.TestCase):
    """测试 MCP 客户端"""

    def setUp(self):
        """设置测试环境"""
        self.client = MCPClient()

    def tearDown(self):
        """清理测试环境"""
        try:
            self.client.shutdown()
        except Exception:
            pass

    def test_add_server(self):
        """测试添加服务器"""
        config = {"command": "npx", "args": ["-y", "test-server"]}
        self.client.add_server("test", config)
        
        servers = self.client.list_servers()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["name"], "test")
        self.assertFalse(servers[0]["connected"])

    def test_remove_server(self):
        """测试移除服务器"""
        config = {"command": "npx", "args": ["-y", "test-server"]}
        self.client.add_server("test", config)
        self.client.remove_server("test")
        
        servers = self.client.list_servers()
        self.assertEqual(len(servers), 0)

    def test_duplicate_server(self):
        """测试重复添加服务器"""
        config = {"command": "npx", "args": ["-y", "test-server"]}
        self.client.add_server("test", config)
        
        with self.assertRaises(ValueError):
            self.client.add_server("test", config)


class TestCredentialPatterns(unittest.TestCase):
    """测试凭证模式匹配"""

    def test_github_pat(self):
        """测试 GitHub PAT 检测"""
        text = "Error: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        self.assertTrue(_CREDENTIAL_PATTERN.search(text))

    def test_openai_key(self):
        """测试 OpenAI key 检测"""
        text = "Error: sk-1234567890abcdefghijklmnopqrstuvwxyz"
        self.assertTrue(_CREDENTIAL_PATTERN.search(text))

    def test_bearer_token(self):
        """测试 Bearer token 检测"""
        text = "Error: Bearer abc123def456"
        self.assertTrue(_CREDENTIAL_PATTERN.search(text))

    def test_safe_text(self):
        """测试安全文本"""
        text = "This is a normal error message"
        self.assertIsNone(_CREDENTIAL_PATTERN.search(text))


class TestAsyncOperations(unittest.TestCase):
    """测试异步操作"""

    def test_ensure_loop(self):
        """测试事件循环创建"""
        client = MCPClient()
        client._ensure_loop()
        
        self.assertIsNotNone(client._loop)
        self.assertTrue(client._loop.is_running())
        
        client.shutdown()


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPServerTask))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPClient))
    suite.addTests(loader.loadTestsFromTestCase(TestCredentialPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncOperations))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "="*70)
    print("测试结果:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
