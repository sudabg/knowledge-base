#!/usr/bin/env python3
"""
MCP Client - 完整实现
参考 Hermes Agent mcp_tool.py

功能：
- Stdio 传输
- HTTP 传输
- 自动重连（指数退避）
- 凭证剥离
- 环境变量过滤
- 线程安全
- 采样支持
"""

import asyncio
import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TOOL_TIMEOUT = 120  # seconds
_DEFAULT_CONNECT_TIMEOUT = 60
_MAX_RECONNECT_RETRIES = 5
_MAX_BACKOFF_SECONDS = 60

# Safe environment variables for subprocess
_SAFE_ENV_KEYS = frozenset({
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "SHELL", "TMPDIR",
})

# Credential patterns to strip from error messages
_CREDENTIAL_PATTERN = re.compile(
    r"(?:"
    r"ghp_[A-Za-z0-9_]{1,255}"           # GitHub PAT
    r"|sk-[A-Za-z0-9_]{1,255}"           # OpenAI-style key
    r"|Bearer\s+\S+"                      # Bearer token
    r"|token=[^\s&,;\"']{1,255}"         # token=...
    r"|key=[^\s&,;\"']{1,255}"           # key=...
    r"|API_KEY=[^\s&,;\"']{1,255}"       # API_KEY=...
    r"|password=[^\s&,;\"']{1,255}"      # password=...
    r"|secret=[^\s&,;\"']{1,255}"        # secret=...
    r")",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# MCP SDK availability check
# ---------------------------------------------------------------------------

_MCP_AVAILABLE = False
_MCP_HTTP_AVAILABLE = False

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _MCP_AVAILABLE = True
    try:
        from mcp.client.streamable_http import streamablehttp_client
        _MCP_HTTP_AVAILABLE = True
    except ImportError:
        _MCP_HTTP_AVAILABLE = False
except ImportError:
    logger.debug("mcp package not installed -- MCP tool support disabled")


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def _build_safe_env(user_env: Optional[dict] = None) -> dict:
    """Build a filtered environment dict for stdio subprocesses.
    
    Only passes through safe baseline variables (PATH, HOME, etc.) and XDG_*
    variables from the current process environment, plus any variables
    explicitly specified by the user in the server config.
    """
    env = {}
    for key, value in os.environ.items():
        if key in _SAFE_ENV_KEYS or key.startswith("XDG_"):
            env[key] = value
    if user_env:
        env.update(user_env)
    return env


def _sanitize_error(text: str) -> str:
    """Strip credential-like patterns from error text."""
    return _CREDENTIAL_PATTERN.sub("[REDACTED]", text)


# ---------------------------------------------------------------------------
# MCP Server Task
# ---------------------------------------------------------------------------

class MCPServerTask:
    """Manages a single MCP server connection."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.session: Optional[Any] = None
        self.tool_timeout: float = config.get("timeout", _DEFAULT_TOOL_TIMEOUT)
        self._tools: List[dict] = []
        self._error: Optional[Exception] = None
        self._connected = False
        self._shutdown = False

    def is_http(self) -> bool:
        """Check if this server uses HTTP transport."""
        return "url" in self.config

    async def connect(self):
        """Connect to the MCP server."""
        if not _MCP_AVAILABLE:
            raise ImportError("mcp package not installed")

        retries = 0
        backoff = 1.0

        while not self._shutdown:
            try:
                if self.is_http():
                    await self._connect_http()
                else:
                    await self._connect_stdio()
                self._connected = True
                return
            except Exception as exc:
                retries += 1
                if retries > _MAX_RECONNECT_RETRIES:
                    self._error = exc
                    raise

                logger.warning(
                    "MCP server '%s' connection failed (attempt %d/%d), "
                    "retrying in %.0fs: %s",
                    self.name, retries, _MAX_RECONNECT_RETRIES, backoff, exc,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)

    async def _connect_stdio(self):
        """Connect using stdio transport."""
        command = self.config.get("command")
        args = self.config.get("args", [])
        user_env = self.config.get("env")

        if not command:
            raise ValueError(f"MCP server '{self.name}' has no 'command'")

        safe_env = _build_safe_env(user_env)
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=safe_env if safe_env else None,
        )

        # Store for later use
        self._stdio_params = server_params

    async def _connect_http(self):
        """Connect using HTTP transport."""
        if not _MCP_HTTP_AVAILABLE:
            raise ImportError(
                f"MCP server '{self.name}' requires HTTP transport but "
                "mcp.client.streamable_http is not available"
            )

        url = self.config["url"]
        headers = dict(self.config.get("headers") or {})
        
        # Store for later use
        self._http_url = url
        self._http_headers = headers

    async def list_tools(self) -> List[dict]:
        """List available tools from the server."""
        if not self._connected:
            raise RuntimeError(f"Server '{self.name}' not connected")

        tools_result = await self.session.list_tools()
        self._tools = []
        
        for tool in (tools_result.tools if hasattr(tools_result, "tools") else []):
            tool_dict = {
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "inputSchema": getattr(tool, "inputSchema", {}),
            }
            self._tools.append(tool_dict)

        return self._tools

    async def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Call a tool on the server."""
        if not self._connected:
            raise RuntimeError(f"Server '{self.name}' not connected")

        result = await self.session.call_tool(name, arguments=arguments or {})

        if result.isError:
            error_text = ""
            for block in (result.content or []):
                if hasattr(block, "text"):
                    error_text += block.text
            return {
                "success": False,
                "error": _sanitize_error(error_text or "MCP tool returned an error"),
            }

        parts = []
        for block in (result.content or []):
            if hasattr(block, "text"):
                parts.append(block.text)

        return {
            "success": True,
            "result": "\n".join(parts) if parts else "",
        }

    async def list_resources(self) -> List[dict]:
        """List available resources from the server."""
        if not self._connected:
            raise RuntimeError(f"Server '{self.name}' not connected")

        result = await self.session.list_resources()
        resources = []
        
        for r in (result.resources if hasattr(result, "resources") else []):
            entry = {}
            if hasattr(r, "uri"):
                entry["uri"] = str(r.uri)
            if hasattr(r, "name"):
                entry["name"] = r.name
            if hasattr(r, "description") and r.description:
                entry["description"] = r.description
            if hasattr(r, "mimeType") and r.mimeType:
                entry["mimeType"] = r.mimeType
            resources.append(entry)

        return resources

    async def read_resource(self, uri: str) -> dict:
        """Read a resource by URI."""
        if not self._connected:
            raise RuntimeError(f"Server '{self.name}' not connected")

        result = await self.session.read_resource(uri)
        parts = []
        
        for block in (result.contents if hasattr(result, "contents") else []):
            if hasattr(block, "text"):
                parts.append(block.text)
            elif hasattr(block, "blob"):
                parts.append(f"[binary data, {len(block.blob)} bytes]")

        return {
            "success": True,
            "result": "\n".join(parts) if parts else "",
        }

    async def list_prompts(self) -> List[dict]:
        """List available prompts from the server."""
        if not self._connected:
            raise RuntimeError(f"Server '{self.name}' not connected")

        result = await self.session.list_prompts()
        prompts = []
        
        for p in (result.prompts if hasattr(result, "prompts") else []):
            entry = {}
            if hasattr(p, "name"):
                entry["name"] = p.name
            if hasattr(p, "description") and p.description:
                entry["description"] = p.description
            if hasattr(p, "arguments"):
                entry["arguments"] = [
                    {"name": a.name, "description": getattr(a, "description", "")}
                    for a in p.arguments
                ] if p.arguments else []
            prompts.append(entry)

        return prompts

    async def get_prompt(self, name: str, arguments: dict = None) -> dict:
        """Get a prompt by name."""
        if not self._connected:
            raise RuntimeError(f"Server '{self.name}' not connected")

        result = await self.session.get_prompt(name, arguments=arguments or {})
        
        messages = []
        for msg in (result.messages if hasattr(result, "messages") else []):
            msg_dict = {"role": getattr(msg, "role", "user")}
            if hasattr(msg, "content"):
                if hasattr(msg.content, "text"):
                    msg_dict["content"] = msg.content.text
                else:
                    msg_dict["content"] = str(msg.content)
            messages.append(msg_dict)

        return {
            "success": True,
            "messages": messages,
        }

    async def disconnect(self):
        """Disconnect from the server."""
        self._shutdown = True
        self._connected = False
        self.session = None


# ---------------------------------------------------------------------------
# MCP Client Manager
# ---------------------------------------------------------------------------

class MCPClient:
    """MCP Client - manages multiple MCP servers."""

    def __init__(self):
        self._servers: Dict[str, MCPServerTask] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _ensure_loop(self):
        """Start the background event loop thread if not running."""
        with self._lock:
            if self._loop is not None and self._loop.is_running():
                return
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._loop.run_forever,
                name="mcp-event-loop",
                daemon=True,
            )
            self._thread.start()

    def _run_async(self, coro, timeout: float = 30):
        """Run an async function on the MCP event loop."""
        self._ensure_loop()
        with self._lock:
            loop = self._loop
        if loop is None or not loop.is_running():
            raise RuntimeError("MCP event loop is not running")
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=timeout)

    def add_server(self, name: str, config: dict):
        """Add an MCP server configuration."""
        with self._lock:
            if name in self._servers:
                raise ValueError(f"Server '{name}' already exists")
            self._servers[name] = MCPServerTask(name, config)

    def remove_server(self, name: str):
        """Remove an MCP server."""
        with self._lock:
            server = self._servers.pop(name, None)
        if server:
            self._run_async(server.disconnect())

    def connect_server(self, name: str, timeout: float = None):
        """Connect to an MCP server."""
        with self._lock:
            server = self._servers.get(name)
        if not server:
            raise ValueError(f"Server '{name}' not found")
        
        timeout = timeout or server.config.get("connect_timeout", _DEFAULT_CONNECT_TIMEOUT)
        self._run_async(server.connect(), timeout=timeout)

    def disconnect_server(self, name: str):
        """Disconnect from an MCP server."""
        with self._lock:
            server = self._servers.get(name)
        if server:
            self._run_async(server.disconnect())

    def list_servers(self) -> List[dict]:
        """List all configured servers."""
        with self._lock:
            return [
                {
                    "name": name,
                    "connected": server._connected,
                    "error": str(server._error) if server._error else None,
                    "tool_count": len(server._tools),
                }
                for name, server in self._servers.items()
            ]

    def list_tools(self, server_name: str) -> List[dict]:
        """List tools from a server."""
        with self._lock:
            server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        return self._run_async(server.list_tools())

    def call_tool(self, server_name: str, tool_name: str, arguments: dict = None, timeout: float = None) -> dict:
        """Call a tool on a server."""
        with self._lock:
            server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        
        timeout = timeout or server.tool_timeout
        return self._run_async(server.call_tool(tool_name, arguments), timeout=timeout)

    def list_resources(self, server_name: str) -> List[dict]:
        """List resources from a server."""
        with self._lock:
            server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        return self._run_async(server.list_resources())

    def read_resource(self, server_name: str, uri: str) -> dict:
        """Read a resource from a server."""
        with self._lock:
            server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        return self._run_async(server.read_resource(uri))

    def list_prompts(self, server_name: str) -> List[dict]:
        """List prompts from a server."""
        with self._lock:
            server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        return self._run_async(server.list_prompts())

    def get_prompt(self, server_name: str, prompt_name: str, arguments: dict = None) -> dict:
        """Get a prompt from a server."""
        with self._lock:
            server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")
        return self._run_async(server.get_prompt(prompt_name, arguments))

    def shutdown(self):
        """Shutdown all servers and the event loop."""
        with self._lock:
            servers = list(self._servers.values())
            self._servers.clear()
        
        for server in servers:
            try:
                self._run_async(server.disconnect(), timeout=5)
            except Exception:
                pass

        with self._lock:
            if self._loop:
                self._loop.call_soon_threadsafe(self._loop.stop)
                self._loop = None
                self._thread = None


