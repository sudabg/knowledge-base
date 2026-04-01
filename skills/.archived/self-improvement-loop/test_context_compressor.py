#!/usr/bin/env python3
"""
单元测试 - Context Compressor
测试 context_compressor_v2.py 的所有功能
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from context_compressor_v2 import (
    ContextCompressor,
    CompressionResult,
    SUMMARY_PREFIX,
    _PRUNED_TOOL_PLACEHOLDER,
)


class TestContextCompressor(unittest.TestCase):
    """测试上下文压缩器"""

    def setUp(self):
        """设置测试环境"""
        self.compressor = ContextCompressor(
            context_length=10000,
            threshold_percent=0.50,
            protect_first_n=2,
            protect_last_n=2,
            quiet_mode=True,
        )

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.compressor.context_length, 10000)
        self.assertEqual(self.compressor.threshold_tokens, 5000)
        self.assertEqual(self.compressor.compression_count, 0)

    def test_should_compress(self):
        """测试压缩触发条件"""
        # 短消息不应该触发
        short_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        self.assertFalse(self.compressor.should_compress(short_messages))

        # 长消息应该触发
        long_messages = [
            {"role": "user", "content": "A" * 10000},
            {"role": "assistant", "content": "B" * 10000},
            {"role": "user", "content": "C" * 10000},
            {"role": "assistant", "content": "D" * 10000},
        ]
        self.assertTrue(self.compressor.should_compress(long_messages))

    def test_prune_old_tool_results(self):
        """测试工具输出修剪"""
        messages = [
            {"role": "user", "content": "Run a command"},
            {"role": "assistant", "content": "Running...", "tool_calls": [{"id": "1", "function": {"name": "terminal"}}]},
            {"role": "tool", "content": "A" * 500, "tool_call_id": "1"},
            {"role": "assistant", "content": "Done!"},
            {"role": "user", "content": "Thanks"},
        ]

        pruned, count = self.compressor._prune_old_tool_results(messages, protect_tail_count=2)
        self.assertEqual(count, 1)
        self.assertEqual(pruned[2]["content"], _PRUNED_TOOL_PLACEHOLDER)

    def test_serialize_for_summary(self):
        """测试序列化"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!", "tool_calls": [{"function": {"name": "test", "arguments": "{}"}}]},
            {"role": "tool", "content": "Result", "tool_call_id": "1"},
        ]

        serialized = self.compressor._serialize_for_summary(messages)
        self.assertIn("[USER]:", serialized)
        self.assertIn("[ASSISTANT]:", serialized)
        self.assertIn("[TOOL RESULT", serialized)

    def test_tool_pair_sanitization(self):
        """测试工具对清理"""
        # 孤立的工具结果
        messages = [
            {"role": "user", "content": "Test"},
            {"role": "tool", "content": "Orphan result", "tool_call_id": "missing"},
            {"role": "assistant", "content": "Done"},
        ]

        sanitized = self.compressor._sanitize_tool_pairs(messages)
        self.assertEqual(len(sanitized), 2)  # 孤立结果被移除

    def test_boundary_alignment(self):
        """测试边界对齐"""
        messages = [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Response", "tool_calls": [{"id": "1"}]},
            {"role": "tool", "content": "Result", "tool_call_id": "1"},
            {"role": "assistant", "content": "Done"},
        ]

        # 前向对齐不应该在工具结果中间切割
        idx = self.compressor._align_boundary_backward(messages, 3)
        self.assertLessEqual(idx, 2)

    def test_get_status(self):
        """测试状态获取"""
        status = self.compressor.get_status()
        self.assertIn("context_length", status)
        self.assertIn("threshold_tokens", status)
        self.assertIn("compression_count", status)

    def test_compress_too_few_messages(self):
        """测试消息太少时的压缩"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        result = self.compressor.compress(messages)
        self.assertEqual(result.original_count, result.compressed_count)
        self.assertFalse(result.summary_generated)

    def test_compute_summary_budget(self):
        """测试摘要预算计算"""
        turns = [{"content": "A" * 1000} for _ in range(10)]
        budget = self.compressor._compute_summary_budget(turns)
        self.assertGreaterEqual(budget, 2000)  # 至少 2000 tokens


class TestCompressionResult(unittest.TestCase):
    """测试压缩结果"""

    def test_result_structure(self):
        """测试结果结构"""
        result = CompressionResult(
            messages=[],
            original_count=10,
            compressed_count=5,
            pruned_tool_results=2,
            summary_generated=True,
            tokens_saved=1000,
        )

        self.assertEqual(result.original_count, 10)
        self.assertEqual(result.compressed_count, 5)
        self.assertEqual(result.pruned_tool_results, 2)
        self.assertTrue(result.summary_generated)
        self.assertEqual(result.tokens_saved, 1000)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestContextCompressor))
    suite.addTests(loader.loadTestsFromTestCase(TestCompressionResult))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

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
