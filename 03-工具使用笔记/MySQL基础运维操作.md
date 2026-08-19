# MySQL 基础运维操作

>  面向交付实施/运维岗位的 MySQL 日常操作速查手册，覆盖安装、启停、权限、备份、排错全流程。

---

## 一、安装与启停

### 1.1 安装（Debian/Ubuntu）

```bash
# 安装 MySQL 服务端
apt-get update
apt-get install mysql-server -y

# 安装后执行安全初始化
mysql_secure_installation
# 按提示设置 root 密码、删除匿名用户、禁止远程 root 登录、删除测试库
```

### 1.2 服务管理

```bash
# 启动 / 停止 / 重启
systemctl start mysql
systemctl stop mysql
systemctl restart mysql

# 查看状态
systemctl status mysql

# 设置开机自启 / 禁用自启
systemctl enable mysql
systemctl disable mysql

# Windows 环境下
net start mysql
net stop mysql
```

### 1.3 首次登录

```bash
# Linux：root 默认无密码（安装后需设置）
mysql -u root -p

# 如果忘记密码，跳过认证启动
mysqld --skip-grant-tables --skip-networking &
mysql -u root
# 然后修改密码：
# ALTER USER 'root'@'localhost' IDENTIFIED BY '新密码';
# FLUSH PRIVILEGES;
```

---

## 二、数据库与表操作

```sql
-- 查看所有数据库
SHOW DATABASES;

-- 创建数据库
CREATE DATABASE dvwa CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- 使用数据库
USE dvwa;

-- 查看当前库所有表
SHOW TABLES;

-- 查看表结构
DESC users;
-- 或
SHOW CREATE TABLE users\G

-- 删除数据库（谨慎）
DROP DATABASE dvwa;
```

---

## 三、用户与权限管理

### 3.1 创建用户

```sql
-- 创建本地用户
CREATE USER 'dvwa'@'localhost' IDENTIFIED BY 'password123';

-- 创建远程访问用户（仅限靶场环境，生产环境慎用）
CREATE USER 'dvwa'@'%' IDENTIFIED BY 'password123';
```

### 3.2 授权

```sql
-- 授予指定库的全部权限
GRANT ALL PRIVILEGES ON dvwa.* TO 'dvwa'@'localhost';

-- 授予只读权限（适用于巡检账号）
GRANT SELECT ON dvwa.* TO 'audit'@'localhost';

-- 授予指定权限
GRANT SELECT, INSERT, UPDATE, DELETE ON dvwa.* TO 'app'@'localhost';

-- 刷新权限（授权后必须执行）
FLUSH PRIVILEGES;
```

### 3.3 查看与回收权限

```sql
-- 查看当前用户权限
SHOW GRANTS;
SHOW GRANTS FOR 'dvwa'@'localhost';

-- 回收权限
REVOKE INSERT, UPDATE, DELETE ON dvwa.* FROM 'dvwa'@'localhost';
FLUSH PRIVILEGES;

-- 删除用户
DROP USER 'dvwa'@'localhost';
```

### 3.4 修改密码

```sql
-- 修改自己的密码
ALTER USER USER() IDENTIFIED BY 'new_password';

-- 管理员修改他人密码
ALTER USER 'dvwa'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

---

## 四、备份与恢复

### 4.1 逻辑备份（mysqldump）

```bash
# 备份单个数据库
mysqldump -u root -p dvwa > dvwa_backup.sql

# 备份所有数据库
mysqldump -u root -p --all-databases > all_backup.sql

# 备份指定表
mysqldump -u root -p dvwa users > users_backup.sql

# 只备份表结构（不含数据）
mysqldump -u root -p --no-data dvwa > dvwa_schema.sql

# 压缩备份
mysqldump -u root -p dvwa | gzip > dvwa_backup_$(date +%Y%m%d).sql.gz
```

### 4.2 恢复

```bash
# 从备份文件恢复
mysql -u root -p dvwa < dvwa_backup.sql

# 恢复压缩备份
gunzip < dvwa_backup_20260814.sql.gz | mysql -u root -p dvwa

# Docker 环境下
docker exec -i <容器名> mysql -u root -p dvwa < dvwa_backup.sql
```

### 4.3 定时备份（crontab）

```bash
# 每天凌晨 2 点自动备份
crontab -e
# 添加：
0 2 * * * mysqldump -u root -p<密码> dvwa > /backup/dvwa_$(date +\%Y\%m\%d).sql

# 定期清理 7 天前的备份
find /backup -name "dvwa_*.sql" -mtime +7 -delete
```

---

## 五、常见报错处理

### 5.1 连接被拒绝

```
ERROR 2003 (HY000): Can't connect to MySQL server on '127.0.0.1' (111)
```

**排查**：
```bash
# 1. 检查 MySQL 是否运行
systemctl status mysql

# 2. 检查端口
ss -tlnp | grep :3306

# 3. 检查防火墙
ufw status | grep 3306
```

### 5.2 密码丢失

```
ERROR 1045 (28000): Access denied for user 'root'@'localhost'
```

**处理**：
```bash
# 1. 停止 MySQL
systemctl stop mysql

# 2. 跳过认证启动
mysqld --skip-grant-tables --skip-networking &

# 3. 无密码登录
mysql -u root

# 4. 修改密码
ALTER USER 'root'@'localhost' IDENTIFIED BY '新密码';
FLUSH PRIVILEGES;
exit;

# 5. 正常重启
killall mysqld
systemctl start mysql
```

### 5.3 字符集乱码

**排查**：
```sql
-- 查看字符集设置
SHOW VARIABLES LIKE 'character_set%';

-- 确保数据库和表使用 utf8mb4
ALTER DATABASE dvwa CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4;
```

**配置文件修改**（`/etc/mysql/mysql.conf.d/mysqld.cnf`）：
```ini
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_general_ci

[client]
default-character-set = utf8mb4
```

### 5.4 表被锁

```sql
-- 查看当前锁状态
SHOW PROCESSLIST;

-- 找到耗时长的查询
SELECT * FROM information_schema.processlist WHERE TIME > 10;

-- 终止问题进程
KILL <进程ID>;
```

### 5.5 Too many connections

```sql
-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 临时调大（重启后失效）
SET GLOBAL max_connections = 200;

-- 永久修改（配置文件）
# /etc/mysql/mysql.conf.d/mysqld.cnf
# max_connections = 200
```

---

## 六、性能速查

```sql
-- 查看慢查询是否开启
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看数据库大小
SELECT
    table_schema AS '数据库',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '大小(MB)'
FROM information_schema.tables
GROUP BY table_schema;

-- 查看表大小
SELECT
    table_name AS '表名',
    ROUND(data_length / 1024 / 1024, 2) AS '数据(MB)',
    ROUND(index_length / 1024 / 1024, 2) AS '索引(MB)',
    table_rows AS '行数'
FROM information_schema.tables
WHERE table_schema = 'dvwa'
ORDER BY data_length DESC;
```

---

> 注意 **注意**：以上操作中的弱口令（password123）仅用于靶场演示，生产环境必须使用强密码策略。

---

**最后更新**：2026-08-14
