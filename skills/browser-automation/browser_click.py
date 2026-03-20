#!/usr/bin/env python3
"""
browser_click: 点击页面元素
"""

from .session_manager import click

def browser_click(selector: str):
    """
    点击指定CSS选择器对应的元素
    
    Args:
      selector: CSS选择器（必填）
    
    Returns:
      status: success/error
      selector: 使用的选择器
      message: 结果描述
    """
    return click(selector)
