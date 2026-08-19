# Docker 基础操作与排错

>  面向交付实施/运维岗位的 Docker 日常操作速查，覆盖镜像、容器、网络、排错全流程。
>
> DVWA 专用部署指南另见：[DOCKER_DEPLOY.md](../DOCKER_DEPLOY.md)

---

## 一、镜像管理

### 1.1 拉取与查看

```bash
# 拉取镜像
docker pull vulnerables/web-dvwa:latest
docker pull mysql:5.7

# 查看本地镜像
docker images

# 查看镜像详情
docker inspect vulnerables/web-dvwa:latest

# 查看镜像历史（分层结构）
docker history vulnerables/web-dvwa:latest
```

### 1.2 删除与清理

```bash
# 删除指定镜像（需先删除依赖该镜像的容器）
docker rmi vulnerables/web-dvwa:latest

# 强制删除
docker rmi -f <镜像ID>

# 清理悬空镜像（无标签的中间层）
docker image prune

# 清理所有未使用的镜像
docker image prune -a
```

### 1.3 国内镜像加速

```bash
# 配置镜像加速（Linux）
# 编辑 /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}

# 重启 Docker 生效
systemctl restart docker

# Windows/Mac：Docker Desktop → Settings → Docker Engine
```

---

## 二、容器生命周期

### 2.1 创建与启动

```bash
# 创建并启动容器（最常用）
docker run -d \
  --name dvwa-lab \
  -p 8080:80 \
  -e SECURITY_LEVEL=low \
  --restart unless-stopped \
  vulnerables/web-dvwa:latest

# 参数说明：
# -d          后台运行
# --name      容器名称
# -p          端口映射（宿主机:容器）
# -e          环境变量
# --restart   重启策略（no/always/unless-stopped/on-failure）

# 使用 docker-compose 启动
docker-compose up -d          # 后台启动
docker-compose up -d --build  # 重新构建后启动
```

### 2.2 查看与管理

```bash
# 查看运行中的容器
docker ps

# 查看所有容器（含已停止）
docker ps -a

# 查看容器资源使用
docker stats
docker stats --no-stream      # 只输出一次

# 查看容器详情
docker inspect dvwa-lab

# 进入容器执行命令
docker exec -it dvwa-lab /bin/bash
docker exec -it dvwa-lab /bin/sh    # 如果没有 bash
```

### 2.3 停止与删除

```bash
# 停止容器
docker stop dvwa-lab

# 启动已停止的容器
docker start dvwa-lab

# 重启容器
docker restart dvwa-lab

# 删除容器（需先停止）
docker rm dvwa-lab

# 强制删除运行中的容器
docker rm -f dvwa-lab

# 清理所有已停止的容器
docker container prune
```

---

## 三、端口映射与数据卷

### 3.1 端口映射

```bash
# 单端口映射
docker run -p 8080:80 nginx

# 多端口映射
docker run -p 8080:80 -p 8443:443 nginx

# 指定 IP 映射（仅本机访问）
docker run -p 127.0.0.1:8080:80 nginx

# 随机端口映射
docker run -P nginx    # 大写 P，随机分配宿主机端口
```

### 3.2 数据卷

```bash
# 挂载目录（宿主机:容器）
docker run -v /data/mysql:/var/lib/mysql mysql:5.7

# 命名数据卷
docker volume create dvwa_data
docker run -v dvwa_data:/var/www/html/dvwa vulnerables/web-dvwa

# 只读挂载
docker run -v /config/nginx.conf:/etc/nginx/nginx.conf:ro nginx

# 查看数据卷
docker volume ls
docker volume inspect dvwa_data

# 清理未使用的数据卷
docker volume prune
```

### 3.3 网络管理

```bash
# 查看网络
docker network ls

# 创建自定义网络
docker network create --driver bridge dvwa-net

# 容器加入网络
docker run --network dvwa-net --name web-app nginx

# 查看网络详情
docker network inspect dvwa-net

# 删除网络
docker network rm dvwa-net
```

