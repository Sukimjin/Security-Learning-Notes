# CSRF 跨站请求伪造（Cross-Site Request Forgery）漏洞复现

> 漏洞模块：DVWA CSRF
> 工具：浏览器、Burp Suite
> 难度等级：Low / Medium / High

---

## 一、漏洞概述

**原理**：服务端未校验请求来源与 token，攻击者诱导受害者在已登录目标网站的情况下，访问恶意页面，受害者浏览器自动携带 Cookie 发送伪造请求。

**OWASP 分类**：A01:2021 - Broken Access Control（失效的访问控制）

**危害**：
- 伪造用户操作（修改密码、转账、关注、发邮件）
- 配合 XSS 形成攻击链，影响放大

**核心条件**：
1. 受害者在目标网站已登录（Cookie 有效）
2. 受害者访问攻击者构造的恶意页面
3. 目标网站不校验来源（Referer / Token）

**合规声明**：本文档所有 Payload 均在本地 DVWA 靶场复现，仅用于安全学习。

---

## 二、DVWA 四等级复现

### 2.1 Low 级别

#### 代码分析
`vulnerabilities/csrf/source/low.php`：
```php
$pass_new = $_GET['password_new'];
$pass_conf = $_GET['password_conf'];
if ($pass_new == $pass_conf) {
    // 修改密码的 SQL（无任何来源校验）
    $insert = "UPDATE users SET password = '$pass_new' WHERE user = '" . dvwaCurrentUser() . "';";
}
```

完全无来源校验。

#### 复现步骤

1. 难度调至 **Low**，进入 **CSRF** 模块
2. 修改密码表单实际是 **GET 请求**：
   ```
   http://127.0.0.1/dvwa/vulnerabilities/csrf/?password_new=123456&password_conf=123456&Change=Change
   ```
3. 修改成功即说明漏洞存在

#### 攻击场景模拟（无真实利用）

**攻击者构造的恶意 HTML 页面**（仅演示思路）：
```html
<!-- 攻击者服务器上的恶意页面 evil.html -->
<img src="http://127.0.0.1/dvwa/vulnerabilities/csrf/?password_new=evil123&password_conf=evil123&Change=Change">
```

当受害者（已登录 DVWA）访问该页面时，浏览器自动加载 `<img>` 标签，携带 DVWA 的 Session Cookie 发送 GET 请求，**受害者密码被静默修改**。

> ⚠️ 本仓库**仅作为原理演示**，不构造可执行的真实攻击页面。

---

### 2.2 Medium 级别

#### 防护机制
服务端校验 `HTTP_REFERER` 头是否包含本机主机名：
```php
if (preg_match('/127.0.0.1/', $_SERVER['HTTP_REFERER'])) {
    // 通过
} else {
    http_response_code(403);
    die('Invalid Referer');
}
```

#### 绕过思路
Referer 头是攻击者可控制的字段：

1. **文件名包含目标主机名**：
   - 将恶意 HTML 命名为 `127.0.0.1.html`
   - Referer 会包含 `127.0.0.1.html` → 通过正则匹配

2. **构造 URL 含 127.0.0.1 的页面**：
   ```html
   <!-- 攻击者页面 -->
   <iframe src="http://attacker.com/127.0.0.1.html">
   ```

---

### 2.3 High 级别

#### 防护机制
服务端引入 Anti-CSRF token（隐藏在表单中），请求必须携带该 token，且 token 与用户 Session 绑定。

#### 绕过思路
需要先获取目标用户的 token：
- 配合 **XSS 漏洞**窃取 token（DVWA Stored XSS）
- 通过社工手段让目标用户访问攻击者页面，页面 JS 自动读取 DVWA 页面 token 并发起请求

**典型攻击链**：Stored XSS + CSRF（XSS 漏洞存在时，CSRF 防护会被绕过）

> ⚠️ 本仓库**仅作为原理说明**，不演示具体利用 Payload。

---

### 2.4 Impossible 级别（安全实现）

```php
// 1. CSRF token 校验
checkToken($_REQUEST['user_token'], $_SESSION['session_token'], 'index.php');

// 2. 强制 POST（GET 请求会被拒绝）
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    die('Method Not Allowed');
}

// 3. 密码强度校验
if (!preg_match('/^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).{12,}$/', $pass_new)) {
    die('Password too weak.');
}

// 4. 修改前要求输入当前密码（confirm step-up）
```

**安全设计要点**：
- ✅ Anti-CSRF token（每次会话生成、不可预测）
- ✅ 强制 POST 请求（GET 请求参数易泄露）
- ✅ 密码强度策略
- ✅ 关键操作二次验证（输入当前密码）

---

## 三、CSRF 攻击构造三要素

| 要素 | 说明 |
|---|---|
| 受害者已登录目标站 | Cookie 有效 |
| 受害者访问攻击者页面 | 浏览器自动加载恶意资源 |
| 目标站不校验请求来源 | Referer / Token 缺失 |

---

## 四、加固建议

### 4.1 服务端层
1. **Anti-CSRF Token**：
   - 每个用户会话生成唯一 token
   - 所有写操作（POST/PUT/DELETE）必须携带 token
   - Token 一次性使用或短时间内失效

2. **SameSite Cookie**：
   ```php
   // PHP 设置 SameSite=Strict
   setcookie('session', $value, [
       'samesite' => 'Strict',
       'secure' => true,
       'httponly' => true,
   ]);
   ```
   - `Strict`：完全禁止第三方请求携带
   - `Lax`：GET 请求可携带（折中方案）

3. **关键操作二次验证**：
   - 修改密码、支付、转账等需输入当前密码 / 短信验证码 / TOTP

4. **Referer 校验**（辅助）：
   - 仅允许同源请求
   - 但 Referer 可被攻击者构造，仅作辅助防御

### 4.2 浏览器层
1. **SameSite Cookie 默认值**：现代浏览器默认 `Lax`，建议关键业务显式设 `Strict`
2. **SameSite Cookie 默认开启**：无需额外配置

### 4.3 业务层
1. **敏感操作页面增加二次确认**
2. **关键操作短信 / 邮件通知**
3. **操作日志审计**：异常来源 IP / User-Agent 触发告警

---

## 五、CSRF vs XSS 区别

| 维度 | CSRF | XSS |
|---|---|---|
| 攻击目标 | 利用受害者身份执行操作 | 在受害者浏览器执行脚本 |
| 是否需要受害者登录 | 是 | 否 |
| 是否能窃取数据 | 通常不能（只能伪造操作） | 能（窃取 Cookie 等） |
| 防御重点 | Token + SameSite | 输出编码 + CSP |

---

## 六、参考

- OWASP CSRF Prevention Cheat Sheet
- OWASP Top 10 2021 - A01 Broken Access Control
- RFC 6265 - HTTP State Management Mechanism（SameSite 定义）
- 《Web 安全深度剖析》—— 张炳帅 著