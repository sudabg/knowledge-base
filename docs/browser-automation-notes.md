# 浏览器自动化技能封装：实战经验与避坑指南

## 背景
我在 OpenClaw 生态中封装了一个 `browser-automation` 技能，提供 `navigate`、`click`、`type`、`screenshot` 四个核心操作。经过实际测试，总结以下要点。

## 技术选型
- **Playwright**: 比 Selenium 更稳定，支持 headless，安装简单
- **Python 封装**: 通过技能机制暴露为工具函数，便于其他 Agent 调用
- **会话管理**: 使用单例 BrowserSession 避免重复启动

## 核心代码结构
```
browser_automation/
├── __init__.py           # 暴露接口
├── session_manager.py    # 浏览器生命周期管理
├── browser_navigate.py   # 导航
├── browser_click.py      # 点击
├── browser_type.py       # 输入
└── browser_screenshot.py # 截图
```

关键实现片段（navigate）:
```python
def browser_navigate(url: str) -> dict:
    session = BrowserSession.get()
    page = session.page
    try:
        response = page.goto(url, timeout=30000)
        return {
            "status": "success",
            "url": page.url,
            "title": page.title()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

## 踩坑记录

### 1. 元素定位超时
- **现象**: `browser_type` 报错 Timeout
- **原因**: 目标元素未在 10s 内出现（动态加载或选择器错误）
- **解决**: 增加 `wait_for_selector` 或使用更稳定的选择器（e.g., `#id` > `class` > `tag`）

### 2. 跨页面会话保持
- **问题**: 每个函数启动新浏览器 → 状态丢失
- **方案**: 使用全局 `BrowserSession` 单例，通过 `get()` 复用同一浏览器上下文

### 3. 资源清理
- **风险**: 浏览器进程僵尸化
- **优化**: `browser_close()` 确保所有标签页关闭；注册 `atexit` 处理器

## 使用建议
- ✅ 在单个脚本中顺序调用（navigate → click → type → screenshot）
- ✅ 配合 `time.sleep(2)` 等待页面渲染（测试阶段）
- ✅ 优先截图调试，确认页面结构后再自动化
- ❌ 避免循环快速触发，可能导致限流或崩溃

## 关联任务
- M-01-1: 发布 3 个高质量开源项目 → 本项目待发布
- S-06: 验证完整工作流 → 基础功能已验证
- S-11: 测试 2 个其他网站 → 待补充

---

*S-04 完成 ✅ — 2026-03-20 23:20*
