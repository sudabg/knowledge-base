#!/usr/bin/env python3
"""
github_auth.py — GitHub 认证管理，自动修复 HOME 和 token 问题
用法: python3 scripts/github_auth.py [command] [args]
"""

import os
import sys
import json
import subprocess
import hashlib
from pathlib import Path

HOME_DIR = "/home/gem"
GH_CONFIG = Path(HOME_DIR) / ".config" / "gh" / "hosts.yml"
WORKSPACE = Path(HOME_DIR) / "workspace" / "agent" / "workspace"
TOOLS_FILE = WORKSPACE / "TOOLS.md"


def ensure_home():
    """Set HOME if not set."""
    if not os.environ.get("HOME"):
        os.environ["HOME"] = HOME_DIR


def get_token_from_config() -> str:
    """Read token from gh config file."""
    if GH_CONFIG.exists():
        content = GH_CONFIG.read_text()
        for line in content.split("\n"):
            if "oauth_token:" in line:
                return line.split("oauth_token:")[1].strip()
    return ""


def save_token(token: str) -> None:
    """Save token to gh config file."""
    GH_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    GH_CONFIG.write_text(f"""github.com:
    user: sudabg
    oauth_token: {token}
    git_protocol: https
""")
    GH_CONFIG.chmod(0o600)


def run_gh(args: list, timeout: int = 15) -> tuple:
    """Run gh command with proper HOME set."""
    ensure_home()
    env = os.environ.copy()
    env["HOME"] = HOME_DIR
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True,
            timeout=timeout, env=env,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def cmd_status():
    """Check gh auth status."""
    code, out, err = run_gh(["auth", "status"])
    print(out)
    if err:
        print(err)
    return code


def cmd_api(path: str):
    """Call GitHub API."""
    code, out, err = run_gh(["api", path])
    if code == 0:
        try:
            data = json.loads(out)
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(out)
    else:
        print(f"Error: {err}")
    return code


def cmd_repos():
    """List user repos."""
    code, out, err = run_gh(["repo", "list", "--limit", "10"])
    if code == 0:
        print(out)
    else:
        print(f"Error: {err}")
    return code


def cmd_create_repo(name: str, desc: str = "", private: bool = False):
    """Create a new repo."""
    args = ["repo", "create", name]
    if private:
        args.append("--private")
    else:
        args.append("--public")
    if desc:
        args.extend(["--description", desc])
    args.extend(["--source=.", "--push"])
    code, out, err = run_gh(args, timeout=60)
    if code == 0:
        print(out)
    else:
        print(f"Error: {err}")
    return code


def cmd_fix():
    """Auto-fix: ensure HOME, check config, verify auth."""
    ensure_home()
    print(f"HOME={os.environ.get('HOME')}")

    if not GH_CONFIG.exists():
        print(f"❌ Config not found: {GH_CONFIG}")
        print("Run: bash scripts/fix-github-auth.sh YOUR_TOKEN")
        return 1

    token = get_token_from_config()
    if not token:
        print("❌ No token in config")
        return 1

    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    print(f"✅ Token found (hash: {token_hash}...)")

    code, out, err = run_gh(["auth", "status"])
    if code == 0:
        print("✅ GitHub auth OK")
    else:
        print(f"❌ Auth failed: {err}")
    return code


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 github_auth.py <command> [args]")
        print("Commands: status, api, repos, create, fix")
        return 1

    cmd = sys.argv[1]
    if cmd == "status":
        return cmd_status()
    elif cmd == "api":
        return cmd_api(sys.argv[2] if len(sys.argv) > 2 else "user")
    elif cmd == "repos":
        return cmd_repos()
    elif cmd == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else "agentforge"
        desc = sys.argv[3] if len(sys.argv) > 3 else ""
        return cmd_create_repo(name, desc)
    elif cmd == "fix":
        return cmd_fix()
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
