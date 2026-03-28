# Browser Automation Skill

Browser automation for OpenClaw agents. Provides a Python API for web navigation, element interaction, and screenshot capture — powered by Playwright.

## When to Use

- Need to automate browser tasks (navigation, form filling, clicking)
- Taking screenshots of web pages
- Scraping or interacting with web content programmatically
- When built-in `camofox_*` tools aren't available (e.g., from Python scripts)

## Available Functions

| Function | Description | Key Args |
|----------|-------------|----------|
| `browser_navigate(url)` | Navigate to a URL | `url`: target URL |
| `browser_click(selector)` | Click an element | `selector`: CSS selector |
| `browser_type(selector, text)` | Type into an input | `selector`: CSS selector, `text`: content |
| `browser_screenshot(path, full_page)` | Capture screenshot | `path`: save path (default `/tmp/screenshot.png`), `full_page`: bool |
| `browser_close()` | Close browser session | None |

## Quick Start

```python
from browser_navigate import browser_navigate
from browser_click import browser_click
from browser_type import browser_type
from browser_screenshot import browser_screenshot

# Navigate
browser_navigate("https://example.com")

# Type into search box
browser_type("input[name='q']", "OpenClaw")

# Click search button
browser_click("button[type='submit']")

# Screenshot results
browser_screenshot("/tmp/search_results.png")
```

## Session Management

- Sessions are managed by a singleton `BrowserSession` — calling `navigate` auto-starts the browser
- Use `browser_close()` to release resources when done
- Thread-safe (uses lock for initialization)

## Anti-Detection Note

This skill uses Playwright (Chromium) directly. For sites with bot detection (Google, Amazon, LinkedIn, etc.), prefer the built-in `camofox_*` tools instead — they use Camoufox (Firefox-based) with anti-detection patches.

Use this skill for: simple automation, internal tools, or when you need Playwright's full API.

## Requirements

- Python 3.8+
- Playwright (`pip install playwright && playwright install chromium`)
- OpenClaw runtime

## License

MIT
