#!/usr/bin/env python3
"""
browser_navigate: 导航到指定URL
"""

from .session_manager import navigate

def browser_navigate(url: str):
    """
    导航到指定URL
    
    Args:
      url: 目标网址（必填）
    
    Returns:
      status: success/error
      url: 当前页面URL
      title: 页面标题
      message: 结果描述
    """
    return navigate(url)
