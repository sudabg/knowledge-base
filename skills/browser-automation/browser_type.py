#!/usr/bin/env python3
"""
browser_type: 在输入框中输入文本
"""

from .session_manager import type_text

def browser_type(selector: str, text: str):
    """
    在指定输入框中输入文本
    
    Args:
      selector: 输入框CSS选择器（必填）
      text: 要输入的文本（必填）
    
    Returns:
      status: success/error
      selector: 使用的选择器
      message: 结果描述
    """
    return type_text(selector, text)
