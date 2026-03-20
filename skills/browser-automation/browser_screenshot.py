#!/usr/bin/env python3
"""
browser_screenshot: 截取当前页面截图
"""

from .session_manager import screenshot

def browser_screenshot(path: str = "/tmp/screenshot.png", full_page: bool = False):
    """
    截取当前浏览器页面截图
    
    Args:
      path: 保存路径（可选，默认 /tmp/screenshot.png）
      full_page: 是否截取完整页面（可选，默认 False）
    
    Returns:
      status: success/error
      path: 截图文件路径
      message: 结果描述
    """
    return screenshot(path, full_page)
