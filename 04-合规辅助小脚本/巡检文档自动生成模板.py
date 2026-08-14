#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巡检文档自动生成模板
=====================

功能说明：
    根据内置巡检检查项模板，自动生成 Markdown 格式的安全现场巡检报告。
    支持交互式录入检查结果，也可通过 CSV 文件批量导入。

    本脚本仅用于合规巡检辅助，不包含任何攻击或渗透功能。

使用方式：
    方式一（交互式）：
        python 巡检文档自动生成模板.py --interactive

    方式二（CSV 批量导入）：
        python 巡检文档自动生成模板.py --csv 巡检结果.csv --inspector 张三 --target Web服务器

    方式三（生成空白模板 CSV）：
        python 巡检文档自动生成模板.py --export-template 巡检模板.csv

CSV 格式说明：
    列：序号,类别,检查项,检查方法,结果,备注
    结果列填写：符合 / 不符合 / 不适用

依赖：仅使用 Python 标准库，无需安装第三方包

作者：Security-Learning-Notes 项目
日期：2026-08
"""

import argparse
import csv
import os
import sys
from datetime import datetime


# ============================================================
# 内置巡检检查项模板
# ============================================================

INSPECTION_ITEMS = [
    # --- 网络设备 ---
    {"序号": 1, "类别": "网络设备", "检查项": "设备登录口令复杂度", "检查方法": "查看配置文件，确认口令长度≥8位且包含大小写、数字、特殊字符"},
    {"序号": 2, "类别": "网络设备", "检查项": "SSH/Telnet 远程管理方式", "检查方法": "确认禁用 Telnet，仅允许 SSH v2"},
    {"序号": 3, "类别": "网络设备", "检查项": "ACL 访问控制列表", "检查方法": "确认仅允许运维网段访问管理端口"},
    {"序号": 4, "类别": "网络设备", "检查项": "固件版本与安全补丁", "检查方法": "对比厂商最新版本，确认无已知高危漏洞"},
    {"序号": 5, "类别": "网络设备", "检查项": "日志审计功能", "检查方法": "确认日志已发送至日志服务器且留存周期≥6个月"},
    {"序号": 6, "类别": "网络设备", "检查项": "NTP 时间同步", "检查方法": "确认已配置 NTP 且时间偏差<1秒"},
    {"序号": 7, "类别": "网络设备", "检查项": "不必要端口关闭", "检查方法": "执行 port scan 确认仅开放业务必须端口"},

    # --- Linux 服务器 ---
    {"序号": 8, "类别": "Linux服务器", "检查项": "root 远程登录限制", "检查方法": "检查 /etc/ssh/sshd_config 中 PermitRootLogin 设置为 no"},
    {"序号": 9, "类别": "Linux服务器", "检查项": "口令策略配置", "检查方法": "检查 /etc/security/pwquality.conf 和 /etc/login.defs"},
    {"序号": 10, "类别": "Linux服务器", "检查项": "账户锁定策略", "检查方法": "确认 pam_faillock 或 pam_tally2 配置连续失败5次锁定"},
    {"序号": 11, "类别": "Linux服务器", "检查项": "文件权限基线", "检查方法": "检查关键目录权限：/etc/passwd 644, /etc/shadow 000"},
    {"序号": 12, "类别": "Linux服务器", "检查项": "防火墙启用状态", "检查方法": "执行 ufw status 或 firewall-cmd --state 确认已启用"},
    {"序号": 13, "类别": "Linux服务器", "检查项": "日志审计配置", "检查方法": "确认 rsyslog 服务运行且日志远程转发已配置"},
    {"序号": 14, "类别": "Linux服务器", "检查项": "定时任务安全", "检查方法": "检查 /etc/crontab 和 /var/spool/cron 无异常任务"},
    {"序号": 15, "类别": "Linux服务器", "检查项": "异常进程排查", "检查方法": "执行 ps aux 确认无未知高危进程"},
    {"序号": 16, "类别": "Linux服务器", "检查项": "SUID 文件检查", "检查方法": "执行 find / -perm -4000 确认无异常 SUID 文件"},

    # --- Windows 服务器 ---
    {"序号": 17, "类别": "Windows服务器", "检查项": "账户策略配置", "检查方法": "secpol.msc 检查密码复杂度、最短长度12位、最长留存90天"},
    {"序号": 18, "类别": "Windows服务器", "检查项": "账户锁定策略", "检查方法": "确认失败登录5次后锁定30分钟"},
    {"序号": 19, "类别": "Windows服务器", "检查项": "远程桌面安全", "检查方法": "确认 RDP 仅允许指定IP段访问，网络级别身份验证(NLA)已启用"},
    {"序号": 20, "类别": "Windows服务器", "检查项": "Windows 防火墙", "检查方法": "确认三种网络配置文件防火墙均已启用"},
    {"序号": 21, "类别": "Windows服务器", "检查项": "补丁更新状态", "检查方法": "确认最近3个月内高危补丁已安装"},
    {"序号": 22, "类别": "Windows服务器", "检查项": "事件审计策略", "检查方法": "确认登录事件、对象访问、特权使用审计已启用"},
    {"序号": 23, "类别": "Windows服务器", "检查项": "来宾账户禁用", "检查方法": "确认 Guest 账户已禁用"},
    {"序号": 24, "类别": "Windows服务器", "检查项": "UAC 用户账户控制", "检查方法": "确认 UAC 级别不低于默认级别"},

    # --- 数据库 ---
    {"序号": 25, "类别": "数据库", "检查项": "数据库账户口令复杂度", "检查方法": "确认所有账户口令长度≥12位且包含多种字符类型"},
    {"序号": 26, "类别": "数据库", "检查项": "多余账户清理", "检查方法": "确认无测试账户、默认账户(如sa/root)已改名或禁用"},
    {"序号": 27, "类别": "数据库", "检查项": "权限最小化", "检查方法": "确认应用账户仅拥有必要库表的最小权限，无 ALL PRIVILEGES"},
    {"序号": 28, "类别": "数据库", "检查项": "审计日志启用", "检查方法": "确认数据库审计已启用且日志留存≥6个月"},
    {"序号": 29, "类别": "数据库", "检查项": "远程访问限制", "检查方法": "确认数据库仅监听内网地址，不对公网开放"},
    {"序号": 30, "类别": "数据库", "检查项": "备份策略", "检查方法": "确认定期自动备份且已验证备份可恢复"},

    # --- Web 应用 ---
    {"序号": 31, "类别": "Web应用", "检查项": "HTTPS 强制跳转", "检查方法": "确认 HTTP 请求自动 301 跳转到 HTTPS"},
    {"序号": 32, "类别": "Web应用", "检查项": "SQL 注入防护", "检查方法": "确认使用预编译语句或 ORM 框架"},
    {"序号": 33, "类别": "Web应用", "检查项": "XSS 防护", "检查方法": "确认输出转义函数已启用，CSP 头部已配置"},
    {"序号": 34, "类别": "Web应用", "检查项": "文件上传限制", "检查方法": "确认上传类型白名单、文件重命名、存储目录不可执行"},
    {"序号": 35, "类别": "Web应用", "检查项": "CSRF 防护", "检查方法": "确认 Token 校验或 SameSite Cookie 已配置"},
    {"序号": 36, "类别": "Web应用", "检查项": "会话管理", "检查方法": "确认 Session ID 随机化、超时自动失效、Cookie HttpOnly+Secure"},
    {"序号": 37, "类别": "Web应用", "检查项": "错误信息处理", "检查方法": "确认生产环境关闭详细错误回显，统一错误页面"},
    {"序号": 38, "类别": "Web应用", "检查项": "WAF 防护", "检查方法": "确认 WAF 已部署且规则库为最新版本"},

    # --- 安全设备 ---
    {"序号": 39, "类别": "安全设备", "检查项": "防火墙规则审查", "检查方法": "确认规则遵循最小权限原则，无 any-any 放行规则"},
    {"序号": 40, "类别": "安全设备", "检查项": "IDS/IDS 规则更新", "检查方法": "确认特征库为最近1周内更新"},
    {"序号": 41, "类别": "安全设备", "检查项": "安全设备高可用", "检查方法": "确认主备切换功能正常，心跳线状态正常"},
    {"序号": 42, "类别": "安全设备", "检查项": "管理口隔离", "检查方法": "确认管理口与业务口物理或逻辑隔离"},
]


# ============================================================
# 报告生成核心逻辑
# ============================================================

def generate_report(inspector, target, inspection_date, results):
    """
    生成 Markdown 格式的巡检报告

    参数:
        inspector: 巡检人员姓名
        target: 巡检目标系统名称
        inspection_date: 巡检日期 (YYYY-MM-DD)
        results: list of dict, 每项包含 序号/类别/检查项/检查方法/结果/备注

    返回:
        str: Markdown 格式的完整报告文本
    """
    lines = []

    # --- 报告头部 ---
    lines.append(f"# 安全现场巡检报告")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 巡检目标 | {target} |")
    lines.append(f"| 巡检人员 | {inspector} |")
    lines.append(f"| 巡检日期 | {inspection_date} |")
    lines.append(f"| 报告生成时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    lines.append("")

    # --- 巡检摘要 ---
    total = len(results)
    passed = sum(1 for r in results if r.get("结果", "").strip() == "符合")
    failed = sum(1 for r in results if r.get("结果", "").strip() == "不符合")
    not_applicable = sum(1 for r in results if r.get("结果", "").strip() == "不适用")
    pending = total - passed - failed - not_applicable

    lines.append("## 巡检摘要")
    lines.append("")
    lines.append(f"| 指标 | 数量 | 占比 |")
    lines.append(f"|------|------|------|")
    lines.append(f"| 检查项总数 | {total} | 100% |")
    lines.append(f"| 符合 | {passed} | {passed/total*100:.1f}% |" if total else "| 符合 | 0 | 0% |")
    lines.append(f"| 不符合 | {failed} | {failed/total*100:.1f}% |" if total else "| 不符合 | 0 | 0% |")
    lines.append(f"| 不适用 | {not_applicable} | {not_applicable/total*100:.1f}% |" if total else "| 不适用 | 0 | 0% |")
    if pending > 0:
        lines.append(f"| 待检查 | {pending} | {pending/total*100:.1f}% |")
    lines.append("")

    # 风险提示
    if failed > 0:
        lines.append(f"> **提示**：共发现 {failed} 项不符合项，请参照下方详细记录制定整改计划。")
    else:
        lines.append(f"> **提示**：所有检查项均符合要求或为不适用项。")
    lines.append("")

    # --- 按类别分组的检查明细 ---
    lines.append("## 检查明细")
    lines.append("")

    # 按"类别"分组
    categories = {}
    for item in results:
        cat = item.get("类别", "未分类")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    for cat_name, cat_items in categories.items():
        lines.append(f"### {cat_name}")
        lines.append("")
        lines.append(f"| 序号 | 检查项 | 检查方法 | 结果 | 备注 |")
        lines.append(f"|------|--------|----------|------|------|")
        for item in cat_items:
            seq = item.get("序号", "")
            check_item = item.get("检查项", "")
            method = item.get("检查方法", "")
            result = item.get("结果", "")
            remark = item.get("备注", "")

            # 结果标记
            if result == "符合":
                result_mark = "符合 ✅"
            elif result == "不符合":
                result_mark = "不符合 ❌"
            elif result == "不适用":
                result_mark = "不适用 ➖"
            else:
                result_mark = result or "待检查 ⬜"

            lines.append(f"| {seq} | {check_item} | {method} | {result_mark} | {remark} |")
        lines.append("")

    # --- 不符合项整改建议 ---
    failed_items = [r for r in results if r.get("结果", "").strip() == "不符合"]
    if failed_items:
        lines.append("## 不符合项整改建议")
        lines.append("")
        lines.append("| 序号 | 类别 | 检查项 | 建议整改措施 | 整改优先级 |")
        lines.append("|------|------|--------|-------------|-----------|")
        for item in failed_items:
            seq = item.get("序号", "")
            cat = item.get("类别", "")
            check_item = item.get("检查项", "")
            remark = item.get("备注", "请根据检查方法进行整改")
            # 简单的优先级判定：数据库和Web应用的不符合项为高，其余为中
            if cat in ("数据库", "Web应用", "安全设备"):
                priority = "高"
            elif cat in ("Linux服务器", "Windows服务器"):
                priority = "中"
            else:
                priority = "中"
            lines.append(f"| {seq} | {cat} | {check_item} | {remark} | {priority} |")
        lines.append("")

    # --- 签字确认 ---
    lines.append("## 签字确认")
    lines.append("")
    lines.append("| 角色 | 姓名 | 签字 | 日期 |")
    lines.append("|------|------|------|------|")
    lines.append(f"| 巡检人员 | {inspector} | | {inspection_date} |")
    lines.append("| 系统管理员 | | | |")
    lines.append("| 安全负责人 | | | |")
    lines.append("")

    # --- 报告尾部 ---
    lines.append("---")
    lines.append("")
    lines.append("*本报告由 Security-Learning-Notes 巡检文档自动生成模板.py 自动生成，仅供学习与合规巡检辅助使用。*")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# 交互式录入
# ============================================================

def interactive_mode():
    """
    交互式录入巡检结果，逐项询问检查结果和备注
    """
    print("=" * 60)
    print("  安全现场巡检报告 - 交互式录入")
    print("=" * 60)
    print()

    inspector = input("请输入巡检人员姓名: ").strip() or "巡检员"
    target = input("请输入巡检目标系统名称: ").strip() or "目标系统"
    inspection_date = input(f"请输入巡检日期 (回车默认今天 {datetime.now().strftime('%Y-%m-%d')}): ").strip()
    if not inspection_date:
        inspection_date = datetime.now().strftime("%Y-%m-%d")

    print()
    print(f"共 {len(INSPECTION_ITEMS)} 项检查项，请逐项录入结果。")
    print("输入说明: 1=符合, 2=不符合, 3=不适用, 回车=跳过(待检查)")
    print()

    results = []
    for item in INSPECTION_ITEMS:
        print(f"[{item['序号']}/{len(INSPECTION_ITEMS)}] [{item['类别']}] {item['检查项']}")
        print(f"  检查方法: {item['检查方法']}")

        choice = input("  结果 (1/2/3/回车): ").strip()
        if choice == "1":
            result = "符合"
        elif choice == "2":
            result = "不符合"
        elif choice == "3":
            result = "不适用"
        else:
            result = "待检查"

        remark = ""
        if result == "不符合":
            remark = input("  请输入备注/整改建议: ").strip()
        elif result == "不适用":
            remark = input("  请输入不适用原因: ").strip()

        result_item = dict(item)
        result_item["结果"] = result
        result_item["备注"] = remark
        results.append(result_item)
        print()

    return inspector, target, inspection_date, results


# ============================================================
# CSV 批量导入
# ============================================================

def csv_import(csv_path):
    """
    从 CSV 文件读取巡检结果

    CSV 列: 序号,类别,检查项,检查方法,结果,备注
    """
    results = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def export_template_csv(csv_path):
    """
    导出空白巡检模板 CSV 文件，供人工填写后导入
    """
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["序号", "类别", "检查项", "检查方法", "结果", "备注"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in INSPECTION_ITEMS:
            row = dict(item)
            row["结果"] = ""
            row["备注"] = ""
            writer.writerow(row)
    print(f"空白巡检模板已导出至: {csv_path}")
    print(f"共 {len(INSPECTION_ITEMS)} 项检查项，请在'结果'列填写: 符合 / 不符合 / 不适用")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="安全现场巡检报告自动生成工具（合规辅助，无攻击功能）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式录入并生成报告
  python %(prog)s --interactive

  # CSV 批量导入生成报告
  python %(prog)s --csv 巡检结果.csv --inspector 张三 --target Web服务器

  # 导出空白模板 CSV 供人工填写
  python %(prog)s --export-template 巡检模板.csv
        """
    )
    parser.add_argument("--interactive", action="store_true", help="交互式录入巡检结果")
    parser.add_argument("--csv", type=str, help="从 CSV 文件导入巡检结果")
    parser.add_argument("--inspector", type=str, default="巡检员", help="巡检人员姓名（配合 --csv 使用）")
    parser.add_argument("--target", type=str, default="目标系统", help="巡检目标系统名称（配合 --csv 使用）")
    parser.add_argument("--date", type=str, help="巡检日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--export-template", type=str, help="导出空白巡检模板 CSV 到指定路径")
    parser.add_argument("--output", "-o", type=str, help="输出 Markdown 文件路径（默认输出到终端）")

    args = parser.parse_args()

    # 导出模板模式
    if args.export_template:
        export_template_csv(args.export_template)
        return

    # 交互式模式
    if args.interactive:
        inspector, target, inspection_date, results = interactive_mode()
    elif args.csv:
        if not os.path.exists(args.csv):
            print(f"错误: CSV 文件不存在: {args.csv}")
            sys.exit(1)
        results = csv_import(args.csv)
        inspector = args.inspector
        target = args.target
        inspection_date = args.date or datetime.now().strftime("%Y-%m-%d")
    else:
        # 无参数时默认使用内置模板生成空白报告（所有项为待检查）
        print("未指定模式，将使用内置模板生成空白巡检报告（所有项标记为待检查）。")
        print("使用 --help 查看更多用法。")
        print()
        results = [dict(item, 结果="待检查", 备注="") for item in INSPECTION_ITEMS]
        inspector = args.inspector
        target = args.target
        inspection_date = args.date or datetime.now().strftime("%Y-%m-%d")

    # 生成报告
    report = generate_report(inspector, target, inspection_date, results)

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"巡检报告已生成: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
