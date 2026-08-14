# dirsearch 目录爆破笔记

> 工具版本：dirsearch 0.4.3
> 适用场景：Web 目录枚举、敏感文件发现、备份文件扫描

---

## 一、工具简介

dirsearch 是一个基于 Python 的命令行 Web 路径扫描器，使用字典枚举 Web 服务器上的目录和文件，常用于渗透测试中的资产发现阶段。

---

## 二、安装

### 2.1 从 GitHub 安装

```bash
# 克隆仓库
git clone https://github.com/maurosoria/dirsearch.git

# 安装依赖
cd dirsearch
pip3 install -r requirements.txt

# 运行
python3 dirsearch.py -h
```

### 2.2 Kali Linux 预装

```bash
# Kali 直接使用
dirsearch -h

# 或
python3 /usr/share/dirsearch/dirsearch.py -h
```

---

## 三、基本使用

### 3.1 最简扫描

```bash
python3 dirsearch.py -u http://127.0.0.1/dvwa
```

### 3.2 常用参数

```bash
# 指定目标 URL
-u URL / --url=URL

# 指定扩展名
-e PHP,HTML,TXT,Bak

# 指定字典
-w PATH / --wordlist=PATH

# 线程数（默认 25）
-t NUM / --threads=NUM

# 超时时间（默认 30s）
--timeout=NUM

# 状态码过滤（默认 200,403,500）
-i STATUS / --include-status=STATUS

# 排除状态码
-x STATUS / --exclude-status=STATUS

# 递归扫描
-r / --recursive

# 跟随重定向
-f / --follow-redirects

# 用户代理
--user-agent=AGENT

# 随机 UA
--random-agent

# 代理
--proxy=PROXY

# Cookie
--cookie=COOKIE

# 请求头
--header=HEADER

# 输出报告
--format=FORMAT
--output-path=PATH
```

---

## 四、DVWA 实战记录

### 4.1 实验场景

使用 dirsearch 对 DVWA 靶场 `http://127.0.0.1/dvwa` 进行目录爆破。

### 4.2 命令

```bash
python3 dirsearch.py -u http://127.0.0.1/dvwa -e php -t 50 -i 200,301
```

### 4.3 爆破结果

| 路径 | 状态码 | 类型 |
|---|---|---|
| `/config/` | 301 | 目录 |
| `/database/` | 301 | 目录 |
| `/setup.php` | 200 | 文件 |
| `/tests/` | 301 | 目录 |
| `/hackable/` | 301 | 目录 |
| `/index.php` | 200 | 文件 |
| `/login.php` | 200 | 文件 |
| `/logout.php` | 302 | 重定向 |
| `/security.php` | 302 | 重定向 |
| `/vulnerabilities/` | 301 | 目录 |

### 4.4 资产发现价值

#### 扫描截图

![dirsearch 对 DVWA 目录爆破过程](screenshots/tools/tools-04.png)

![dirsearch 扫描结果详情](screenshots/tools/tools-05.png)

通过目录爆破识别出以下敏感资产：

1. **`/config/`** —— DVWA 配置文件目录，可能暴露数据库密码
2. **`/database/`** —— 数据库相关文件
3. **`/setup.php`** —— 安装脚本，可重置数据库
4. **`/tests/`** —— 测试目录，可能含敏感测试数据
5. **`/hackable/uploads/`** —— 上传目录（DVWA 故意保留用于漏洞演示）

### 4.5 风险提示

**发现的备份文件残留风险**：
- 某些生产系统会保留 `*.bak`、`*.old`、`*.swp` 等备份文件
- 这些文件可能被下载导致源码泄露
- 等保测评中应纳入检查项

---

## 五、高级用法

### 5.1 自定义字典

```bash
# 使用自定义字典
python3 dirsearch.py -u http://target.com -w /path/to/custom.txt

# 常用字典路径
/usr/share/wordlists/dirb/common.txt       # Kali 预装
/usr/share/seclists/Discovery/Web-Content/  # SecLists
```

### 5.2 递归扫描

```bash
# 启用递归（会进入发现的目录继续扫描）
python3 dirsearch.py -u http://target.com -r --max-recursion-depth=3
```

### 5.3 子目录扫描

```bash
# 指定子目录
python3 dirsearch.py -u http://target.com/api -e php,html -i 200,301
```

### 5.4 绕过 403

