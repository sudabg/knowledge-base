#!/usr/bin/env python3
"""
browser_close: 关闭浏览器会话
"""

from .session_manager import close

def browser_close():
    """
    关闭浏览器会话，释放资源
    
    Returns:
      status: success/error
      message: 结果描述
    """
    return close()
