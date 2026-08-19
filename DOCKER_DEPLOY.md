# Docker 一键部署 DVWA 靶场

>  **3 分钟启动 DVWA** — 面试官可立即跑起来验证漏洞复现。

---

## 一、为什么用 Docker？

传统方式部署 DVWA 需要：
- 安装 Apache + MySQL + PHP（版本兼容性坑）
- 下载 DVWA 源码
- 配置数据库
- 改文件权限
- **耗时 30+ 分钟**

Docker 部署只需：
- 拉镜像 → 启动容器 → 浏览器访问
- **耗时 2-3 分钟**

---

## 二、环境准备

### 2.1 Windows / macOS

1. 下载 **Docker Desktop**：
   - 官网：https://www.docker.com/products/docker-desktop/
   - 下载对应系统版本
2. 安装并启动 Docker Desktop
3. 验证安装：
   ```bash
   docker --version
   docker-compose --version
   ```

### 2.2 Linux（Ubuntu/Debian）

```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证
sudo docker --version
```

---

## 三、启动 DVWA

### 3.1 拉取并启动

在本仓库根目录执行：

```bash
docker-compose up -d
```

输出示例：
```
[+] Running 3/3
 ⠿ Network dvwa-net       Created
 ⠿ Container dvwa-lab     Started
```

### 3.2 验证容器运行

```bash
docker ps
```

应看到类似：
```
CONTAINER ID   IMAGE                      STATUS         PORTS
abc123def456   vulnerables/web-dvwa:latest   Up 30 seconds   0.0.0.0:8080->80/tcp
```

### 3.3 浏览器访问

打开浏览器，访问：**http://localhost:8080**

看到 DVWA 登录页面 → 默认账号 `admin` / `password`

---

## 四、初始化 DVWA

首次访问会跳转到 `/setup.php`，需要初始化数据库：

1. 页面下方点击 **「Create / Reset Database」** 按钮
2. 等待 2-3 秒，看到「Setup successful」字样
3. 自动跳转到登录页，输入 `admin` / `password`
4. 登录成功，进入 DVWA 主页

---

## 五、开始漏洞复现

### 5.1 调整安全等级

左侧菜单 → **DVWA Security** → 难度选择：
- **Low** — 无过滤，学习原理
- **Medium** — 简单过滤，学习绕过
- **High** — 严格过滤，学习高级技巧
- **Impossible** — 安全实现，学习防御

点 **Submit** 生效。

### 5.2 推荐复现顺序

1. **SQL Injection**（最重要）
2. **XSS (Reflected)**
3. **XSS (Stored)**
4. **File Upload**
5. **Command Injection**
6. **CSRF**
7. **File Inclusion**
8. **Brute Force**

每个漏洞都按 Low → Medium → High → Impossible 顺序复现。

### 5.3 Burp Suite 抓包（推荐）

DVWA 部署在容器内，但监听 `localhost:8080`：
- Burp Suite 代理设置为 `127.0.0.1:8080`
- 浏览器代理设置为 `127.0.0.1:8080`
- DVWA 访问地址 `http://localhost:8080`

> 注意 Burp 默认监听 8080 端口会与 DVWA 冲突，建议：
> - 方案 A：把 DVWA 改到 8888 端口（修改 docker-compose.yml 中的 `ports: - "8888:80"`）
> - 方案 B：把 Burp 监听端口改到 8081

---

## 六、停止与清理

### 6.1 停止靶场

```bash
docker-compose down
```

### 6.2 完全清理（含数据卷）

```bash
docker-compose down -v
docker image rm vulnerables/web-dvwa
```

### 6.3 重新启动

```bash
docker-compose up -d
```

---

## 七、常见问题

### Q1：访问 localhost:8080 提示「拒绝连接」

**A**：等待 5-10 秒，容器启动需要时间。可用 `docker ps` 查看状态。

### Q2：初始化数据库失败

**A**：
1. 检查容器是否正常运行：`docker ps -a`
2. 查看日志：`docker logs dvwa-lab`
3. 常见原因：MySQL 容器启动慢，重试几次即可

### Q3：改了源代码刷新没生效

**A**：容器内是独立文件系统，修改容器内文件只在容器生命周期内有效。
- 持久化方案：将代码目录挂载到宿主机（修改 docker-compose.yml 加 volumes）
- 简单方案：删除容器后重启 `docker-compose up -d`

### Q4：性能慢

**A**：Docker Desktop 默认分配 4GB 内存，可在 Docker Desktop → Settings → Resources 调整。

### Q5：Windows 上报错「bind: address already in use」

**A**：8080 端口被占用（可能是 IIS、SQL Server、其他应用）。
- 方案 A：停止占用 8080 的服务
- 方案 B：改端口：编辑 `docker-compose.yml` 把 `"8080:80"` 改成 `"8888:80"`，然后访问 `http://localhost:8888`

---

## 八、安全注意事项

> 注意 **DVWA 是故意设计有漏洞的靶场，仅供安全学习！**

- ✗ **禁止部署到公网 / 任何可被外部访问的环境**
- ✗ **禁止用于真实业务系统**
- ✗ **禁止用于任何未授权测试**
- ✓ **仅限本地学习使用**
- ✓ **用完立即停止容器**（`docker-compose down`）
- ✓ **不要在生产环境复现任何 DVWA 漏洞**

详见 [README.md §重要声明](README.md#-重要声明)

---

**最后更新**：2026-08-14