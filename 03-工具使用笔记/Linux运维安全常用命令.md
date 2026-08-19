# Linux 运维安全常用命令笔记

> 适用场景：Linux 服务器运维、安全巡检、日志分析
> 系统：CentOS / Ubuntu / Debian / Kali

---

## 一、账号与权限管理

### 1.1 账号操作

```bash
# 查看当前用户
whoami
id

# 创建用户
sudo useradd -m -s /bin/bash username
sudo passwd username

# 删除用户（保留家目录）
sudo userdel username

# 删除用户（同时删除家目录）
sudo userdel -r username

# 锁定 / 解锁用户
sudo passwd -l username    # 锁定
sudo passwd -u username    # 解锁

# 修改用户到期时间
sudo chage -E 2026-12-31 username

# 强制下次登录修改密码
sudo chage -d 0 username

# 查看用户密码策略
sudo chage -l username
```

### 1.2 用户组管理

```bash
# 查看用户所属组
groups username

# 添加到组
sudo usermod -aG groupname username

# 查看所有用户
cat /etc/passwd | awk -F: '{print $1}'

# 查看所有组
cat /etc/group | awk -F: '{print $1}'

# 查找空口令账号
awk -F: '($2==""){print $1}' /etc/shadow
```

### 1.3 sudo 配置

```bash
# 编辑 sudo 配置
sudo visudo

# 查看 sudo 权限
sudo -l

# 给用户组 sudo 权限
%admin ALL=(ALL) ALL

# 给特定用户特定命令权限
username ALL=(ALL) /usr/bin/systemctl restart apache2
```

---

## 二、文件权限管理

### 2.1 权限查看

```bash
# 查看文件权限
ls -l filename

# 查看目录权限
ls -ld directory

# 数字权限
stat -c "%a %n" filename

# 查看文件所有者
ls -ln filename
```

### 2.2 权限修改

```bash
# 修改权限（符号）
chmod u+x file           # 用户加执行
chmod g-w file           # 组员减写
chmod o=r file           # 其他仅读
chmod a+r file           # 所有人加读

# 修改权限（数字）
chmod 755 file           # rwxr-xr-x
chmod 644 file           # rw-r--r--
chmod 600 file           # rw-------

# 修改所有者
chown user:group file
chown -R user:group directory

# 修改 ACL（细粒度权限）
setfacl -m u:username:rwx file
setfacl -m g:groupname:rx file
getfacl file
```

### 2.3 特殊权限

```bash
# SUID（执行时提升为文件所有者权限）
chmod u+s file
chmod 4755 file

# SGID（在目录中创建文件继承组）
chmod g+s directory
chmod 2755 directory

# Sticky Bit（目录内文件仅所有者可删）
chmod +t directory
chmod 1755 directory

# 查找 SUID 文件（风险排查）
find / -perm -4000 -type f 2>/dev/null
find / -perm -2000 -type f 2>/dev/null
```

### 2.4 危险文件权限排查

```bash
# 查找全局可写文件
find / -perm -o=w -type f 2>/dev/null

# 查找全局可写目录
find / -perm -o=w -type d 2>/dev/null

# 查找无主文件
find / -nouser -o -nogroup 2>/dev/null

# 查找 SSH 私钥
find / -name "id_rsa" -type f 2>/dev/null
```

---

## 三、网络配置与排查

### 3.1 网络接口

```bash
# 查看网卡信息
ip addr show
ifconfig

# 查看路由表
ip route
route -n

# 查看 DNS
cat /etc/resolv.conf

# 查看主机名
hostname
hostnamectl
```

### 3.2 端口监听

```bash
# 查看所有监听端口
ss -tlnp
netstat -tlnp

# 查看所有连接
ss -an
netstat -an

# 查看 TCP 连接
ss -t

# 查看特定端口
ss -tlnp | grep :80

# 查看进程占用的端口
lsof -i :80
```

### 3.3 网络排查