---

## 四、日志查看与排错

### 4.1 容器日志

```bash
# 查看容器日志
docker logs dvwa-lab

# 实时跟踪日志
docker logs -f dvwa-lab

# 查看最后 100 行
docker logs --tail 100 dvwa-lab

# 查看指定时间后的日志
docker logs --since "2026-08-14T00:00:00" dvwa-lab

# 查看带时间戳的日志
docker logs -t dvwa-lab
```

### 4.2 容器内进程与文件

```bash
# 查看容器内进程
docker top dvwa-lab

# 查看容器文件系统变更
docker diff dvwa-lab

# 从容器复制文件到宿主机
docker cp dvwa-lab:/var/log/apache2/error.log ./error.log

# 从宿主机复制文件到容器
docker cp ./config.inc.php dvwa-lab:/var/www/html/dvwa/config/
```

### 4.3 资源监控

```bash
# 实时资源使用
docker stats

# 单个容器
docker stats dvwa-lab

# 查看容器内事件
docker events --filter container=dvwa-lab
```

---

## 五、常见故障排查

### 5.1 端口冲突

```
Error: Bind for 0.0.0.0:8080 failed: port is already allocated
```

**解决**：
```bash
# 查看占用端口的容器
docker ps -a | grep 8080

# 停止占用端口的容器
docker stop <容器名>

# 或修改端口映射
docker run -p 9090:80 ...
```

### 5.2 镜像拉取超时

```
Error: pull access denied / timeout
```

**解决**：
```bash
# 1. 配置国内镜像源（见 1.3）
# 2. 检查网络
ping registry-1.docker.io
# 3. 手动导入
docker load -i dvwa.tar
```

### 5.3 容器无法启动

```
Error: container exited immediately
```

**排查**：
```bash
# 1. 查看退出码
docker ps -a
# 0 = 正常退出，1 = 应用错误，125 = docker 错误，126/127 = 命令不存在

# 2. 查看日志
docker logs <容器名>

# 3. 检查启动命令
docker inspect <容器名> | grep -A5 Cmd

# 4. 用交互模式调试
docker run -it --entrypoint /bin/sh <镜像名>
```

### 5.4 磁盘空间不足

```
Error: no space left on device
```

**解决**：
```bash
# 查看 Docker 磁盘使用
docker system df

# 全面清理
docker system prune -a
# 注意：会删除所有未使用的镜像、容器、网络

# 清理构建缓存
docker builder prune

# 查看 Docker 数据目录大小
du -sh /var/lib/docker/
```

### 5.5 容器间无法通信

**排查**：
```bash
# 1. 确认在同一网络
docker network inspect <网络名>
# 检查 Containers 字段

# 2. 容器内测试连通性
docker exec -it <容器A> ping <容器B名>
docker exec -it <容器A> curl http://<容器B名>:端口

# 3. 检查防火墙
iptables -L
# Docker 默认创建 iptables 规则，不要手动 flush
```

---

## 六、docker-compose 常用命令

```bash
# 启动（后台）
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止并删除容器、网络
docker-compose down

# 仅停止，不删除
docker-compose stop

# 重新构建镜像
docker-compose build

# 重启单个服务
docker-compose restart dvwa

# 查看配置
docker-compose config
```

---

## 七、Docker 清理速查

| 命令 | 清理内容 |
|------|---------|
| `docker container prune` | 已停止的容器 |
| `docker image prune` | 悬空镜像 |
| `docker image prune -a` | 所有未使用的镜像 |
| `docker volume prune` | 未使用的数据卷 |
| `docker network prune` | 未使用的网络 |
| `docker system prune` | 上面四项（不含数据卷） |
| `docker system prune -a --volumes` | 全部清理（谨慎） |

---

> 注意 **注意**：`docker system prune -a` 会删除所有未被运行中容器使用的镜像，执行前确认。

---

**最后更新**：2026-08-14
