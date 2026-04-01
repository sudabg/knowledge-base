#!/usr/bin/env python3
"""
危险命令检测：自动检测并阻止危险命令。
参考 Hermes Agent approval.py 实现。
"""

import os
import re
import json
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/gem/workspace/agent/workspace"))
APPROVAL_LOG = WORKSPACE / ".learnings" / "command_approval.json"
CUSTOM_RULES = WORKSPACE / ".learnings" / "command_rules.json"

# 风险级别数值映射
_RISK_LEVEL_VALUES = {
    "safe": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

def _risk_level_value(level: str) -> int:
    """获取风险级别的数值。"""
    return _RISK_LEVEL_VALUES.get(level, 0)

class RiskLevel(Enum):
    """风险级别。"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# 敏感路径检测（参考 Hermes）
_SSH_SENSITIVE_PATH = r'(?:~|\$home|\$\{home\})/\.ssh(?:/|$)'
_ENV_SENSITIVE_PATH = (
    r'(?:~\/\.hermes/|'
    r'(?:\$home|\$\{home\})/\.hermes/|'
    r'(?:\$hermes_home|\$\{hermes_home\})/)'
    r'\.env\b'
)
_SENSITIVE_WRITE_TARGET = (
    r'(?:/etc/|/dev/sd|'
    rf'{_SSH_SENSITIVE_PATH}|'
    rf'{_ENV_SENSITIVE_PATH})'
)

# 危险命令模式（参考 Hermes approval.py）
DANGEROUS_PATTERNS = [
    # SSH 敏感路径（参考 Hermes）
    (rf'\b(rm|cp|mv|chmod|chown)\b.*{_SSH_SENSITIVE_PATH}', "操作 SSH 敏感路径", RiskLevel.CRITICAL),

    # 递归删除
    (r'\brm\s+(-[^\s]*\s+)*/', "递归删除根目录", RiskLevel.CRITICAL),
    (r'\brm\s+-[^\s]*r', "递归删除", RiskLevel.HIGH),
    (r'\brm\s+--recursive\b', "递归删除（长标志）", RiskLevel.HIGH),

    # 权限修改
    (r'\bchmod\s+(-[^\s]*\s+)*(777|666|o\+[rwx]*w|a\+[rwx]*w)\b', "全局可写权限", RiskLevel.HIGH),
    (r'\bchmod\s+--recursive\b.*(777|666|o\+[rwx]*w|a\+[rwx]*w)', "递归全局可写", RiskLevel.HIGH),

    # 所有者修改
    (r'\bchown\s+(-[^\s]*)?R\s+root', "递归 chown 到 root", RiskLevel.HIGH),
    (r'\bchown\s+--recursive\b.*root', "递归 chown 到 root（长标志）", RiskLevel.HIGH),

    # 磁盘操作
    (r'\bmkfs\b', "格式化磁盘", RiskLevel.CRITICAL),
    (r'\bdd\s+.*if=', "磁盘复制", RiskLevel.HIGH),
    (r'>\s*/dev/sd', "写入块设备", RiskLevel.CRITICAL),

    # SQL 注入
    (r'\bDROP\s+(TABLE|DATABASE)\b', "SQL DROP", RiskLevel.HIGH),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "SQL DELETE without WHERE", RiskLevel.HIGH),
    (r'\bTRUNCATE\s+(TABLE)?\s*\w', "SQL TRUNCATE", RiskLevel.HIGH),

    # 系统配置
    (r'>\s*/etc/', "覆盖系统配置", RiskLevel.HIGH),
    (r'\btee\b.*["\']?{_SENSITIVE_WRITE_TARGET}', "通过 tee 覆盖系统文件", RiskLevel.HIGH),
    (r'>>?\s*["\']?{_SENSITIVE_WRITE_TARGET}', "通过重定向覆盖系统文件", RiskLevel.HIGH),

    # 系统服务
    (r'\bsystemctl\s+(stop|disable|mask)\b', "停止/禁用系统服务", RiskLevel.HIGH),

    # 进程操作
    (r'\bkill\s+-9\s+-1\b', "杀死所有进程", RiskLevel.CRITICAL),
    (r'\bpkill\s+-9\b', "强制杀死进程", RiskLevel.HIGH),

    # Fork bomb
    (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', "Fork bomb", RiskLevel.CRITICAL),

    # Shell 命令执行
    (r'\b(bash|sh|zsh|ksh)\s+-[^\s]*c(\s+|$)', "通过 -c/-lc 执行命令", RiskLevel.HIGH),
    (r'\b(python[23]?|perl|ruby|node)\s+-[ec]\s+', "通过 -e/-c 执行脚本", RiskLevel.HIGH),

    # 远程脚本执行
    (r'\b(curl|wget)\b.*\|\s*(ba)?sh\b', "管道远程内容到 shell", RiskLevel.CRITICAL),
    (r'\b(bash|sh|zsh|ksh)\s+<\s*<?\s*\(\s*(curl|wget)\b', "通过 process substitution 执行远程脚本", RiskLevel.CRITICAL),

    # xargs/find with rm
    (r'\bxargs\s+.*\brm\b', "xargs with rm", RiskLevel.HIGH),
    (r'\bfind\b.*-exec\s+(/\S*/)?rm\b', "find -exec rm", RiskLevel.HIGH),
    (r'\bfind\b.*-delete\b', "find -delete", RiskLevel.HIGH),

    # Gateway 自保护（参考 Hermes）
    (r'gateway\s+run\b.*(&\s*$|&\s*;|\bdisown\b|\bsetsid\b)', "在 systemd 外启动 gateway", RiskLevel.HIGH),
    (r'\bnohup\b.*gateway\s+run\b', "在 systemd 外启动 gateway", RiskLevel.HIGH),

    # 自我终止保护（参考 Hermes）
    (r'\b(pkill|killall)\b.*\b(hermes|gateway|cli\.py)\b', "杀死 hermes/gateway 进程", RiskLevel.HIGH),

    # sed -i 编辑系统配置（参考 Hermes）
    (r'\bsed\s+-[^\s]*i.*\s/etc/', "原地编辑系统配置", RiskLevel.HIGH),
    (r'\bsed\s+--in-place\b.*\s/etc/', "原地编辑系统配置（长标志）", RiskLevel.HIGH),

    # cp/mv/install 到系统路径（参考 Hermes）
    (r'\b(cp|mv|install)\b.*\s/etc/', "复制/移动文件到 /etc/", RiskLevel.HIGH),

    # 网络操作
    (r'\bcurl\s+', "网络请求", RiskLevel.MEDIUM),
    (r'\bwget\s+', "下载文件", RiskLevel.MEDIUM),
    (r'\bnc\s+', "网络连接", RiskLevel.MEDIUM),
    (r'\bncat\s+', "网络连接", RiskLevel.MEDIUM),
    (r'\btelnet\s+', "远程连接", RiskLevel.MEDIUM),
    (r'\bssh\s+', "SSH 连接", RiskLevel.MEDIUM),

    # 进程管理
    (r'\bps\s+aux', "查看进程", RiskLevel.LOW),
    (r'\bnetstat\s+', "查看网络状态", RiskLevel.LOW),
    (r'\bifconfig\s+', "查看网络配置", RiskLevel.LOW),
    (r'\bip\s+addr', "查看 IP 地址", RiskLevel.LOW),
]

# 受保护的路径
PROTECTED_PATHS = [
    "/", "/etc", "/usr", "/var", "/bin", "/sbin", "/lib", "/lib64",
    "/boot", "/dev", "/proc", "/sys",
    str(WORKSPACE / "MEMORY.md"),
    str(WORKSPACE / "SOUL.md"),
    str(WORKSPACE / "USER.md"),
    str(WORKSPACE / "AGENTS.md"),
]

class CommandApproval:
    """命令审批系统（参考 Hermes approval.py）。"""

    def __init__(self):
        self.custom_rules = self._load_custom_rules()
        self._lock = threading.Lock()
        self._session_states: Dict[str, Dict] = {}

    def _load_custom_rules(self) -> Dict:
        """加载自定义规则。"""
        if CUSTOM_RULES.exists():
            with open(CUSTOM_RULES, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"allowed": [], "blocked": []}

    def _save_custom_rules(self):
        """保存自定义规则。"""
        CUSTOM_RULES.parent.mkdir(parents=True, exist_ok=True)
        with open(CUSTOM_RULES, "w", encoding="utf-8") as f:
            json.dump(self.custom_rules, f, ensure_ascii=False, indent=2)

    def analyze_command(self, command: str, session_key: str = "default") -> Dict:
        """分析命令风险。"""
        with self._lock:
            result = {
                "command": command,
                "risk_level": RiskLevel.SAFE.value,
                "risks": [],
                "requires_approval": False,
                "suggestions": [],
                "timestamp": datetime.now().isoformat(),
                "session_key": session_key,
            }

            # 检查自定义白名单
            for allowed in self.custom_rules.get("allowed", []):
                if re.search(allowed, command):
                    return result

            # 检查自定义黑名单
            for blocked in self.custom_rules.get("blocked", []):
                if re.search(blocked, command):
                    result["risk_level"] = RiskLevel.HIGH.value
                    result["risks"].append(f"自定义规则阻止: {blocked}")
                    result["requires_approval"] = True
                    return result

            # 检查危险模式
            for pattern, description, level in DANGEROUS_PATTERNS:
                if re.search(pattern, command):
                    result["risks"].append(f"{level.value}: {description}")
                    # 更新风险级别（取最高级别）
                    if _risk_level_value(level.value) > _risk_level_value(result["risk_level"]):
                        result["risk_level"] = level.value

            # 检查受保护路径
            for protected in PROTECTED_PATHS:
                if protected in command:
                    result["risks"].append(f"操作受保护路径: {protected}")
                    # 如果当前是 SAFE，提升到 MEDIUM
                    if result["risk_level"] == RiskLevel.SAFE.value:
                        result["risk_level"] = RiskLevel.MEDIUM.value

            # 决定是否需要审批
            if result["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
                result["requires_approval"] = True
                result["suggestions"].append("建议使用 trash 代替 rm")
                result["suggestions"].append("建议先备份再执行")

            return result

    def approve_command(self, command: str, session_key: str = "default") -> bool:
        """审批命令（需要用户确认）。"""
        analysis = self.analyze_command(command, session_key)

        if not analysis["requires_approval"]:
            return True

        print(f"⚠️ 命令需要审批:")
        print(f"  命令: {command}")
        print(f"  风险: {analysis['risk_level']}")
        for risk in analysis["risks"]:
            print(f"  - {risk}")
        print()
        print("建议:")
        for suggestion in analysis["suggestions"]:
            print(f"  - {suggestion}")
        print()

        response = input("是否继续执行？(y/N): ")
        approved = response.lower() in ["y", "yes"]

        # 记录审批决策
        self.log_decision(command, approved, session_key)

        return approved

    def add_allowed_pattern(self, pattern: str):
        """添加允许的模式。"""
        with self._lock:
            if pattern not in self.custom_rules["allowed"]:
                self.custom_rules["allowed"].append(pattern)
                self._save_custom_rules()

    def add_blocked_pattern(self, pattern: str):
        """添加阻止的模式。"""
        with self._lock:
            if pattern not in self.custom_rules["blocked"]:
                self.custom_rules["blocked"].append(pattern)
                self._save_custom_rules()

    def log_decision(self, command: str, approved: bool, session_key: str = "default", reason: str = ""):
        """记录审批决策。"""
        with self._lock:
            APPROVAL_LOG.parent.mkdir(parents=True, exist_ok=True)

            logs = []
            if APPROVAL_LOG.exists():
                with open(APPROVAL_LOG, "r", encoding="utf-8") as f:
                    logs = json.load(f)

            logs.append({
                "command": command,
                "approved": approved,
                "session_key": session_key,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            })

            with open(APPROVAL_LOG, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

def main():
    """主函数。"""
    import sys

    approval = CommandApproval()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            if len(sys.argv) > 2:
                cmd = " ".join(sys.argv[2:])
                analysis = approval.analyze_command(cmd)
                print(json.dumps(analysis, ensure_ascii=False, indent=2))
            else:
                print("用法: command_approval.py check <command>")

        elif command == "approve":
            if len(sys.argv) > 2:
                cmd = " ".join(sys.argv[2:])
                if approval.approve_command(cmd):
                    print("✅ 命令已批准")
                else:
                    print("❌ 命令被拒绝")
            else:
                print("用法: command_approval.py approve <command>")

        elif command == "allow":
            if len(sys.argv) > 2:
                pattern = sys.argv[2]
                approval.add_allowed_pattern(pattern)
                print(f"✅ 已添加允许模式: {pattern}")
            else:
                print("用法: command_approval.py allow <pattern>")

        elif command == "block":
            if len(sys.argv) > 2:
                pattern = sys.argv[2]
                approval.add_blocked_pattern(pattern)
                print(f"✅ 已添加阻止模式: {pattern}")
            else:
                print("用法: command_approval.py block <pattern>")

        elif command == "history":
            if APPROVAL_LOG.exists():
                with open(APPROVAL_LOG, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                print("审批历史:")
                for log in logs[-10:]:
                    status = "✅" if log["approved"] else "❌"
                    print(f"  {status} {log['timestamp']} - {log['command'][:50]}")
            else:
                print("暂无审批历史")

        else:
            print(f"未知命令: {command}")
    else:
        print("命令审批系统 - 用法:")
        print("  python3 command_approval.py check <command>  # 检查命令风险")
        print("  python3 command_approval.py approve <command>  # 审批命令")
        print("  python3 command_approval.py allow <pattern>  # 添加允许模式")
        print("  python3 command_approval.py block <pattern>  # 添加阻止模式")
        print("  python3 command_approval.py history          # 查看历史")

if __name__ == "__main__":
    main()