```bash
# 使用不同请求方法绕过
python3 dirsearch.py -u http://target.com --method=POST

# 添加额外请求头
python3 dirsearch.py -u http://target.com --header="X-Forwarded-For: 127.0.0.1"

# 添加 Cookie
python3 dirsearch.py -u http://target.com --cookie="PHPSESSID=xxx"
```

### 5.5 代理模式

```bash
# 通过 Burp Suite 代理（便于查看）
python3 dirsearch.py -u http://target.com --proxy=127.0.0.1:8080

# 通过 SOCKS 代理
python3 dirsearch.py -u http://target.com --proxy=socks5://127.0.0.1:1080
```

---

## 六、报告输出

### 6.1 输出格式

```bash
# 纯文本
python3 dirsearch.py -u http://target.com --format plain -o report.txt

# JSON
python3 dirsearch.py -u http://target.com --format json -o report.json

# CSV
python3 dirsearch.py -u http://target.com --format csv -o report.csv

# XML
python3 dirsearch.py -u http://target.com --format xml -o report.xml

# Markdown
python3 dirsearch.py -u http://target.com --format md -o report.md
```

### 6.2 报告字段

```json
{
  "url": "http://target.com/admin",
  "status": 200,
  "content_length": 1234,
  "content_type": "text/html",
  "redirect": ""
}
```

---

## 七、与 dirb / gobuster 对比

| 工具 | 语言 | 优点 | 缺点 |
|---|---|---|---|
| **dirsearch** | Python | 易用、报告丰富 | 单线程模式较慢 |
| **dirb** | C | 经典工具、稳定 | 字典默认较小 |
| **gobuster** | Go | 速度快 | 配置较复杂 |
| **ffuf** | Go | 速度快、功能强 | 需要 Go 环境 |

### 7.1 gobuster 简单对比

```bash
# gobuster 目录枚举
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt -x php,html

# gobuster DNS 子域
gobuster dns -d target.com -w /usr/share/wordlists/subdomains.txt
```

### 7.2 ffuf 简单对比

```bash
# ffuf 目录枚举
ffuf -u http://target.com/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php

# ffuf POST 参数枚举
ffuf -u http://target.com/login -X POST -d "username=admin&password=FUZZ" -w password.txt
```

---

## 八、字典推荐

### 8.1 Kali 内置字典

```bash
/usr/share/wordlists/dirb/
├── common.txt          # 通用（约 4600 个）
├── big.txt             # 大字典（约 20000 个）
├── small.txt           # 小字典（约 950 个）
└── others/             # 其他专项字典

/usr/share/wordlists/seclists/
├── Discovery/Web-Content/
│   ├── common.txt
│   ├── big.txt
│   ├── PHP.fuzz.txt
│   └── backup.txt
```

### 8.2 自建字典建议

| 业务类型 | 重点词 |
|---|---|
| 通用 | admin, login, api, test, backup |
| Java 应用 | WEB-INF, META-INF |
| PHP 应用 | phpmyadmin, config, includes |
| 中国业务 | admin123, guanli, houtai |

---

## 九、合法使用边界

⚠️ **仅在授权目标上使用**：
- 本地 DVWA 靶场 ✅
- 客户书面授权的渗透测试 ✅
- 未授权系统 ❌（可能违反《网络安全法》）

### 9.1 速率控制

```bash
# 降低线程数避免对目标造成影响
python3 dirsearch.py -u http://target.com -t 10

# 增加请求间隔
python3 dirsearch.py -u http://target.com --delay=0.1
```

### 9.2 注意事项

- 高并发扫描可能触发 WAF / IDS 告警
- 部分目标对扫描行为有限速（429 响应）
- 重要目标建议人工低频扫描

---

## 十、常见问题

### 10.1 扫描结果为空

**原因**：
- 字典不匹配
- 目标有 WAF 拦截
- 状态码被过滤

**解决**：
```bash
# 尝试更多扩展名
python3 dirsearch.py -u http://target.com -e php,html,txt,aspx,jsp

# 显示所有状态码（修改 -x 不排除任何）
python3 dirsearch.py -u http://target.com -x 404
```

### 10.2 误报严重

**解决**：
- 增加状态码过滤 `-i 200,301,302`
- 排除误报路径
- 人工二次确认

### 10.3 扫描超时

**解决**：
- 减少线程 `-t 10`
- 增加超时 `--timeout=60`
- 减少字典规模

---

## 十一、参考

- dirsearch GitHub：<https://github.com/maurosoria/dirsearch>
- SecLists 字典：<https://github.com/danielmiessler/SecLists>
- OWASP Testing Guide - Information Gathering
- 仅在授权测试场景使用