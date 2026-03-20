# 🌐 Browser Automation Quickstart

本文档介绍如何使用 OpenClaw 的 browser-automation 技能进行网页自动化操作。

## 📦 技能结构

```
skills/browser-automation/
├── __init__.py
├── browser_navigate.py    # 导航到URL
├── browser_click.py       # 点击元素
├── browser_type.py        # 输入文本
├── browser_screenshot.py  # 截图（已修复）
└── test_skill.py         # 测试脚本
```

## 🚀 快速开始

### 1. 导航到网页

使用 `browser_navigate` 工具访问任意URL：

```python
# 导航到 example.com 并获取标题
await browser_navigate({
    "url": "https://example.com",
    "waitUntil": "networkidle0"
})
```

### 2. 截图保存

使用 `browser_screenshot` 工具截取当前页面：

```python
# 截图并保存到指定路径
await browser_screenshot({
    "path": "/tmp/example_final.png",
    "fullPage": True
})
```

### 3. 点击元素

使用 `browser_click` 工具点击页面元素（支持ref和CSS选择器）：

```python
# 通过元素ref点击
await browser_click({
    "tabId": "your_tab_id",
    "ref": "e1"  # 来自快照的元素引用
})

# 或通过CSS选择器点击
await browser_click({
    "tabId": "your_tab_id",
    "selector": "button.submit"
})
```

### 4. 输入文本

使用 `browser_type` 工具在输入框中输入文本：

```python
# 在搜索框中输入文字
await browser_type({
    "tabId": "your_tab_id",
    "ref": "e2",  # 输入框元素ref
    "text": "Hello World",
    "pressEnter": True  # 输入后按回车
})
```

## 📋 完整工作流示例

以下是一个完整的自动化工作流示例：

```python
# 1. 创建新标签页并导航到Google
tab = await camofox_create_tab({
    "url": "https://google.com"
})

# 2. 等待页面加载
await browser_navigate({
    "tabId": tab.tabId,
    "url": "https://google.com"
})

# 3. 在搜索框中输入关键词
await browser_type({
    "tabId": tab.tabId,
    "selector": "input[name='q']",
    "text": "OpenClaw browser automation",
    "pressEnter": True
})

# 4. 等待搜索结果加载
await browser_navigate({
    "tabId": tab.tabId,
    "url": "https://www.google.com/search?q=OpenClaw+browser+automation"
})

# 5. 截图保存结果
await browser_screenshot({
    "tabId": tab.tabId,
    "path": "/tmp/search_results.png",
    "fullPage": True
})

# 6. 关闭标签页
await camofox_close_tab({
    "tabId": tab.tabId
})
```

## ⚠️ 注意事项

1. **标签页管理**：所有操作都需要有效的 `tabId`，可通过 `camofox_create_tab` 获取
2. **元素定位**：优先使用快照中的元素ref（如 e1, e2），备用CSS选择器
3. **等待策略**：使用 `waitUntil` 参数确保页面加载完成后再执行操作
4. **错误处理**：建议包装操作在try/catch块中，处理网络超时或元素未找到的情况
5. **资源清理**：使用完标签页后记得调用 `camofox_close_tab` 释放资源

## 🔧 故障排除

- **元素未找到**：检查选择器是否正确，尝试使用快照中的ref
- **页面加载超时**：增加 `timeoutMs` 参数或调整 `waitUntil` 条件
- **权限问题**：确保已授予必要的浏览器权限
- **无头环境限制**：某些交互可能在无头模式下行为不同

## 📚 进阶用法

参考 `test_skill.py` 查看完整的测试用例和最佳实践。

祝您使用愉快！ 🦞