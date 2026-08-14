# Burp Suite 基础使用笔记

> 工具版本：Burp Suite Community Edition 2023.10
> 适用场景：Web 渗透测试、手工漏洞验证、请求拦截与重放

---

## 一、工具简介

Burp Suite 是 Web 应用安全测试的事实标准工具，由 PortSwigger 公司开发。社区版（Community）功能受限但已能满足基础测试需求。

### 1.1 各版本对比

| 模块 | Community | Professional |
|---|---|---|
| Proxy | ✅ | ✅ |
| Repeater | ✅ | ✅ |
| Decoder | ✅ | ✅ |
| Comparer | ✅ | ✅ |
| Intruder | ✅（限速） | ✅ |
| Scanner | ❌ | ✅ |
| Crawler | ❌ | ✅ |
| Extensions | 部分 | ✅ |

> 本笔记以 **Community 版** 为基础，专业版增加功能仅作说明。

---

## 二、Proxy 代理模块

### 2.1 基础配置

```bash
# 启动 Burp Suite
java -jar burpsuite_community.jar

# 浏览器代理设置
# 127.0.0.1:8080
```

### 2.2 CA 证书导入（HTTPS 抓包必做��

```
1. 浏览器访问 http://burp
2. 下载 CA 证书（cacert.der）
3. 浏览器 → 设置 → 受信任的根证书颁发机构 → 导入
4. 重启浏览器
```

### 2.3 常用操作

```
# 拦截请求
Proxy → Intercept → Intercept is on

# 查看历史
Proxy → HTTP History（Ctrl+I）

# 转发请求
Intercept → Forward（Ctrl+F）

# 丢弃请求
Intercept → Drop

# 拦截规则配置
Proxy → Options → Intercept Client Requests
```

---

## 三、Repeater 重放模块

### 3.1 用途

- 修改请求参数后重放
- 对比响应差异
- 手工验证漏洞

### 3.2 基本操作

```
1. 在 HTTP History 中右键 → Send to Repeater
2. 进入 Repeater 标签页
3. 修改请求参数（如修改 id 值）
4. 点击 Send 发送
5. 右侧查看响应
```

### 3.3 DVWA 实战示例

**SQL 注入探测**（参见 `漏洞复现合集/SQL注入.md`）：

```
GET /dvwa/vulnerabilities/sqli/?id=1'&Submit=Submit HTTP/1.1
Host: 127.0.0.1
Cookie: PHPSESSID=xxx; security=low
```

观察响应：
- `id=1` → 200 正常
- `id=1'` → 500 数据库错误 → 确认注入点

---

## 四、Intruder 暴力破解模块

### 4.1 用途

- 自动化字典爆破（账号、密码、Token）
- Fuzz 测试
- 批量参数探测

### 4.2 攻击类型

| 类型 | 描述 | 适用场景 |
|---|---|---|
| **Sniper** | 单字典单位置逐个替换 | 单参数爆破 |
| **Battering ram** | 单字典多位置同值替换 | 同步参数 |
| **Pitchfork** | 多字典多位置同位替换 | 账号+密码同步 |
| **Cluster bomb** | 多字典多位置笛卡尔积 | 全部组合 |

### 4.3 DVWA 暴力破解实战

详见 `漏洞复现合集/暴力破解.md`，关键步骤：

```
1. 拦截登录请求 → Send to Intruder
2. Positions 标签 → Clear § → 给 password 加 §
3. Attack type → Sniper
4. Payloads → Simple list → 导入密码字典
6. Resource Pool → 配置并发数与节流
7. Start attack → 观察 Length 列差异
```

### 4.4 Community 版限制

- Intruder **限速**：每秒最多 1 个请求
- **无 Macros**（无法自动刷新 CSRF Token）
- 解决方案：使用 Repeater 手动测试（参见暴力破解 High 级别）

---

## 五、Comparer 对比模块

### 5.1 用途

对比两个请求 / 响应的差异，常用于：
- 盲注探测（响应长度 / 内容差异）
- 漏洞确认（修改 Payload 前后的对比）

### 5.2 基本操作

```
1. Repeater 中右键请求 → Send to Comparer (Request)
2. 修改 Payload 后再次 Send to Comparer (Request)
3. Comparer → 切换到 Words / Bytes 视图查看差异
```

---

## 六、Decoder 编解码模块

### 6.1 常用编解码

