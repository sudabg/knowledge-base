# browser-automation

Browser automation skill for OpenClaw agents. Provides a simple Python API for web navigation, element interaction, and screenshot capture — powered by Playwright.

## Features

| Module | Description |
|--------|-------------|
| `browser_navigate.py` | Navigate to URLs and get page info |
| `browser_click.py` | Click elements by CSS selector |
| `browser_type.py` | Type text into input fields |
| `browser_screenshot.py` | Capture page screenshots |
| `browser_close.py` | Close browser sessions |
| `session_manager.py` | Manage browser session lifecycle (singleton) |

## Quick Start

```python
from browser_navigate import browser_navigate
from browser_click import browser_click
from browser_type import browser_type
from browser_screenshot import browser_screenshot

# Navigate to a page
result = browser_navigate("https://example.com")
# → {"status": "success", "url": "https://example.com", "title": "Example Domain", ...}

# Type into a search input
browser_type("input[name='q']", "hello world")

# Click a button
browser_click("button[type='submit']")

# Take a screenshot
browser_screenshot("/tmp/page.png")
```

## API Reference

### `browser_navigate(url: str)`
Navigate the browser to `url`. Auto-starts a session if none exists.

**Returns:** `{status, url, title, message}`

### `browser_click(selector: str)`
Click the element matching `selector` (CSS selector).

**Returns:** `{status, selector, message}`

### `browser_type(selector: str, text: str)`
Fill the input matching `selector` with `text`.

**Returns:** `{status, selector, message}`

### `browser_screenshot(path: str, full_page: bool = False)`
Capture a screenshot. `full_page=True` captures the entire scrollable page.

**Returns:** `{status, path, message}`

### `browser_close()`
Close the browser session and free resources.

**Returns:** `{status, message}`

## Session Architecture

- **Singleton pattern:** One browser session per agent process
- **Auto-start:** Calling any function auto-initializes the browser
- **Thread-safe:** Initialization uses a threading lock
- **Explicit cleanup:** Call `browser_close()` when done

## When to Use This vs. Camoufox

| Use Case | Recommendation |
|----------|---------------|
| Simple automation, internal tools | ✅ This skill (Playwright) |
| Sites with bot detection (Google, LinkedIn) | 🦊 Use `camofox_*` tools instead |
| Need Playwright-specific features (PDF, video, etc.) | ✅ This skill |
| Quick interactive browsing | 🦊 Use `camofox_*` tools |

## Requirements

- Python 3.8+
- Playwright: `pip install playwright && playwright install chromium`
- OpenClaw runtime

## License

MIT
