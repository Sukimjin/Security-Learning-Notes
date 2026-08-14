# Nmap 常用扫描命令笔记

> 工具版本：Nmap 7.94
> 适用场景：资产识别、端口扫描、服务识别、操作系统探测

---

## 一、Nmap 基础

### 1.1 安装

```bash
# Kali / Debian
sudo apt install nmap

# CentOS / RHEL
sudo yum install nmap
```

### 1.2 基本语法

```bash
nmap [扫描类型] [选项] {目标}
```

---

## 二、主机发现（Ping Sweep）

### 2.1 仅主机发现，不扫描端口

```bash
# 扫描 192.168.1.0/24 网段存活主机
nmap -sn 192.168.1.0/24
```

### 2.2 多种主机发现方式

```bash
# ARP 发现（局域网最快）
nmap -sn -PR 192.168.1.0/24

# ICMP echo 发现
nmap -sn -PE 192.168.1.0/24

# TCP SYN ping
nmap -sn -PS 192.168.1.0/24

# 跳过主机发现直接扫描（防止防火墙丢 ping 包）
nmap -Pn 192.168.1.10
```

---

## 三、端口扫描

### 3.1 端口范围

```bash
# 扫描默认 1000 个常用端口
nmap 192.168.1.10

# 扫描全部 65535 个端口（慢）
nmap -p- 192.168.1.10

# 扫描指定端口
nmap -p 80,443,8080 192.168.1.10

# 扫描端口范围
nmap -p 1-1000 192.168.1.10
```

### 3.2 扫描类型

```bash
# TCP SYN 扫描（默认，半连接，最快）
nmap -sS 192.168.1.10

# TCP Connect 扫描（完整连接，需 root）
nmap -sT 192.168.1.10

# UDP 扫描（慢）
nmap -sU 192.168.1.10

# FIN 扫描（绕过某些防火墙）
nmap -sF 192.168.1.10

# NULL 扫描
nmap -sN 192.168.1.10

# Xmas 扫描
nmap -sX 192.168.1.10
```

---

## 四、服务与版本识别

### 4.1 服务识别

```bash
# 默认服务识别
nmap -sV 192.168.1.10

# 指定识别强度（0-9，越高越详细越慢）
nmap -sV --version-intensity 9 192.168.1.10

# 轻量级识别
nmap -sV --version-light 192.168.1.10
```

### 4.2 操作系统识别

```bash
# 启用 OS 检测
nmap -O 192.168.1.10

# 限制 OS 检测
nmap -O --osscan-limit 192.168.1.10

# 激进探测（更多 OS 特征）
nmap -O --osscan-guess 192.168.1.10
```

### 4.3 综合扫描

```bash
# 全方位扫描（SYN + 版本 + OS + 脚本 + traceroute）
sudo nmap -A 192.168.1.10
```

---

## 五、NSE 脚本（Nmap Scripting Engine）

### 5.1 脚本分类

| 类别 | 说明 |
|---|---|
| `auth` | 认证相关 |
| `broadcast` | 广播探测 |
| `brute` | 暴力破解 |
| `default` | 默认脚本 |
| `discovery` | 服务发现 |
| `dos` | 拒绝服务 |
| `exploit` | 漏洞利用 |
| `external` | 外部资源 |
| `fuzzer` | 模糊测试 |
| `intrusive` | 入侵性 |
| `malware` | 恶意软件 |
| `safe` | 安全脚本 |
| `version` | 版本检测 |
| `vuln` | 漏洞扫描 |

### 5.2 常用脚本

```bash
# 使用默认脚本集
nmap -sC 192.168.1.10

# 使用 vuln 类脚本（漏洞扫描）
nmap --script vuln 192.168.1.10

# 使用特定脚本
nmap --script http-title 192.168.1.10

# 多个脚本
nmap --script "http-headers,http-methods" 192.168.1.10

# SMB 漏洞扫描
nmap --script smb-vuln-ms17-010 192.168.1.0/24

# HTTP 暴力破解目录
nmap --script http-enum 192.168.1.10
```