```bash
# 测试连通性
ping -c 4 target.com

# 路由追踪
traceroute target.com
tracepath target.com

# DNS 查询
nslookup target.com
dig target.com
host target.com

# 端口测试
nc -zv target.com 80
telnet target.com 80

# HTTP 请求
curl -I http://target.com
curl -v http://target.com

# 抓包分析
sudo tcpdump -i eth0 port 80 -w capture.pcap
sudo tcpdump -i eth0 -nn -X port 80
```

---

## 四、防火墙配置

### 4.1 ufw（Ubuntu）

```bash
# 启用 / 禁用
sudo ufw enable
sudo ufw disable

# 查看状态
sudo ufw status verbose

# 默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许服务
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow from 192.168.1.0/24 to any port 22

# 拒绝规则
sudo ufw deny from 1.2.3.4

# 删除规则（先查看带编号）
sudo ufw status numbered
sudo ufw delete 3

# 重置
sudo ufw reset
```

### 4.2 firewalld（CentOS / RHEL）

```bash
# 查看区域
sudo firewall-cmd --get-active-zones

# 查看规则
sudo firewall-cmd --list-all

# 添加服务
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload

# 富规则
sudo firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 service name=ssh accept'
```

### 4.3 iptables（通用）

```bash
# 查看规则
sudo iptables -L -n -v
sudo iptables -t nat -L -n

# 默认策略
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# 允许已建立的连接
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许 SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 允许本地
sudo iptables -A INPUT -i lo -j ACCEPT

# 保存规则
sudo iptables-save > /etc/iptables/rules.v4

# 恢复
sudo iptables-restore < /etc/iptables/rules.v4
```

---

## 五、进程与服务管理

### 5.1 进程查看

```bash
# 查看所有进程
ps aux
ps -ef

# 进程树
pstree -p

# 实时监控
top
htop

# 查找特定进程
ps aux | grep nginx
pgrep nginx

# 查看进程打开的文件
lsof -p PID
```

### 5.2 进程操作

```bash
# 结束进程
kill PID
kill -9 PID             # 强制
killall processname
pkill processname

# 后台运行
nohup command &
disown

# 优先级
nice -n 10 command
renice -n 10 PID
```

### 5.3 systemd 服务管理

```bash
# 查看服务状态
sudo systemctl status nginx

# 启动 / 停止 / 重启
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx

# 启用 / 禁用开机自启
sudo systemctl enable nginx
sudo systemctl disable nginx

# 查看所有启动失败的服务
sudo systemctl list-units --failed

# 查看服务日志
sudo journalctl -u nginx -f
sudo journalctl -u nginx --since "1 hour ago"
```

---

## 六、日志分析

### 6.1 系统日志位置

| 日志 | 路径 | 说明 |
|---|---|---|
| 系统日志 | `/var/log/syslog` 或 `/var/log/messages` | 通用系统消息 |
| 认证日志 | `/var/log/auth.log` 或 `/var/log/secure` | 登录、sudo |
| 内核日志 | `/var/log/kern.log` 或 `/var/log/dmesg` | 内核消息 |
| 启动日志 | `/var/log/boot.log` | 启动信息 |
| 应用日志 | `/var/log/<app>/` | 各应用日志 |
| Apache | `/var/log/apache2/` 或 `/var/log/httpd/` | Web 服务 |
| MySQL | `/var/log/mysql/` | 数据库 |
| SSH | `/var/log/secure` 或 `/var/log/auth.log` | SSH 登录 |

### 6.2 常用日志分析命令

```bash
# 实时跟踪日志
tail -f /var/log/syslog

# 查看最后 100 行
tail -n 100 /var/log/syslog

# 搜索关键字
grep "error" /var/log/syslog
grep -i "fail" /var/log/auth.log

# 统计 IP 访问次数
awk '{print $1}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head 20

# 查找 4xx/5xx 错误
grep -E " [4-5][0-9]{2} " /var/log/apache2/access.log

# 查找登录失败
grep "Failed password" /var/log/auth.log

# 时间段日志
grep "Aug 14" /var/log/syslog
sed -n '/Aug 14 10:00:00/,/Aug 14 11:00:00/p' /var/log/syslog
```