| 类型 | 用途 |
|---|---|
| URL | URL 编码 / 解码 |
| HTML | HTML 实体编码 |
| Base64 | Base64 编解码 |
| Hex | 十六进制 |
| ASCII | 字符与 ASCII 转换 |
| Hash | MD5 / SHA1 / SHA256 等 |

### 6.2 实战示例

**Base64 解码**（读取 PHP 源码）：
```
1. 在浏览器看到一串 Base64
2. 复制到 Decoder → Base64 → Decode as...
3. 查看解码后的内容
```

**URL 编码 Payload**：
```
原始：1' OR 1=1 --
URL 编码：1%27%20OR%201%3D1%20--
```

---

## 七、Target 站点地图

### 7.1 用途

- 自动记录访问过的所有 URL
- 显示站点结构
- 标记漏洞（专业版）

### 7.2 DVWA 站点地图

```
Target → Site map
├── http://127.0.0.1
│   └── /dvwa
│       ├── /login.php
│       ├── /index.php
│       ├── /vulnerabilities/
│       │   ├── /brute/
│       │   ├── /sqli/
│       │   ├── /xss_r/
│       │   ├── /xss_s/
│       │   ├── /upload/
│       │   ├── /fi/
│       │   ├── /csrf/
│       │   └── /exec/
│       └── /security.php
```

---

## 八、Extensions 扩展模块

### 8.1 常用扩展（Community 版可用）

- **Logger++**：增强日志记录
- **Autorize**：越权测试自动化
- **Param Miner**：隐藏参数发现
- **JSON Web Tokens**：JWT 解析

### 8.2 安装方法

```
1. Extender → BApp Store
2. 搜索扩展 → Install
3. 重启 Burp 后生效
```

---

## 九、DVWA 实战中的 Burp Suite 使用总结

### 9.1 暴力破解模块
详见 `漏洞复现合集/暴力破解.md`
- Low：Intruder Sniper + 字典爆破
- Medium：Intruder Sniper + 2000ms 节流
- High：Repeater 手动重放（Community 无 Macros）

### 9.2 SQL 注入模块
详见 `漏洞复现合集/SQL注入.md`
- Repeater 修改 id 参数探测注入
- 时间盲注通过响应延迟确认

### 9.3 文件上传模块
详见 `漏洞复现合集/文件上传漏洞.md`
- Repeater 拦截上传请求
- 修改 Content-Type 绕过 MIME 校验

### 9.4 CSRF 模块
- 拦截密码修改 GET 请求
- 提取 URL 构造 PoC

#### 实操截图

![Burp Suite Intruder 爆破配置与结果](screenshots/tools/tools-08.png)

![Burp Suite Repeater SQL 注入测试](screenshots/tools/tools-09.png)

![Burp Suite HTTP History 请求记录](screenshots/tools/tools-10.png)

![Burp Suite Intruder 攻击结果分析](screenshots/tools/tools-11.png)

![Burp Suite 文件上传请求拦截修改](screenshots/tools/tools-12.png)

![Burp Suite 响应对比分析](screenshots/tools/tools-13.png)

---

## 十、快捷键速查

| 快捷键 | 功能 |
|---|---|
| `Ctrl+I` | 切换到 HTTP History |
| `Ctrl+R` | 切换到 Repeater |
| `Ctrl+F` | 转发请求 |
| `Ctrl+T` | 丢弃请求 |
| `Ctrl+U` | URL 编码选中字符 |
| `Ctrl+Shift+U` | URL 解码选中字符 |

---

## 十一、常见问题

### 11.1 浏览器无法访问 HTTPS 网站

**原因**：CA 证书未导入
**解决**：从 http://burp 下载证书并导入浏览器

### 11.2 Intruder 启动失败（Community 版）

**错误**：Attack requires Burp Suite Professional
**解决**：使用 Repeater 手动测试

### 11.3 中文乱码

**解决**：修改字体设置或使用 Display → 修改字符编码

### 11.4 抓不到本地回环请求

**原因**：浏览器配置未生效或代理类型不对
**解决**：
- 检查代理类型（HTTP/HTTPS）
- 检查 127.0.0.1:8080 是否被占用
- 使用 `curl -x 127.0.0.1:8080 http://127.0.0.1/dvwa` 验证

---

## 十二、参考

- Burp Suite 官方文档：<https://portswigger.net/burp/documentation>
- PortSwigger Web Security Academy：<https://portswigger.net/web-security>
- DVWA 配合 Burp 实战教程：参见本仓库 `01-DVWA靶场实训/`
- 仅在授权测试场景使用