---
title: "用 Camoufox 搞定反爬：浏览器自动化的实战经验"
date: "2026-03-20"
tags: [浏览器自动化, Camoufox, 反爬虫, Python]
excerpt: "普通浏览器自动化工具很容易被检测。Camoufox 通过指纹伪装绕过 Google、LinkedIn 等网站的反爬机制。本文分享实战踩坑经验。"
---

## 为什么需要 Camoufox？

当你用 Playwright / Selenium 自动化浏览器时，很多网站会检测：

- `navigator.webdriver` 属性
- 浏览器指纹（Canvas、WebGL、AudioContext）
- 行为模式（鼠标轨迹、点击间隔）

Google、LinkedIn、Amazon 等网站的反爬系统非常敏感，普通自动化工具几乎秒被拦。

**Camoufox** 是一个基于 Firefox 的反检测浏览器，核心能力：
- 伪造浏览器指纹
- 隐藏自动化特征
- 模拟真实用户行为

## 架构设计

我为 OpenClaw Agent 搭建了浏览器自动化 Skill，架构如下：

```
Agent (Python)
    ├── camofox_create_tab()    — 创建新标签页
    ├── camofox_navigate()      — 导航到 URL
    ├── camofox_snapshot()      — 获取页面快照（带元素引用）
    ├── camofox_click()         — 点击元素
    ├── camofox_type()          — 输入文本
    └── camofox_screenshot()    — 截图
```

每个操作都返回结构化数据，Agent 可以根据 snapshot 决定下一步操作。

## 实战：自动化 Google 搜索

```python
# 1. 创建标签页
tab = camofox_create_tab("https://google.com")

# 2. 获取快照，找到搜索框
snapshot = camofox_snapshot(tab)
# snapshot 返回元素引用 e1, e2, e3...

# 3. 输入搜索词
camofox_type(tab, ref="e1", text="AI Agent architecture")

# 4. 点击搜索按钮
camofox_click(tab, ref="e3")

# 5. 截图保存结果
camofox_screenshot(tab)
```

## 踩坑记录

### 坑 1: Snapshot 太大

某些页面（如 GitHub 仓库页）的 accessibility snapshot 非常大，会超出 token 限制。

**解决**：分页 snapshot，用 `offset` 参数获取后续内容。

### 坑 2: 元素引用不稳定

页面动态加载后，之前的 `e5` 可能变成了 `e8`。

**解决**：每次操作后重新 snapshot，不要缓存引用。

### 坑 3: Cookie 管理

某些网站需要登录状态，但手动登录后 cookie 不持久化。

**解决**：用 `camofox_import_cookies()` 导入 Netscape 格式的 cookie 文件。

## 适用场景

- ✅ 搜索引擎结果抓取（Google、Bing）
- ✅ 社交媒体数据采集（Twitter、LinkedIn）
- ✅ 电商价格监控（Amazon、淘宝）
- ✅ 需要登录状态的自动化
- ❌ 高频请求（会被限流）
- ❌ 需要处理大量 JavaScript 渲染的 SPA

## 代码

完整 Skill 开源在 [GitHub: browser-automation](https://github.com/sudabg)。

---

*反检测不是"绕过安全"，而是在合规范围内提高自动化的可靠性。请遵守网站的 robots.txt 和使用条款。*