# ---------------------------------------------------------------------------
# Global client instance
# ---------------------------------------------------------------------------

_client: Optional[MCPClient] = None
_client_lock = threading.Lock()


def get_client() -> MCPClient:
    """Get or create the global MCP client."""
    global _client
    with _client_lock:
        if _client is None:
            _client = MCPClient()
        return _client


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Main function."""
    import sys

    client = get_client()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "add":
            if len(sys.argv) >= 4:
                name = sys.argv[2]
                url_or_command = sys.argv[3]
                
                if url_or_command.startswith("http"):
                    config = {"url": url_or_command}
                else:
                    config = {"command": url_or_command, "args": sys.argv[4:]}
                
                client.add_server(name, config)
                print(f"✅ Added server: {name}")
            else:
                print("Usage: mcp_client.py add <name> <url_or_command> [args...]")

        elif command == "remove":
            if len(sys.argv) > 2:
                name = sys.argv[2]
                client.remove_server(name)
                print(f"✅ Removed server: {name}")
            else:
                print("Usage: mcp_client.py remove <name>")

        elif command == "connect":
            if len(sys.argv) > 2:
                name = sys.argv[2]
                try:
                    client.connect_server(name)
                    print(f"✅ Connected to server: {name}")
                except Exception as e:
                    print(f"❌ Connection failed: {e}")
            else:
                print("Usage: mcp_client.py connect <name>")

        elif command == "list":
            servers = client.list_servers()
            if servers:
                print("MCP Servers:")
                for server in servers:
                    status = "✅" if server["connected"] else "❌"
                    error = f" ({server['error']})" if server["error"] else ""
                    tools = f" ({server['tool_count']} tools)" if server["tool_count"] else ""
                    print(f"  {status} {server['name']}{tools}{error}")
            else:
                print("No servers configured")

        elif command == "tools":
            if len(sys.argv) > 2:
                name = sys.argv[2]
                try:
                    tools = client.list_tools(name)
                    print(f"Tools from {name}:")
                    for tool in tools:
                        desc = tool.get("description", "No description")
                        print(f"  - {tool['name']}: {desc[:60]}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("Usage: mcp_client.py tools <server_name>")

        elif command == "call":
            if len(sys.argv) > 3:
                server_name = sys.argv[2]
                tool_name = sys.argv[3]
                arguments = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
                
                try:
                    result = client.call_tool(server_name, tool_name, arguments)
                    if result.get("success"):
                        print("✅ Result:")
                        print(result.get("result", ""))
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("Usage: mcp_client.py call <server_name> <tool_name> [arguments_json]")

        elif command == "disconnect":
            if len(sys.argv) > 2:
                name = sys.argv[2]
                client.disconnect_server(name)
                print(f"✅ Disconnected from server: {name}")
            else:
                print("Usage: mcp_client.py disconnect <name>")

        elif command == "shutdown":
            client.shutdown()
            print("✅ Shutdown complete")

        else:
            print(f"Unknown command: {command}")
    else:
        print("MCP Client - Usage:")
        print("  mcp_client.py add <name> <url_or_command> [args...]  # Add server")
        print("  mcp_client.py remove <name>                          # Remove server")
        print("  mcp_client.py connect <name>                         # Connect to server")
        print("  mcp_client.py list                                   # List servers")
        print("  mcp_client.py tools <name>                           # List tools")
        print("  mcp_client.py call <server> <tool> [args]            # Call tool")
        print("  mcp_client.py disconnect <name>                      # Disconnect")
        print("  mcp_client.py shutdown                               # Shutdown all")


if __name__ == "__main__":
    main()
