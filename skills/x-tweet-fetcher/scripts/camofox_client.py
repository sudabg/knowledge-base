#!/usr/bin/env python3
"""
Camofox Client - Shared module for Camofox browser automation.

Provides functions to open tabs, get snapshots, and fetch pages via Camofox REST API.
Used by fetch_tweet.py and fetch_china.py.

Improvements (2026-03-24, from EXPERIENCE.md):
  - Retry with exponential backoff (1s → 2s → 4s) for transient failures
  - Health check with caching to avoid repeated probes
  - Error classification: connection refused vs timeout vs parse error
  - Tab cleanup on error (no leaked tabs)
  - Configurable timeouts per operation
"""

import json
import secrets
import sys
import time
import urllib.request
import urllib.error
from typing import Optional


# ─── Health check cache (avoids repeated probes) ───────────────────────────
_health_cache = {"ok": False, "ts": 0.0, "ttl": 30.0}  # cache 30s


def check_camofox(port: int = 9377, force: bool = False) -> bool:
    """Return True if Camofox is reachable. Caches result for 30s."""
    now = time.time()
    if not force and (now - _health_cache["ts"]) < _health_cache["ttl"]:
        return _health_cache["ok"]
    try:
        req = urllib.request.Request(f"http://localhost:{port}/tabs", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp.read()
        _health_cache.update({"ok": True, "ts": now})
        return True
    except Exception:
        _health_cache.update({"ok": False, "ts": now})
        return False


def _classify_error(e: Exception) -> str:
    """Classify error for logging: connection_refused | timeout | http_error | other."""
    if isinstance(e, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(e, TimeoutError):
        return "timeout"
    if isinstance(e, urllib.error.URLError) and "Connection refused" in str(e):
        return "connection_refused"
    if isinstance(e, urllib.error.HTTPError):
        return f"http_{e.code}"
    return "other"


def _retry_request(req, timeout=10, max_retries=3, port=9377):
    """
    Execute HTTP request with exponential backoff.
    Returns response body (bytes) or raises last exception.
    Backoff: 1s → 2s → 4s (capped at max_retries).
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            err_type = _classify_error(e)
            # Don't retry on client errors (4xx) — format issue, not transient
            if err_type.startswith("http_"):
                code = int(err_type.split("_")[1])
                if 400 <= code < 500:
                    raise
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1, 2, 4
                print(f"[Camofox] {err_type}, retry {attempt+1}/{max_retries} in {wait}s", file=sys.stderr)
                time.sleep(wait)
    raise last_err


def camofox_open_tab(url: str, session_key: str, port: int = 9377) -> Optional[str]:
    """Open a new Camofox tab; return tabId or None."""
    if not url.startswith(('http://', 'https://')):
        print(f"[Camofox] rejected non-HTTP URL: {url[:60]}", file=sys.stderr)
        return None
    try:
        payload = json.dumps({
            "userId": "x-tweet-fetcher",
            "sessionKey": session_key,
            "url": url,
        }).encode()
        req = urllib.request.Request(
            f"http://localhost:{port}/tabs",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        data = _retry_request(req, timeout=10)
        return json.loads(data.decode()).get("tabId")
    except Exception as e:
        print(f"[Camofox] open tab error ({_classify_error(e)}): {e}", file=sys.stderr)
        return None


def camofox_snapshot(tab_id: str, port: int = 9377, timeout: int = 15) -> Optional[str]:
    """Get page snapshot text from Camofox tab. Configurable timeout for slow pages."""
    try:
        url = f"http://localhost:{port}/tabs/{tab_id}/snapshot?userId=x-tweet-fetcher"
        data = _retry_request(url, timeout=timeout, max_retries=2)
        return json.loads(data.decode()).get("snapshot", "")
    except Exception as e:
        print(f"[Camofox] snapshot error ({_classify_error(e)}): {e}", file=sys.stderr)
        return None


def camofox_close_tab(tab_id: str, port: int = 9377):
    """Close a Camofox tab."""
    try:
        req = urllib.request.Request(
            f"http://localhost:{port}/tabs/{tab_id}",
            method="DELETE",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def camofox_fetch_page(url: str, session_key: str, wait: float = 8, port: int = 9377,
                       snapshot_timeout: int = 15) -> Optional[str]:
    """Open URL in Camofox, wait, snapshot, close. Returns snapshot text.
    
    Always cleans up tab even on error (no leaked tabs).
    Configurable wait and snapshot_timeout for slow-loading pages.
    """
    tab_id = camofox_open_tab(url, session_key, port)
    if not tab_id:
        return None
    try:
        time.sleep(wait)
        return camofox_snapshot(tab_id, port, timeout=snapshot_timeout)
    except Exception as e:
        print(f"[Camofox] fetch_page error ({_classify_error(e)}): {e}", file=sys.stderr)
        return None
    finally:
        camofox_close_tab(tab_id, port)


import re
import urllib.parse


def camofox_search(query: str, num: int = 10, lang: str = "zh-CN", engine: str = "google", port: int = 9377) -> list:
    """
    Search via Camofox. Supports Google and DuckDuckGo.
    
    Args:
        query: search keywords
        num: max results
        lang: language code
        engine: "google" or "duckduckgo"
        port: Camofox port
    
    Returns list of dicts: [{"title": ..., "url": ..., "snippet": ...}, ...]
    """
    encoded = urllib.parse.quote(query)
    
    if engine == "duckduckgo":
        search_url = f"https://duckduckgo.com/?q={encoded}&kl={lang}&t=h_"
        snapshot = camofox_fetch_page(search_url, f"ddg-{secrets.token_hex(8)}", wait=5, port=port)
        if not snapshot:
            return []
        return _parse_duckduckgo_results(snapshot, num)
    else:
        search_url = f"https://www.google.com/search?q={encoded}&hl={lang}&num={num}"
        snapshot = camofox_fetch_page(search_url, f"search-{secrets.token_hex(8)}", wait=4, port=port)
        if not snapshot:
            return []
        return _parse_google_results(snapshot)


def _parse_duckduckgo_results(snapshot: str, max_results: int = 10) -> list:
    """Parse DuckDuckGo search results from Camofox snapshot text."""
    results = []
    lines = snapshot.split("\n")
    i = 0
    while i < len(lines) and len(results) < max_results:
        line = lines[i].strip()
        # DuckDuckGo result pattern: heading with link
        if '- heading "' in line and '[level=' in line:
            m = re.search(r'heading "(.+?)"', line)
            title = m.group(1) if m else ""
            
            # Look for URL nearby
            url = ""
            for j in range(max(0, i - 3), min(len(lines), i + 3)):
                if "/url:" in lines[j]:
                    candidate = lines[j].strip().split("/url:", 1)[1].strip()
                    if candidate and "duckduckgo.com" not in candidate:
                        url = candidate
                        break
            
            # Look forward for snippet
            snippet_parts = []
            k = i + 1
            while k < len(lines) and k < i + 8:
                sline = lines[k].strip()
                if sline.startswith("- heading ") or sline.startswith("- link "):
                    break
                for prefix in ["- text:", "text:", "- emphasis:", "emphasis:"]:
                    if sline.startswith(prefix):
                        snippet_parts.append(sline.split(prefix, 1)[1].strip())
                        break
                k += 1
            
            snippet = " ".join(snippet_parts).strip()
            
            if url and title:
                results.append({"title": title, "url": url, "snippet": snippet})
        i += 1
    return results


def _parse_google_results(snapshot: str) -> list:
    """Parse Google search results from Camofox snapshot text."""
    results = []
    lines = snapshot.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for search result links with heading inside
        # Pattern: - link "Title ... site https://..." [eNN]:
        #            - /url: https://actual-url
        #            - heading "Title" [level=3]
        #            - text: site description
        #          - text: snippet...
        if '- heading "' in line and '[level=3]' in line:
            # Extract title
            m = re.search(r'heading "(.+?)"', line)
            title = m.group(1) if m else ""
            
            # Look backwards for the URL
            url = ""
            for j in range(max(0, i - 3), i):
                if "/url:" in lines[j]:
                    url = lines[j].strip().split("/url:", 1)[1].strip()
                    break
            
            # Look forward for snippet text
            snippet_parts = []
            k = i + 1
            # Skip the "text: site description" line right after heading
            if k < len(lines) and "text:" in lines[k] and ("https://" in lines[k] or "http://" in lines[k]):
                k += 1
            # Collect snippet lines until next link/heading
            while k < len(lines):
                sline = lines[k].strip()
                if sline.startswith("- link ") or sline.startswith("- heading "):
                    break
                if sline.startswith("- text:"):
                    snippet_parts.append(sline.split("- text:", 1)[1].strip())
                elif sline.startswith("- emphasis:"):
                    snippet_parts.append(sline.split("- emphasis:", 1)[1].strip())
                elif sline.startswith("text:"):
                    snippet_parts.append(sline.split("text:", 1)[1].strip())
                elif sline.startswith("emphasis:"):
                    snippet_parts.append(sline.split("emphasis:", 1)[1].strip())
                k += 1
            
            snippet = " ".join(snippet_parts).strip()
            
            # Filter out non-result entries
            if url and title and not url.startswith("/search") and "google.com" not in url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })
        i += 1
    return results


if __name__ == "__main__":
    import sys
    # Usage: python3 camofox_client.py [--engine google|duckduckgo] query...
    engine = "google"
    args = sys.argv[1:]
    if "--engine" in args:
        idx = args.index("--engine")
        engine = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    query = " ".join(args) if args else "AI Agent"
    print(f"Searching ({engine}): {query}")
    results = camofox_search(query, engine=engine)
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   {r['url']}")
        print(f"   {r['snippet'][:100]}...")