### 5.3 DVWA 实战中用到的命令

```bash
# 扫描 DVWA 靶机（Kali 虚拟机，IP 通常为 192.168.1.x）
nmap -sV -O 192.168.1.10

# 扫描 DVWA Web 服务详细信息
nmap -p 80 -sV --script http-enum,http-headers,http-methods 192.168.1.10
```

---

## 六、性能与输出

### 6.1 性能调优

```bash
# 时间模板（0-5，越高越快越激进）
# T0: 偏执 / T1: 鬼祟 / T2: 礼貌 / T3: 正常 / T4: 激进 / T5: 疯狂
nmap -T4 192.168.1.10
nmap -T4 --max-retries 1 --min-parallelism 10 192.168.1.10
```

### 6.2 输出格式

```bash
# 正常输出
nmap -oN scan_result.txt 192.168.1.10

# XML 输出（适合脚本处理）
nmap -oX scan_result.xml 192.168.1.10

# Grepable 输出
nmap -oG scan_result.gnmap 192.168.1.10

# 全部输出
nmap -oA scan_all 192.168.1.10
```

### 6.3 详细程度

```bash
# 详细级别（0-2）
nmap -v 192.168.1.10
nmap -vv 192.168.1.10
```

---

## 七、规避防火墙 / IDS

### 7.1 常用技巧

```bash
# 分片扫描
nmap -f 192.168.1.10

# 指定 MTU
nmap --mtu 24 192.168.1.10

# 诱饵扫描
nmap -D RND:10 192.168.1.10

# 源端口欺骗
nmap --source-port 53 192.168.1.10

# 时间延迟
nmap --scan-delay 1s 192.168.1.10
```

### 7.2 注意事项

⚠️ **仅在授权测试场景使用规避技术**：
- 未授权使用规避技术可能违法
- 多数企业 IDS 会记录规避行为

---

## 八、DVWA 实战记录

### 8.1 实验场景

```bash
# 假设 DVWA 靶机 IP：192.168.1.10
# Kali 攻击机执行：

# 1. 主机发现
nmap -sn 192.168.1.0/24

# 2. 全端口扫描
nmap -sS -p- 192.168.1.10

# 3. 服务识别
nmap -sV -O 192.168.1.10

# 4. 漏洞脚本扫描
nmap --script http-enum,http-title,http-methods -p 80 192.168.1.10

# 5. 综合扫描
sudo nmap -A -T4 192.168.1.10
```

### 8.2 输出示例

```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.4p1
80/tcp   open  http    Apache httpd 2.4.58
3306/tcp open  mysql   MariaDB 10.5
```

#### 实操截图

![Nmap 端口扫描与服务识别结果](screenshots/tools/tools-01.png)

![Nmap 漏洞脚本扫描输出](screenshots/tools/tools-02.png)

![Nmap 综合扫描结果](screenshots/tools/tools-03.png)

---

## 九、常见问题

### 9.1 扫描结果不准确

可能原因：
- 防火墙丢包 → 加 `-Pn` 跳过主机发现
- 速率被限 → 降低 `-T` 模板
- 主机无响应 → 检查网络连接

### 9.2 扫描速度慢

- 使用 `-T4` 或 `-T5`
- 限制端口范围 `-p 1-10000`
- 增加并发 `--min-parallelism 10`

### 9.3 需要 root 权限

部分扫描类型需 root：
- SYN 扫描 (`-sS`)
- OS 检测 (`-O`)
- Raw socket 操作

```bash
sudo nmap -sS -O 192.168.1.10
```

---

## 十、参考

- Nmap 官方文档：<https://nmap.org/book/man.html>
- Nmap NSE 脚本库：<https://nmap.org/nsedoc/>
- 《Nmap 网络扫描》—— 戈登·里昂 著
- 实战安全测试中**仅对授权目标使用**