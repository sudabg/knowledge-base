#!/usr/bin/env python3
"""
Browser Automation Skill for OpenClaw
基于 Playwright 的浏览器自动化技能，支持导航、点击、输入、截图。
"""

from .browser_navigate import browser_navigate
from .browser_click import browser_click
from .browser_type import browser_type
from .browser_screenshot import browser_screenshot
from .browser_close import browser_close

__all__ = [
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_screenshot",
    "browser_close",
]
