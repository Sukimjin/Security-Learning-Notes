# Linux 真实排障案例集

> 排障思路：**先看现象 → 再用命令缩小范围 → 定位根因 → 解决 → 复盘预防**。
> 以下案例均来自搭建 LAMP / DVWA / Docker 环境时真实踩过的坑，适合安服与交付实施岗面试"服务起不来你怎么查"类问题。
> 基础命令速查见 [`Linux运维安全常用命令.md`](Linux运维安全常用命令.md)。

每个案例统一用五段式：**现象 → 排查 → 定位 → 解决 → 预防**。

---

## 案例 1：磁盘写满，服务报错 "No space left on device"

- **现象**：Web 服务突然 500，日志报 `No space left on device`；`touch` 新建文件也失败。
- **排查**：
  ```bash
  df -h                 # 看哪个挂载点 100%
  du -sh /* 2>/dev/null # 逐层找大目录（再从大目录往下 du）
  ```
- **定位**：`/var/log/` 下某服务日志无限增长（或 `/tmp` 堆满），占满根分区。
- **解决**：
  ```bash
  # 删大文件前先确认非正在写入的关键文件
  lsof | grep deleted   # 找已被删但仍被进程占用的文件（空间不释放）
  # 清空日志而非删文件，避免进程句柄失效：
  truncate -s 0 /var/log/xxx.log
  # 或 echo > /var/log/xxx.log
  ```
- **预防**：配置 `logrotate` 轮转；监控磁盘使用率；临时文件定时清理。

---

## 案例 2：Permission denied，Web 页面打不开

- **现象**：访问页面 403 Forbidden，或脚本执行报 `Permission denied`。
- **排查**：
  ```bash
  ls -l /var/www/html/index.php   # 看 owner / 权限
  namei -l /var/www/html/index.php # 逐级看路径每段权限
  getenforce                      # 看 SELinux 是否 Enforcing
  ```
- **定位**：文件 owner 是 root 而 Apache 以 www-data 运行；或目录缺执行位 `x`；或 SELinux 上下文不对。
- **解决**：
  ```bash
  chown -R www-data:www-data /var/www/html
  chmod 644 file ; chmod 755 dir
  # SELinux 下恢复上下文：
  restorecon -Rv /var/www/html
  ```
- **预防**：部署脚本统一设好 owner 与权限；上系统前 `getenforce` 确认策略。

---

## 案例 3：服务起不来（以 Apache / MySQL 为例）

- **现象**：`systemctl start apache2` 失败，或 MySQL 启动后立刻退出。
- **排查**：
  ```bash
  systemctl status apache2        # 看失败原因摘要
  journalctl -xe -u apache2       # 看详细日志
  ss -tulnp | grep ':80\|:3306'   # 看端口是否被占
  apache2ctl configtest           # Apache 配置语法检查
  ```
- **定位**：常见为端口被占（另一实例未退）、配置文件语法错、或数据目录权限不对。
- **解决**：按日志提示修配置 / 释放端口 / 修正目录权限；MySQL 还需确认 `datadir` 权限与磁盘空间。
- **预防**：改配置前先 `configtest` / 备份；用 `systemctl` 而非直接拉二进制；变更走变更记录。

---

## 案例 4：端口被占用，新服务起不来

- **现象**：启动时报 `Address already in use` 或 `bind() to 0.0.0.0:8080 failed`。
- **排查**：
  ```bash
  ss -tulnp | grep :8080          # 看哪个进程占着
  # 或老命令：netstat -tulnp | grep :8080
  ```
- **定位**：上一次启动的进程没退干净，或别的服务占了同端口。
- **解决**：
  ```bash
  kill <PID>            # 正常终止
  kill -9 <PID>         # 顽固进程强杀（谨慎）
  # 或改新服务监听端口避免冲突
  ```
- **预防**：统一端口规划表；Docker 映射端口前先 `ss` 查占用；服务用 systemd 托管自动拉起。

---

## 案例 5：CPU / 内存飙高，系统卡顿

- **现象**：`top` 里某进程 CPU 99%，或可用内存见底、开始用 swap。
- **排查**：
  ```bash
  top                      # 实时看，按 P 按 CPU 排、按 M 按内存排
  ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head  # 进程排序
  free -h                  # 内存概览
  ```
- **定位**：可能是死循环脚本、被挖矿（异常高 CPU 且进程名可疑）、或内存泄漏。
- **解决**：确认非业务关键后 `kill` 异常进程；挖矿类需断网查定时任务 `/etc/cron*` 与可疑服务，清理后改密码。
- **预防**：监控告警；最小权限运行服务；定期查异常进程与计划任务。

---

## 案例 6：SSH 连不上服务器

- **现象**：`ssh user@host` 超时或 `Connection refused`。
- **排查**：
  ```bash
  ping <IP>                              # 先确认网络通不通
  ss -tulnp | grep :22                   # 目标机看 sshd 是否在听
  systemctl status sshd                  # sshd 服务状态
  iptables -L -n | grep 22               # 防火墙是否放行 22
  ```
- **定位**：分三类 —— 网络不通（IP/路由）、sshd 没起、防火墙挡了。
- **解决**：起 sshd（`systemctl start sshd`）、放行防火墙（`<br>` 注意安全，仅放允许来源）、修正网络配置。
- **预防**：改 SSH 端口 + 禁 root 登录 + 密钥登录；防火墙默认 deny 仅放白名单；保留带外/控制台通道防锁死。

---

## 排障通用心法

1. **先分层定位**：网络层（ping/ss）→ 服务层（status/journalctl）→ 应用层（日志/配置）。
2. **看日志优先**：`journalctl -xe -u 服务名` 八成能直接给原因。
3. **一次只改一个变量**：改完立刻验证，避免多改后分不清哪步生效。
4. **动生产环境前备份 + 留回退**：配置先 cp 一份，危险操作先在测试机验证。

> 本文聚焦通用 Linux 排障；Docker 相关排错见 [`../01-DVWA靶场实训/环境部署与故障排查手册.md`](../01-DVWA靶场实训/环境部署与故障排查手册.md)。
