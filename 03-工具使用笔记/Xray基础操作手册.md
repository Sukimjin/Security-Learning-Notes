# Xray 基础操作手册

> 工具版本：Xray 1.9.x（社区版）
> 适用场景：Web 漏洞自动化扫描、被动代理流量审计

---

## 一、Xray 简介

Xray 是长亭科技开发的 Web 漏洞扫描器，支持主动扫描和被动代理两种模式，覆盖 OWASP Top 10 等常见漏洞。

---

## 二、安装

### 2.1 下载

```bash
# 官方 GitHub Release
wget https://github.com/chaitin/xray/releases/download/1.9.11/xray_linux_amd64.zip

unzip xray_linux_amd64.zip

chmod +x xray_linux_amd64
sudo mv xray_linux_amd64 /usr/local/bin/xray
```

### 2.2 生成证书（被动代理需要）

```bash
xray genca

# 输出：
# ca.crt 和 ca.key.pem 在当前目录
# 导入 ca.crt 到浏览器信任（用于 HTTPS 流量解密）
```

---

## 三、扫描模式

### 3.1 主动扫描（webscan）

```bash
# 基本扫描
xray webscan --url http://192.168.1.10/dvwa

# 指定插件
xray webscan --plugins sqli,xss,xxe,ssrf --url http://target.com

# 输出 HTML 报告
xray webscan --url http://target.com --html-output report.html

# 输出 JSON 报告
xray webscan --url http://target.com --json-output report.json
```

### 3.2 被动代理（mitm）

```bash
# 启动被动代理监听
xray webscan --listen 127.0.0.1:7777 --html-output proxy_report.html

# 浏览器设置 HTTP 代理为 127.0.0.1:7777
# 浏览器正常浏览目标网站，Xray 自动分析流量
```

### 3.3 反向代理模式（高级）

```bash
# 反向代理模式
xray webscan --plugins cmd-injection,sqli --listen 0.0.0.0:8888 --reverse-proxy-target http://target.com
```

---

## 四、插件分类

### 4.1 漏洞检测插件

| 插件 | 说明 |
|---|---|
| `sqli` | SQL 注入 |
| `xss` | XSS 跨站脚本 |
| `xxe` | XML 外部实体 |
| `ssrf` | 服务端请求伪造 |
| `cmd-injection` | 命令注入 |
| `path-traversal` | 路径穿越 |
| `fileupload` | 文件上传 |
| `csrf` | CSRF |
| `brute-force` | 暴力破解 |
| `dirscan` | 目录扫描 |
| `redirect` | 重定向漏洞 |
| `crlf-injection` | CRLF 注入 |

### 4.2 基础能力插件

| 插件 | 说明 |
|---|---|
| `baseline` | 基线检查（缺少安全头等） |
| `detection` | 检测通用 Web 特征 |
| `fingerprint` | 指纹识别 |

### 4.3 指纹识别插件

| 插件 | 说明 |
|---|---|
| `vuln` | 漏洞指纹 |
| `tech` | 技术栈指纹 |

---

## 五、DVWA 实战记录

### 5.1 第一次实战：Xray 代理扫描 DVWA

**场景**：使用 Xray 代理模式扫描 DVWA 靶场

**操作过程**：
```bash
# 1. 启动 Xray 代理监听
xray webscan --listen 127.0.0.1:7777 --html-output dvwa_scan.html

# 2. 设置浏览器代理为 127.0.0.1:7777

# 3. 浏览器访问 http://127.0.0.1/dvwa
```

**问题记录**：
```
DVWA 需要登录才能访问漏洞模块。
浏览器流量未被代理完整捕获（DVWA 登录会话 Cookie 未被拦截），
导致 Xray 自动化扫描未产出漏洞报告。
```

**原因分析**：
1. DVWA 的 Session Cookie 是 HttpOnly，JavaScript 无法读取
2. Xray 仅拦截 HTTP/HTTPS 协议层流量，不注入 JS 提取 Cookie
3. 浏览器中已登录状态未走代理

