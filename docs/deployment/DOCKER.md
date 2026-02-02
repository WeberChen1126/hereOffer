# Docker 部署指南

本文档介绍如何使用 Docker 和 Docker Compose 部署 hereOffer 系统。

## 目录

- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [日志查看](#日志查看)
- [数据持久化](#数据持久化)
- [常见问题](#常见问题)

---

## 前置要求

### 必需软件

| 软件           | 版本要求  | 用途                     |
| -------------- | --------- | ------------------------ |
| Docker         | >= 20.10  | 容器运行时               |
| Docker Compose | >= 2.0    | 多容器编排               |

### 系统要求

| 资源 | 最低配置 | 推荐配置 |
| ---- | -------- | -------- |
| CPU  | 2 核     | 4 核     |
| 内存 | 4 GB     | 8 GB     |
| 磁盘 | 20 GB    | 50 GB    |

### 安装 Docker

**Windows**:
```powershell
# 下载 Docker Desktop for Windows
# https://www.docker.com/products/docker-desktop/

# 安装后启动 Docker Desktop
# 确认版本
docker --version
docker-compose --version
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 确认版本
docker --version
docker compose version
```

**macOS**:
```bash
# 使用 Homebrew
brew install --cask docker

# 启动 Docker Desktop
open -a Docker

# 确认版本
docker --version
docker-compose --version
```

---

## 快速开始

### 1. 克隆代码

```bash
git clone <your-repo-url>
cd AI-HR
```

### 2. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必需的环境变量（参见 [配置说明](#配置说明)）。

### 3. 构建和启动服务

使用 Makefile（推荐）：

```bash
# 构建并启动所有服务
make up

# 或者单独命令
make build    # 构建 Docker 镜像
make start    # 启动服务
```

或者直接使用 Docker Compose：

```bash
docker-compose up --build -d
```

### 4. 验证部署

检查所有服务是否正常运行：

```bash
# 查看服务状态
docker-compose ps

# 健康检查
curl http://localhost:8000/healthz
```

预期响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "ok"
  },
  "request_id": "..."
}
```

### 5. 访问服务

- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001
  - 用户名: `minioadmin`
  - 密码: `minioadmin`

---

## 配置说明

### 服务架构

`docker-compose.yml` 定义了以下服务：

```yaml
services:
  mysql:      # MySQL 8.0 数据库
  redis:      # Redis 7.2 缓存和任务队列
  minio:      # MinIO 对象存储
  api:        # FastAPI 应用
  worker:     # RQ 异步任务 Worker
```

### 环境变量

在 `.env` 文件中配置以下变量：

#### 数据库配置

```bash
# MySQL
MYSQL_ROOT_PASSWORD=your_root_password_here
MYSQL_DATABASE=hereoffer
MYSQL_USER=hereoffer_user
MYSQL_PASSWORD=your_mysql_password_here

# 数据库连接 URL（在 api 和 worker 中使用）
DATABASE_URL=mysql+pymysql://hereoffer_user:your_mysql_password_here@mysql:3306/hereoffer
```

#### Redis 配置

```bash
REDIS_URL=redis://redis:6379/0
```

#### MinIO 配置

```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=resumes
```

#### JWT 配置

```bash
JWT_SECRET=your_jwt_secret_key_here_at_least_32_chars_long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080  # 7 天
```

#### LLM 配置

```bash
# Alibaba DashScope API
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=qwen-plus
LLM_TIMEOUT=60
```

#### 语音服务配置（可选）

```bash
# Alibaba Cloud NLS
ALIYUN_AK_ID=your_access_key_id
ALIYUN_AK_SECRET=your_access_key_secret
ALIYUN_NLS_APPKEY=your_nls_appkey
ALIYUN_NLS_REGION=cn-shanghai
```

#### 其他配置

```bash
# CORS（跨域）
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# 日志级别
LOG_LEVEL=INFO

# 文件上传
MAX_UPLOAD_SIZE=10485760  # 10MB
```

### 端口映射

| 服务  | 容器端口 | 宿主机端口 | 说明                |
| ----- | -------- | ---------- | ------------------- |
| api   | 8000     | 8000       | FastAPI 服务        |
| mysql | 3306     | 3306       | MySQL 数据库        |
| redis | 6379     | 6379       | Redis               |
| minio | 9000     | 9000       | MinIO API           |
| minio | 9001     | 9001       | MinIO Web 控制台    |

---

## 服务管理

### 启动服务

```bash
# 启动所有服务
make up
# 或
docker-compose up -d

# 启动单个服务
docker-compose up -d api
```

### 停止服务

```bash
# 停止所有服务
make down
# 或
docker-compose down

# 停止并删除卷（清空数据）
docker-compose down -v
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart api
```

### 查看服务状态

```bash
# 查看所有服务
docker-compose ps

# 查看资源占用
docker stats
```

### 重新构建镜像

```bash
# 强制重新构建（清除缓存）
make rebuild
# 或
docker-compose build --no-cache

# 仅构建 API 服务
docker-compose build api
```

---

## 日志查看

### 查看所有服务日志

```bash
# 实时查看
make logs
# 或
docker-compose logs -f

# 查看最近 100 行
docker-compose logs --tail=100
```

### 查看单个服务日志

```bash
# API 服务
docker-compose logs -f api

# Worker 服务
docker-compose logs -f worker

# MySQL
docker-compose logs -f mysql
```

### 日志示例

**API 启动成功**:
```
api_1    | INFO:     Started server process [1]
api_1    | INFO:     Waiting for application startup.
api_1    | INFO:     Application startup complete.
api_1    | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Worker 启动成功**:
```
worker_1 | 16:20:32 RQ worker 'rq:worker:...' started
worker_1 | 16:20:32 Subscribing to channel rq:pubsub:...
worker_1 | 16:20:32 Cleaning registries for queue: default
```

---

## 数据持久化

Docker Compose 使用命名卷（named volumes）来持久化数据：

```yaml
volumes:
  mysql-data:     # MySQL 数据库文件
  redis-data:     # Redis 数据文件
  minio-data:     # MinIO 对象存储文件
```

### 备份数据

#### MySQL 备份

```bash
# 导出数据库
docker-compose exec mysql mysqldump -u root -p hereoffer > backup.sql

# 或使用环境变量
docker-compose exec -e MYSQL_PWD=$MYSQL_ROOT_PASSWORD mysql \
  mysqldump -u root hereoffer > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### MinIO 备份

```bash
# 方式 1: 使用 mc (MinIO Client)
docker run --rm -v $(pwd):/backup \
  --network ai-hr_default \
  minio/mc:latest \
  mc mirror minio/resumes /backup/resumes

# 方式 2: 直接复制 Docker 卷
docker run --rm -v minio-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio_backup.tar.gz -C /data .
```

### 恢复数据

#### MySQL 恢复

```bash
# 导入数据库
docker-compose exec -T mysql mysql -u root -p hereoffer < backup.sql
```

#### MinIO 恢复

```bash
# 解压到 Docker 卷
docker run --rm -v minio-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/minio_backup.tar.gz -C /data
```

### 清空数据

```bash
# ⚠️ 警告：这将删除所有数据！
docker-compose down -v
```

---

## 常见问题

### 1. 端口被占用

**错误信息**:
```
Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use
```

**解决方法**:
```bash
# 查找占用端口的进程（以 8000 为例）
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000

# 停止占用进程或修改 docker-compose.yml 中的端口映射
```

### 2. 服务无法启动

**检查步骤**:

1. 查看日志：
   ```bash
   docker-compose logs api
   docker-compose logs worker
   ```

2. 检查环境变量：
   ```bash
   docker-compose config
   ```

3. 验证 `.env` 文件是否存在且配置正确

4. 重新构建镜像：
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### 3. 数据库连接失败

**错误信息**:
```
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server...")
```

**解决方法**:

1. 检查 MySQL 服务是否正常运行：
   ```bash
   docker-compose ps mysql
   docker-compose logs mysql
   ```

2. 验证 `DATABASE_URL` 配置是否正确

3. 等待 MySQL 完全启动（首次启动需要初始化）：
   ```bash
   docker-compose up -d mysql
   sleep 30  # 等待 30 秒
   docker-compose up -d api worker
   ```

### 4. MinIO 无法访问

**检查步骤**:

1. 验证 MinIO 服务状态：
   ```bash
   docker-compose ps minio
   docker-compose logs minio
   ```

2. 访问 MinIO 控制台：http://localhost:9001

3. 检查桶是否已创建：
   ```bash
   docker-compose exec minio mc ls local
   ```

4. 手动创建桶（如果不存在）：
   ```bash
   docker-compose exec minio mc mb local/resumes
   docker-compose exec minio mc mb local/voices
   ```

### 5. Worker 无法消费任务

**检查步骤**:

1. 查看 Worker 日志：
   ```bash
   docker-compose logs -f worker
   ```

2. 检查 Redis 连接：
   ```bash
   docker-compose exec redis redis-cli ping
   # 应该返回 PONG
   ```

3. 查看队列状态：
   ```bash
   docker-compose exec redis redis-cli llen rq:queue:default
   ```

4. 重启 Worker：
   ```bash
   docker-compose restart worker
   ```

### 6. Docker 镜像构建失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement...
```

**解决方法**:

1. 清理 Docker 缓存：
   ```bash
   docker system prune -a
   docker builder prune -a
   ```

2. 使用国内镜像源（编辑 `Dockerfile`）：
   ```dockerfile
   # 在 RUN pip install 前添加
   RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 检查 `requirements.txt` 中的包版本是否可用

### 7. API 返回 502/503 错误

**可能原因**:

1. API 服务未启动完成
2. Uvicorn worker 崩溃
3. 数据库连接失败

**排查步骤**:

```bash
# 1. 查看 API 日志
docker-compose logs -f api

# 2. 检查健康检查
curl http://localhost:8000/healthz

# 3. 进入容器调试
docker-compose exec api bash
python -c "from app.database import SessionLocal; db = SessionLocal(); print('DB OK')"

# 4. 重启服务
docker-compose restart api
```

### 8. 容器内存不足

**错误信息**:
```
Killed
```

**解决方法**:

1. 增加 Docker Desktop 内存限制（Settings > Resources > Memory）

2. 限制单个服务内存：
   ```yaml
   # docker-compose.yml
   services:
     api:
       deploy:
         resources:
           limits:
             memory: 1G
   ```

---

## 高级配置

### 使用外部数据库

如果你已有 MySQL/Redis 服务，可以注释掉 `docker-compose.yml` 中对应的服务，并修改连接 URL：

```yaml
# docker-compose.yml
services:
  # mysql:  # 注释掉
  # redis:  # 注释掉
  
  api:
    environment:
      - DATABASE_URL=mysql+pymysql://user:pass@external-mysql:3306/hereoffer
      - REDIS_URL=redis://external-redis:6379/0
```

### 启用 HTTPS

1. 准备 SSL 证书：
   ```bash
   mkdir -p certs
   # 将证书文件放到 certs/ 目录
   ```

2. 修改 `docker-compose.yml`：
   ```yaml
   services:
     api:
       command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=/certs/key.pem --ssl-certfile=/certs/cert.pem
       volumes:
         - ./certs:/certs:ro
       ports:
         - "443:8000"
   ```

### 生产环境优化

**docker-compose.prod.yml**:
```yaml
services:
  api:
    environment:
      - LOG_LEVEL=WARNING
      - DEBUG=false
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  worker:
    deploy:
      replicas: 2
```

启动：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 下一步

- [Kubernetes 部署](./KUBERNETES.md) - 生产环境集群部署
- [环境变量配置](./ENVIRONMENT.md) - 详细的配置说明
- [API 参考](../frontend/API_REFERENCE.md) - API 接口文档
- [监控和日志](./PRODUCTION.md) - 生产环境最佳实践

---

**最后更新**: 2026-02-01
