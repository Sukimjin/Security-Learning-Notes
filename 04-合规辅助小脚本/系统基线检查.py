#!/usr/bin/env python3
"""
系统基线检查脚本 — 跨平台（Linux / Windows）

功能：
  - 检查开放端口
  - 列出系统用户
  - 查看运行服务
  - 检查防火墙状态
  - Linux 额外检查 SSH 配置
  - Windows 额外检查 RDP 状态

合规声明：
  本脚本仅读取系统信息用于基线巡检，不修改任何配置，
  不包含端口扫描、漏洞利用等攻击功能。

用法：
  python 系统基线检查.py                  # 输出到控制台
  python 系统基线检查.py --output report.md  # 输出到文件
  python 系统基线检查.py --help
"""

import argparse
import platform
import subprocess
import sys
from datetime import datetime


def run_cmd(cmd):
    """执行系统命令，返回输出字符串。失败返回 '[命令执行失败]'。"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return f"[命令执行失败: {e}]"


# ============================================================
# Linux 检查项
# ============================================================

def linux_open_ports():
    """检查开放端口"""
    output = run_cmd("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")
    return output if output else "[未获取到端口信息]"


def linux_users():
    """列出可登录的系统用户"""
    output = run_cmd("cat /etc/passwd | grep -E '/(bash|sh|zsh)$' | cut -d: -f1,6")
    return output if output else "[未获取到用户信息]"


def linux_services():
    """查看运行中的服务"""
    output = run_cmd("systemctl list-units --type=service --state=running --no-pager 2>/dev/null | head -30")
    return output if output else "[未获取到服务信息]"


def linux_firewall():
    """检查防火墙状态"""
    ufw = run_cmd("ufw status 2>/dev/null")
    if ufw and "not found" not in ufw.lower():
        return f"[UFW]\n{ufw}"
    iptables = run_cmd("iptables -L -n --line-numbers 2>/dev/null | head -20")
    if iptables and "not found" not in iptables.lower():
        return f"[iptables]\n{iptables}"
    firewalld = run_cmd("firewall-cmd --state 2>/dev/null")
    if firewalld and "not running" not in firewalld.lower():
        return f"[firewalld] {firewalld}"
    return "[未检测到防火墙]"


def linux_ssh_config():
    """检查 SSH 关键配置"""
    checks = []
    sshd_config = run_cmd("cat /etc/ssh/sshd_config 2>/dev/null")
    if not sshd_config or "No such file" in sshd_config:
        return "[SSH 配置文件未找到]"

    for keyword in ["PermitRootLogin", "PasswordAuthentication",
                     "Port ", "MaxAuthTries", "Protocol"]:
        for line in sshd_config.split("\n"):
            if line.strip().startswith(keyword) and not line.strip().startswith("#"):
                checks.append(line.strip())
                break
        else:
            checks.append(f"# {keyword.strip()} 未显式配置（使用默认值）")
    return "\n".join(checks)


# ============================================================
# Windows 检查项
# ============================================================

def win_open_ports():
    """检查开放端口"""
    output = run_cmd("netstat -ano | findstr LISTENING")
    return output if output else "[未获取到端口信息]"


def win_users():
    """列出系统用户"""
    output = run_cmd("net user")
    return output if output else "[未获取到用户信息]"


def win_services():
    """查看运行中的服务"""
    output = run_cmd('sc query state= active | findstr /i "SERVICE_NAME DISPLAY_NAME"')
    return output if output else "[未获取到服务信息]"


def win_firewall():
    """检查防火墙状态"""
    output = run_cmd("netsh advfirewall show allprofiles state")
    return output if output else "[未获取到防火墙信息]"


def win_rdp():
    """检查 RDP 状态"""
    output = run_cmd("reg query \"HKLM\\System\\CurrentControlSet\\Control\\Terminal Server\" /v fDenyTSConnections 2>nul")
    if "0x0" in output:
        return "RDP 状态: 已启用（fDenyTSConnections=0）\n注意 建议: 确保已配置 NLA 网络级别认证"
    elif "0x1" in output:
        return "RDP 状态: 已禁用（fDenyTSConnections=1）"
    return f"RDP 状态: {output}"


# ============================================================
# 主流程
# ============================================================

def run_checks(is_linux):
    """执行所有检查项，返回 (title, content) 列表"""
    if is_linux:
        checks = [
            ("开放端口", linux_open_ports()),
            ("可登录用户", linux_users()),
            ("运行中的服务", linux_services()),
            ("防火墙状态", linux_firewall()),
            ("SSH 配置", linux_ssh_config()),
        ]
    else:
        checks = [
            ("开放端口", win_open_ports()),
            ("系统用户", win_users()),
            ("运行中的服务", win_services()),
            ("防火墙状态", win_firewall()),
            ("RDP 状态", win_rdp()),
        ]
    return checks


def generate_report(checks, is_linux):
    """生成 Markdown 格式报告"""
    os_name = "Linux" if is_linux else "Windows"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# 系统基线检查报告",
        f"",
        f"| 项目 | 值 |",
        f"|------|-----|",
        f"| 操作系统 | {os_name} |",
        f"| 检查时间 | {timestamp} |",
        f"| 主机名 | {platform.node()} |",
        f"",
        f"---",
        f"",
    ]

    for title, content in checks:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("```")
        lines.append(content)
        lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("> 注意 本报告由系统基线检查脚本自动生成，仅包含只读检查结果。")
    lines.append("> 请根据组织安全策略人工评估各项配置是否符合基线要求。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="系统基线检查脚本（跨平台）— 仅读取系统信息，不修改任何配置"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出到指定文件（默认输出到控制台）"
    )
    args = parser.parse_args()

    is_linux = platform.system() == "Linux"
    checks = run_checks(is_linux)
    report = generate_report(checks, is_linux)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
