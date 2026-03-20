#!/usr/bin/env python3
"""Claw Compactor Skill — OpenClaw Integration"""
import sys
from pathlib import Path

_DEV_DIR = Path("/tmp/claw-compactor/scripts")
if _DEV_DIR.exists():
    sys.path.insert(0, str(_DEV_DIR))

try:
    from lib.fusion.engine import FusionEngine
    from lib.tokens import estimate_tokens
except ImportError as e:
    raise ImportError(f"Claw Compactor modules not found. Install: pip install -e /tmp/claw-compactor. Error: {e}")

_engine = FusionEngine()

def compress(text: str) -> dict:
    """Compress a single text string."""
    result = _engine.compress(text)
    return {
        "compressed": result["compressed"],
        "original": result["original"],
        "stats": result["stats"],
        "compression_ratio": result["stats"]["reduction_pct"] / 100,
    }

def compress_messages(messages: list[dict]) -> dict:
    """Compress OpenAI-format message list.
    Returns dict with 'compressed' (serialized JSON), 'messages' (list), and stats.
    """
    result = _engine.compress_messages(messages)
    return {
        "compressed": result["messages"],  # the compressed message list
        "original_length": sum(len(m.get("content","")) for m in messages),
        "stats": result["stats"],
        "compression_ratio": result["stats"]["reduction_pct"] / 100,
    }

def estimate(text: str) -> int:
    """Estimate token count for text."""
    return estimate_tokens(text)

__all__ = ["compress", "compress_messages", "estimate"]