**解决方案**：
- 通过 Burp Suite 手动完成漏洞验证（更可控）
- 或使用 Xray 的「主动扫描 + Cookie」模式（需指定 Cookie）

### 5.2 手动指定 Cookie 扫描

```bash
# 1. 从浏览器获取 PHPSESSID
# 2. 配置 Cookie 扫描
xray webscan --plugins sqli,xss,cmd-injection \
    --url "http://127.0.0.1/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit" \
    --headers "Cookie: PHPSESSID=xxx; security=low"

# 输出报告
xray webscan --plugins sqli --url ... --json-output /tmp/scan.json
```

### 5.3 实战经验总结

#### Xray 扫描截图

![Xray 代理模式启动与监听](screenshots/tools/tools-06.png)

![Xray 漏洞扫描报告](screenshots/tools/tools-07.png)

| 经验 | 说明 |
|------|------|
| 主动扫描需登录态 | 多数 Web 应用漏洞模块需登录，使用代理模式需正确捕获 Cookie |
| 配合 Burp Suite | Xray 自动化扫描 + Burp 手工验证，效率最佳 |
| 扫描并发控制 | 多目标扫描时使用 `--limit-rate` 控制速率 |
| 报告归档 | 报告按客户 + 日期分类保存 |

---

## 六、报告输出

### 6.1 HTML 报告

```bash
xray webscan --url http://target.com --html-output report_$(date +%Y%m%d).html
```

### 6.2 JSON 报告（程序化处理）

```bash
xray webscan --url http://target.com --json-output report.json

# 解析 JSON
cat report.json | jq '.[] | {target, vuln_type, severity, detail}'
```

### 6.3 输出字段

```json
{
  "target": "http://target.com/api?id=1",
  "vuln_type": "sqli",
  "severity": "high",
  "detail": {
    "param": "id",
    "payload": "1' AND 1=1 --",
    "evidence": "返回内容差异"
  },
  "request": "...",
  "response": "..."
}
```

---

## 七、高级功能

### 7.1 配置 YAML 文件

```yaml
# config.yaml
plugins:
  sqli:
    enabled: true
    intensity: high
  xss:
    enabled: true
    intensity: medium

proxy:
  http: http://127.0.0.1:8080

allowHosts:
  - "*127.0.0.1*"
  - "*target.com*"

denyHosts:
  - "*logout*"
```

```bash
xray webscan --config config.yaml --url http://target.com
```

### 7.2 子域名收集

```bash
xray subdomains --target target.com
```

### 7.3 POC 自定义

```bash
# Xray 内置 POC 库
xray webscan --poc ./pocs/ --url http://target.com
```

---

## 八、注意事项

### 8.1 合法使用边界

⚠️ **仅在授权目标上使用**：
- 本地 DVWA 靶场 ✅
- 客户书面授权的目标 ✅
- 未授权系统 ❌（可能违反《网络安全法》）

### 8.2 速率控制

```bash
# 控制扫描速率（避免对目标造成 DoS）
xray webscan --url http://target.com --limit-rate 100
```

### 8.3 与其他工具联动

| 工具 | 联动方式 |
|---|---|
| **Burp Suite** | Burp 作为代理上游 → Xray 作为代理下游 |
| **rad（爬虫）** | Xray + rad 实现深度爬取 + 漏洞扫描 |
| **AWVS** | 报告对比验证 |

---

## 九、常见问题

### 9.1 主动扫描返回空

- 目标无明显漏洞
- 目标有 WAF / IPS 拦截
- 目标需要登录（Cookie 缺失）

### 9.2 代理模式无流量

- 检查浏览器代理设置
- 检查 Xray 证书是否导入浏览器（HTTPS）
- 检查防火墙是否放行监听端口

### 9.3 报告文件大

```bash
# 仅输出关键漏洞
xray webscan --plugins sqli,xss --url ... --html-output report.html
```

---

## 十、参考

- Xray 官方文档：<https://docs.xray.cool/>
- Xray GitHub：<https://github.com/chaitin/xray>
- 长亭科技：<https://www.chaitin.cn/>
- 实战经验：以 Burp Suite 手工测试为主，Xray 作为辅助