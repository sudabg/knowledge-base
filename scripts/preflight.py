#!/usr/bin/env python3
"""
工具调用预检：在 exec 前运行，返回风险评估。
用法: python3 scripts/preflight.py "<command>"
返回 JSON: {"risk": "safe|low|medium|high|critical", "reason": "...", "allow": true|false}
"""
import sys, json, re

# 危险模式
CRITICAL_PATTERNS = [
    (r'rm\s+-rf\s+/', "递归删除根目录"),
    (r'dd\s+if=.*of=/dev/', "磁盘写入"),
    (r'mkfs\.', "格式化磁盘"),
    (r':\(\)\s*\{.*\|.*&\s*\}', "Fork bomb"),
    (r'chmod\s+777\s+/', "全局可写系统目录"),
    (r'curl.*\|\s*(ba)?sh', "远程脚本直接执行"),
    (r'export\s+(OPENAI|ANTHROPIC|GEMINI|AWS|GCP|AZURE)_(API_KEY|SECRET|TOKEN)\b', "环境变量泄露 API 密钥"),
    (r'echo\s+.*[A-Za-z0-9]{32,}\s*>\s*\S*\.txt', "疑似泄露长 token 到明文文件"),
    (r'scp|rsync.*\b@\b.*:', "远程文件传输（数据外传风险）"),
    (r'base64\s+-d.*\|\s*(ba)?sh', "Base64 解码后执行（隐蔽攻击）"),
]

HIGH_PATTERNS = [
    (r'rm\s+-rf\s+\.', "递归删除当前目录"),
    (r'rm\s+-rf\s+~', "递归删除 home"),
    (r'pkill\s+-9', "强制终止进程"),
    (r'killall', "终止所有同名进程"),
    (r'>\s*/dev/sd', "直接写磁盘设备"),
    (r'iptables\s+-F', "清空防火墙规则"),
    (r'shutdown|reboot', "关机/重启"),
    (r'nc\s+-l|ncat|netcat', "开启网络监听（反弹 shell 风险）"),
    (r'chown\s+root|chgrp\s+root', "修改文件所有者为 root（提权风险）"),
    (r'sudo\s+.*(passwd|shadow|visudo)', "sudo 修改认证配置"),
]

MEDIUM_PATTERNS = [
    (r'rm\s+', "删除文件"),
    (r'git\s+reset\s+--hard', "Git 硬重置"),
    (r'git\s+clean\s+-fd', "Git 清理未跟踪文件"),
    (r'mv\s+.*\s+/dev/null', "移动到 /dev/null"),
    (r'pip\s+install|npm\s+install', "安装依赖"),
    (r'nohup', "后台运行"),
    (r'crontab\s+-e', "编辑定时任务"),
]

SENSITIVE_PATHS = [
    (r'\.ssh/', "SSH 密钥目录"),
    (r'\.env\b', "环境变量文件"),
    (r'/etc/passwd|/etc/shadow', "系统密码文件"),
    (r'openclaw\.json', "OpenClaw 配置"),
    (r'\.bashrc|\.profile', "Shell 配置文件"),
]

def check_command(cmd):
    findings = []

    for pattern, reason in CRITICAL_PATTERNS:
        if re.search(pattern, cmd):
            findings.append(("critical", reason))

    for pattern, reason in HIGH_PATTERNS:
        if re.search(pattern, cmd):
            findings.append(("high", reason))

    for pattern, reason in MEDIUM_PATTERNS:
        if re.search(pattern, cmd):
            findings.append(("medium", reason))

    for pattern, reason in SENSITIVE_PATHS:
        if re.search(pattern, cmd):
            findings.append(("medium", f"涉及敏感路径: {reason}"))

    if not findings:
        return {"risk": "safe", "reason": "无危险模式", "allow": True}

    max_risk = max(findings, key=lambda x: {"critical":4,"high":3,"medium":2,"low":1,"safe":0}[x[0]])
    reasons = [f[1] for f in findings]

    return {
        "risk": max_risk[0],
        "reason": "; ".join(reasons),
        "allow": max_risk[0] in ("safe", "low", "medium"),
        "details": [{"risk": f[0], "reason": f[1]} for f in findings]
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: preflight.py '<command>'"}))
        sys.exit(1)

    cmd = " ".join(sys.argv[1:])
    result = check_command(cmd)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["allow"]:
        sys.exit(2)
