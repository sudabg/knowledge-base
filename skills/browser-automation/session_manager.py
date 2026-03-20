#!/usr/bin/env python3
"""
Playwright Session Manager
维护单一浏览器会话，供多次操作复用。
"""

from playwright.sync_api import sync_playwright
import threading

class BrowserSession:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            self._initialized = True
    
    def start(self, headless=True):
        """启动浏览器会话"""
        if self.page is not None:
            return {"status": "success", "message": "Session already running"}
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            return {"status": "success", "message": "Browser session started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def stop(self):
        """停止浏览器会话"""
        try:
            if self.page:
                self.page = None
            if self.context:
                self.context.close()
                self.context = None
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            return {"status": "success", "message": "Browser session stopped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_page(self):
        """获取当前页面，如未启动则自动启动"""
        if self.page is None:
            self.start()
        return self.page

# 全局会话实例
_session = BrowserSession()

def navigate(url: str):
    """导航到指定URL"""
    try:
        page = _session.get_page()
        page.goto(url, timeout=30000)
        return {
            "status": "success",
            "url": page.url,
            "title": page.title(),
            "message": f"Navigated to {url}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def click(selector: str):
    """点击元素"""
    try:
        page = _session.get_page()
        page.click(selector, timeout=10000)
        return {"status": "success", "selector": selector, "message": f"Clicked {selector}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def type_text(selector: str, text: str):
    """在输入框中输入文本"""
    try:
        page = _session.get_page()
        page.fill(selector, text, timeout=10000)
        return {"status": "success", "selector": selector, "message": f"Typed into {selector}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def screenshot(path: str = "/tmp/screenshot.png", full_page: bool = False):
    """截取当前页面"""
    try:
        page = _session.get_page()
        page.screenshot(path=path, full_page=full_page, timeout=10000)
        return {"status": "success", "path": path, "message": f"Screenshot saved to {path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def close():
    """关闭会话"""
    return _session.stop()
