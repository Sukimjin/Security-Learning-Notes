#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志简单解析工具（合规辅助脚本）
=================================

用途：解析 Apache / Nginx 访问日志，生成异常 IP、访问频次、状态码分布等统计信息。

注意 重要声明：
    本脚本为日志统计分析工具，**不包含任何攻击功能**。
    仅用于安全运维日志审计、巡检报告数据支撑。
    严禁用于未授权系统的攻击或数据窃取。

支持的日志格式：
    - Apache Combined Log Format（含 Referer 和 User-Agent）
    - Nginx 默认日志格式（与 Apache Combined 类似）

格式限制：
    - 仅支持 IPv4 地址（IPv6 日志行将被跳过）
    - 仅支持 Combined 格式（Common 格式缺少 Referer/UA 字段，无法完整解析）
    - 不支持 JSON 格式日志（如 Nginx 自定义 JSON 日志）

使用方法：
    python3 日志简单解析.py <日志文件路径> [选项]

示例：
    python3 日志简单解析.py /var/log/apache2/access.log
    python3 日志简单解析.py access.log -t 50          # 展示前 50 条
    python3 日志简单解析.py access.log --top-n 50      # 同上（长参数）
    python3 日志简单解析.py --help                      # 查看完整帮助

作者：Security-Learning-Notes
版本：V1.0
"""

import sys
import re
import argparse
from collections import Counter, defaultdict
from datetime import datetime


# Apache Combined Log Format 正则
LOG_PATTERN = re.compile(
    r'(?P<ip>\d+\.\d+\.\d+\.\d+)\s+'  # 客户端 IP
    r'\S+\s+'                          # identd
    r'\S+\s+'                          # 用户
    r'\[(?P<time>[^\]]+)\]\s+'        # 时间
    r'"(?P<method>[A-Z]+)\s+'         # 请求方法
    r'(?P<url>[^\s"]+)\s+'           # URL
    r'(?P<protocol>HTTP/[\d.]+)"\s+'  # 协议
    r'(?P<status>\d{3})\s+'          # 状态码
    r'(?P<size>\d+|-)\s+'             # 响应大小
    r'"(?P<referer>[^"]*)"\s+'       # Referer
    r'"(?P<useragent>[^"]*)"'        # User-Agent
)


def parse_log_file(filepath):
    """
    逐行解析日志文件，返回解析后的记录列表。
    解析失败的行将被跳过并打印警告。
    """
    records = []
    parse_errors = 0

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                match = LOG_PATTERN.match(line)
                if match:
                    records.append({
                        'ip': match.group('ip'),
                        'time': match.group('time'),
                        'method': match.group('method'),
                        'url': match.group('url'),
                        'protocol': match.group('protocol'),
                        'status': match.group('status'),
                        'size': match.group('size'),
                        'referer': match.group('referer'),
                        'useragent': match.group('useragent'),
                    })
                else:
                    parse_errors += 1
    except FileNotFoundError:
        print(f'[ERROR] 文件不存在: {filepath}')
        sys.exit(1)
    except PermissionError:
        print(f'[ERROR] 无权限读取: {filepath}')
        sys.exit(1)

    print(f'[INFO] 解析完成: 共 {len(records)} 条记录，{parse_errors} 行解析失败')
    return records


def analyze_records(records, top_n=20):
    """
    分析日志记录，生成多维度统计报告。
    """
    print()
    print('=' * 70)
    print(f'日志分析报告  生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    # 1. 访问量 Top IP
    print()
    print(f'【1】访问频次 TOP {top_n} IP')
    print('-' * 70)
    ip_counter = Counter(r['ip'] for r in records)
    for ip, count in ip_counter.most_common(top_n):
        print(f'  {ip:<20s}  访问次数: {count}')

    # 2. 状态码分布
    print()
    print('【2】HTTP 状态码分布')
    print('-' * 70)
    status_counter = Counter(r['status'] for r in records)
    total = sum(status_counter.values())
    for status in sorted(status_counter.keys()):
        count = status_counter[status]
        pct = (count / total * 100) if total else 0
        desc = {
            '200': '成功', '201': '已创建', '204': '无内容',
            '301': '永久重定向', '302': '临时重定向', '304': '未修改',
            '400': '客户端错误', '401': '未授权', '403': '禁止访问',
            '404': '未找到', '405': '方法不允许',
            '500': '服务器错误', '502': '网关错误', '503': '服务不可用',
        }.get(status, '其他')
        print(f'  {status} ({desc:<8s})  {count:>6d}  占比: {pct:.2f}%')

    # 3. 高频访问 URL
    print()
    print(f'【3】访问频次 TOP {top_n} URL')
    print('-' * 70)
    url_counter = Counter(r['url'] for r in records)
    for url, count in url_counter.most_common(top_n):
        print(f'  {count:>5d}  {url[:80]}')

    # 4. HTTP 方法分布
    print()
    print('【4】HTTP 方法分布')
    print('-' * 70)
    method_counter = Counter(r['method'] for r in records)
    for method, count in method_counter.most_common():
        pct = (count / total * 100) if total else 0
        print(f'  {method:<10s}  {count:>6d}  占比: {pct:.2f}%')

    # 5. 可疑请求检测（OWASP Top 10 关键字）
    print()
    print('【5】可疑请求检测（OWASP Top 10 特征匹配）')
    print('-' * 70)
    suspicious_patterns = {
        'SQL 注入': re.compile(r'(?i)(union.*select|select.*from|concat\(|benchmark|sleep\(|extractvalue|load_file|0x[0-9a-f]+)'),
        'XSS 跨站': re.compile(r'(?i)(<script|onerror=|onload=|javascript:|alert\(|prompt\()'),
        '路径穿越': re.compile(r'(?i)(\.\./|\.\.\\|%2e%2e)'),
        '命令注入': re.compile(r'(?i)(;|\||&&|\$\(|`|nc\s|curl\s|wget\s)'),
        '文件包含': re.compile(r'(?i)(php://|file://|data:|expect://|phar://)'),
        '扫描工具 UA': re.compile(r'(?i)(sqlmap|nmap|nikto|dirbuster|masscan|wpscan|acunetix|nessus|burp)'),
    }

    suspicious_count = 0
    for category, pattern in suspicious_patterns.items():
        matching_records = [r for r in records if pattern.search(r['url']) or pattern.search(r['useragent'])]
        if matching_records:
            print(f'  [{category}] 命中 {len(matching_records)} 次:')
            suspicious_count += len(matching_records)
            for r in matching_records[:5]:  # 仅显示前 5 条
                print(f'    {r["ip"]:<18s}  {r["method"]:<6s}  {r["url"][:60]}')
            if len(matching_records) > 5:
                print(f'    ... 还有 {len(matching_records) - 5} 条')

    print()
    print(f'  共发现可疑请求 {suspicious_count} 条，建议人工核查')

    # 6. 4xx/5xx 错误来源 IP
    print()
    print(f'【6】错误请求（4xx/5xx）来源 TOP {top_n} IP')
    print('-' * 70)
    error_ips = Counter(
        r['ip'] for r in records
        if r['status'].startswith('4') or r['status'].startswith('5')
    )
    for ip, count in error_ips.most_common(top_n):
        print(f'  {ip:<20s}  错误次数: {count}')

    # 7. 高频 404 IP（可能目录爆破）
    print()
    print(f'【7】高频 404 请求 TOP {top_n} IP（可能存在目录爆破）')
    print('-' * 70)
    not_found_ips = Counter(
        r['ip'] for r in records if r['status'] == '404'
    )
    for ip, count in not_found_ips.most_common(top_n):
        if count >= 5:  # 仅显示超过 5 次的 IP
            print(f'  {ip:<20s}  404 次数: {count}')

    print()
    print('=' * 70)
    print('分析完成。建议将以上数据写入巡检报告。')
    print('=' * 70)


def main():
    """
    入口函数：解析命令行参数并执行日志分析。
    """
    parser = argparse.ArgumentParser(
        description="Apache/Nginx 访问日志解析工具（合规辅助脚本）",
        epilog=(
            "示例:\n"
            "  python3 日志简单解析.py /var/log/apache2/access.log\n"
            "  python3 日志简单解析.py access.log -t 50\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "logfile",
        help="日志文件路径（Apache Combined / Nginx 默认格式）",
    )
    parser.add_argument(
        "-t", "--top-n",
        type=int,
        default=20,
        metavar="N",
        help="每项统计展示前 N 条（默认: 20）",
    )

    args = parser.parse_args()

    print(f"开始解析日志: {args.logfile}")
    records = parse_log_file(args.logfile)

    if not records:
        print("[WARN] 无有效记录，退出")
        sys.exit(0)

    analyze_records(records, args.top_n)


if __name__ == '__main__':
    main()