### 6.3 日志轮转

```bash
# 查看 logrotate 配置
cat /etc/logrotate.conf
ls /etc/logrotate.d/

# 手动轮转
sudo logrotate -f /etc/logrotate.conf
```

---

## 七、系统监控

### 7.1 性能监控

```bash
# CPU 信息
lscpu
cat /proc/cpuinfo

# 内存
free -h

# 磁盘使用
df -h
du -sh /var/*

# IO 监控
iostat -x 1
iotop

# 负载
uptime
w

# 网络流量
iftop
nethogs
sar -n DEV 1
```

### 7.2 磁盘管理

```bash
# 查看磁盘分区
lsblk
fdisk -l

# 检查文件系统
sudo fsck /dev/sda1

# 查看 inode
df -i

# 查找大文件
find / -size +100M -type f 2>/dev/null
```

---

## 八、安全加固常用

### 8.1 SSH 加固

```bash
sudo nano /etc/ssh/sshd_config
```

```sshd_config
Port 2222                       # 修改默认端口
PermitRootLogin no              # 禁止 root 登录
PasswordAuthentication no       # 禁用密码认证
PubkeyAuthentication yes        # 启用公钥认证
AllowUsers secadmin           # 限制登录用户
MaxAuthTries 3                  # 最大尝试次数
ClientAliveInterval 300         # 超时断开
ClientAliveCountMax 2
Protocol 2
```

```bash
sudo systemctl restart sshd
```

### 8.2 系统更新

```bash
# Debian / Ubuntu
sudo apt update
sudo apt upgrade -y
sudo apt dist-upgrade

# CentOS / RHEL
sudo yum update -y

# 检查安全更新
sudo apt list --upgradable
```

### 8.3 文件完整性检查

```bash
# 安装 AIDE
sudo apt install aide
sudo aideinit
sudo aide --check

# 检查关键文件 md5
md5sum /etc/passwd /etc/shadow /etc/group
```

### 8.4 漏洞扫描

```bash
# 安装 ClamAV 杀毒
sudo apt install clamav
sudo freshclam
sudo clamscan -r /home/

# Lynis 安全审计
sudo apt install lynis
sudo lynis audit system
```

### 8.5 rootkit 检测

```bash
# chkrootkit
sudo apt install chkrootkit
sudo chkrootkit

# rkhunter
sudo apt install rkhunter
sudo rkhunter --check
```

---

## 九、常用配置路径

| 服务 | 配置路径 |
|---|---|
| SSH | `/etc/ssh/sshd_config` |
| Apache | `/etc/apache2/` 或 `/etc/httpd/` |
| Nginx | `/etc/nginx/` |
| MySQL | `/etc/mysql/` 或 `/etc/my.cnf` |
| PHP | `/etc/php/<version>/` |
| 防火墙 | `/etc/ufw/`、`/etc/firewalld/`、`/etc/iptables/` |
| Cron | `/etc/crontab`、`/etc/cron.d/` |
| 日志轮转 | `/etc/logrotate.conf`、`/etc/logrotate.d/` |

---

## 十、快捷键

| 快捷键 | 功能 |
|---|---|
| `Ctrl+C` | 中断当前命令 |
| `Ctrl+D` | 退出当前 Shell |
| `Ctrl+L` | 清屏 |
| `Ctrl+A` | 光标移至行首 |
| `Ctrl+E` | 光标移至行尾 |
| `Ctrl+U` | 删除光标前所有字符 |
| `Ctrl+K` | 删除光标后所有字符 |
| `Ctrl+R` | 反向搜索历史命令 |
| `Ctrl+Z` | 挂起当前进程 |
| `Tab` | 自动补全 |

---

## 十一、参考

- Linux man pages（最权威参考）
- 《Linux 命令行与 shell 脚本编程大全》
- Linux 中国：<https://linux.cn/>
- 各发行版官方文档：Ubuntu/CentOS/Debian