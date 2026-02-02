# hereOffer 后端架构设计

## 目录

- [概览](#概览)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [核心模块](#核心模块)
- [数据流](#数据流)
- [安全设计](#安全设计)
- [性能考虑](#性能考虑)

---

## 概览

hereOffer 是一个基于 LLM 的智能招聘系统，采用前后端分离架构，后端使用 FastAPI 框架构建 RESTful API，通过异步任务队列处理耗时的 LLM 调用，并支持实时对话功能。

### 核心特性

- **用户认证**：基于 JWT 的身份验证和 RBAC 权限控制
- **简历处理**：自动解析、结构化和智能评分
- **异步任务链**：RQ (Redis Queue) 处理耗时操作
- **岗位管理**：CRUD 操作和题库关联
- **投递管理**：状态机驱动的申请流程
- **实时对话**：WebSocket + LLM + 语音支持

---

## 技术栈

### 后端框架
- **FastAPI**: 高性能异步 Web 框架
- **Pydantic**: 数据验证和序列化
- **SQLAlchemy**: ORM 和数据库抽象层
- **Alembic**: 数据库迁移工具

### 数据存储
- **MySQL 8.0**: 关系型数据库（用户、岗位、投递、对话）
- **Redis 7.2**: 缓存和任务队列
- **MinIO**: S3 兼容对象存储（简历文件）

### 异步任务
- **RQ (Redis Queue)**: 任务队列系统
- **tenacity**: 重试机制

### AI & LLM
- **Alibaba DashScope**: LLM API（qwen-plus, qwen-turbo）
- **Alibaba Cloud NLS**: ASR 和 TTS（语音功能）

### 部署
- **Docker**: 容器化
- **Docker Compose**: 本地开发和单机部署
- **Kubernetes**: 生产环境编排（可选）

---

## 系统架构

```
┌─────────────────┐
│  Frontend UI    │
│  (React/Vue)    │
└────────┬────────┘
         │ HTTP/WebSocket
         │
┌────────▼────────────────────────────────────────┐
│              Nginx (Reverse Proxy)              │
└────────┬────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────┐
│          FastAPI Application (API Service)       │
│  ┌──────────────────────────────────────────┐  │
│  │  Routers (auth, jobs, applications, etc) │  │
│  └─────────────────┬────────────────────────┘  │
│  ┌─────────────────▼────────────────────────┐  │
│  │  Services (LLM, File Storage, Chat)      │  │
│  └─────────────────┬────────────────────────┘  │
│  ┌─────────────────▼────────────────────────┐  │
│  │  Models (SQLAlchemy ORM)                 │  │
│  └──────────────────────────────────────────┘  │
└─────────┬──────────────────┬────────────────────┘
          │                  │
          │                  │ Enqueue Task
          │                  │
┌─────────▼──────┐   ┌───────▼────────────────────┐
│  MySQL         │   │  Redis                     │
│  (Primary DB)  │   │  (Cache + Task Queue)      │
└────────────────┘   └───────┬────────────────────┘
                             │
                             │ Dequeue Task
                             │
                     ┌───────▼────────────────────┐
                     │  RQ Worker                 │
                     │  ┌──────────────────────┐  │
                     │  │  Worker Tasks        │  │
                     │  │  - Parse Resume      │  │
                     │  │  - Score Resume      │  │
                     │  │  - Generate Qs       │  │
                     │  └──────────────────────┘  │
                     └───────┬────────────────────┘
                             │
                     ┌───────▼────────────────────┐
                     │  External Services         │
                     │  - DashScope (LLM)         │
                     │  - MinIO (File Storage)    │
                     │  - Alibaba NLS (Voice)     │
                     └────────────────────────────┘
```

### 架构说明

1. **API 服务**：接收 HTTP 请求，处理业务逻辑，返回响应
2. **Worker 服务**：从 Redis 队列中拉取任务，执行耗时操作（LLM 调用）
3. **数据库层**：MySQL 存储持久化数据
4. **缓存层**：Redis 用于会话、任务队列
5. **对象存储**：MinIO 存储文件（简历）
6. **外部服务**：LLM API、语音服务

---

## 项目结构

```
D:\CO\AI-HR\
├── app/                          # FastAPI 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   ├── config.py                 # 配置管理（环境变量）
│   ├── constants.py              # 常量定义（枚举、状态）
│   ├── database.py               # 数据库连接和会话
│   ├── models.py                 # SQLAlchemy 模型
│   ├── schemas.py                # Pydantic 数据模式
│   ├── auth.py                   # 认证和授权逻辑
│   ├── task_queue.py             # 任务队列接口
│   │
│   ├── routers/                  # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py               # 用户注册/登录
│   │   ├── health.py             # 健康检查
│   │   ├── jobs.py               # 岗位管理（Admin）
│   │   ├── applications.py       # 投递管理（Candidate）
│   │   ├── admin_applications.py # 投递管理（Admin）
│   │   ├── chat.py               # 对话管理（HTTP）
│   │   ├── websocket_chat.py     # 对话管理（WebSocket）
│   │   └── debug.py              # 调试接口
│   │
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── llm_service.py        # LLM 调用封装
│   │   ├── file_storage.py       # 文件存储（MinIO）
│   │   ├── state_machine.py      # 状态机
│   │   ├── chat_service.py       # 对话服务
│   │   └── voice_service.py      # 语音服务（ASR/TTS）
│   │
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── file_extraction.py    # 文件解析（PDF/DOCX）
│
├── worker/                       # RQ Worker 目录
│   ├── __init__.py
│   ├── config.py                 # Worker 配置
│   ├── run_worker.py             # Worker 启动脚本
│   └── tasks.py                  # 异步任务定义
│
├── migrations/                   # Alembic 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
│
├── tests/                        # 测试文件
│   ├── test_basic.py
│   └── test_state_machine.py
│
├── docker-compose.yml            # Docker Compose 配置
├── Dockerfile                    # Docker 镜像定义
├── requirements.txt              # Python 依赖
├── Makefile                      # 常用命令封装
├── alembic.ini                   # Alembic 配置
├── pytest.ini                    # pytest 配置
└── .env                          # 环境变量（不提交到 Git）
```

---

## 核心模块

### 1. 认证模块 (`app/auth.py`)

**职责**：
- 用户密码哈希（bcrypt）
- JWT token 生成和验证
- FastAPI 依赖注入（`get_current_user`, `require_admin`）

**流程**：
1. 用户注册：密码 → bcrypt → 存入数据库
2. 用户登录：验证密码 → 生成 JWT → 返回 token
3. 请求鉴权：从 Header 提取 token → 验证 → 返回用户信息

**安全措施**：
- 使用 bcrypt（自动加盐）
- JWT 过期时间：7 天（可配置）
- 密码强度：至少 6 位（建议客户端增强）

---

### 2. 路由模块 (`app/routers/`)

**职责**：定义 API 端点，处理请求和响应

#### 主要路由

| 路由文件              | 前缀             | 描述                     |
| --------------------- | ---------------- | ------------------------ |
| `health.py`           | `/healthz`       | 健康检查                 |
| `auth.py`             | `/auth`          | 注册、登录               |
| `jobs.py`             | `/admin/jobs`    | 岗位 CRUD（Admin）       |
| `applications.py`     | `/applications`  | 投递 CRUD（Candidate）   |
| `admin_applications.py` | `/admin/applications` | 投递管理（Admin） |
| `chat.py`             | `/chat`          | 对话 HTTP API            |
| `websocket_chat.py`   | `/ws/chat`       | 对话 WebSocket           |
| `debug.py`            | `/debug`         | 调试接口（开发环境）     |

---

### 3. 服务模块 (`app/services/`)

#### 3.1 LLM 服务 (`llm_service.py`)

**职责**：封装 DashScope API 调用

**方法**：
- `parse_resume(text)`: 简历结构化解析
- `score_resume(text, jd)`: 简历评分
- `generate_questions(job_desc, resume_info)`: 生成面试题
- `chat_completion(messages)`: 通用 LLM 对话

**配置**：
- 模型：qwen-plus（默认）
- 超时：60 秒
- 重试：3 次（指数退避）

#### 3.2 文件存储服务 (`file_storage.py`)

**职责**：MinIO 对象存储操作

**方法**：
- `upload_file(bucket, object_name, file_data, content_type)`
- `download_file(bucket, object_name)`
- `list_files(bucket, prefix)`
- `init_buckets()`: 初始化桶（`resumes`, `voices`）

#### 3.3 状态机服务 (`state_machine.py`)

**职责**：管理 Application 状态转换

**状态定义**（`app/constants.py`）：
```
RESUME_UPLOADED → PARSING → PARSED → SCORING → SCORED → 
GENERATING_QUESTIONS → QUESTIONS_READY → INTERVIEW_SCHEDULED → 
INTERVIEW_COMPLETED → PASSED / REJECTED / HUMAN_REVIEW
```

**规则**：
- 只允许合法的状态转换
- 记录转换日志
- 失败时回退到 `HUMAN_REVIEW`

#### 3.4 对话服务 (`chat_service.py`)

**职责**：管理对话会话和消息

**方法**：
- `create_session(user_id, job_id, session_type)`
- `add_message(session_id, role, content, audio_url)`
- `get_session_messages(session_id, limit)`
- `generate_ai_response(session_id, user_message)`: LLM 生成回复

#### 3.5 语音服务 (`voice_service.py`)

**职责**：ASR 和 TTS

**方法**：
- `speech_to_text(audio_data)`: 语音 → 文字
- `text_to_speech(text)`: 文字 → 语音

**实现**：
- 生产环境：Alibaba Cloud NLS
- 开发环境：Mock（返回固定值）

---

### 4. 异步任务模块 (`worker/tasks.py`)

**职责**：执行耗时的 LLM 调用

#### 任务列表

| 任务函数                  | 触发条件                  | 后续任务              |
| ------------------------- | ------------------------- | --------------------- |
| `parse_application_task`  | 投递创建（状态：PARSING） | `score_application_task` |
| `score_application_task`  | 解析完成（状态：SCORING） | `generate_questions_task` |
| `generate_questions_task` | 评分完成（状态：GENERATING_QUESTIONS） | 无 |

#### 任务特性

- **幂等性**：基于 `TaskRun` 记录（`input_hash`）防止重复执行
- **重试机制**：失败后最多重试 3 次（指数退避）
- **异常处理**：失败后将状态设为 `HUMAN_REVIEW`
- **链式调用**：任务完成后自动触发下一个任务

---

### 5. 数据模型 (`app/models.py`)

核心模型：

- **User**: 用户（candidate/admin）
- **Job**: 岗位
- **QuestionBank**: 题库（关联 Job）
- **Application**: 投递申请
- **TaskRun**: 任务执行记录（幂等性）
- **ChatSession**: 对话会话
- **ChatMessage**: 对话消息

详细设计见 [DATABASE.md](./DATABASE.md)

---

## 数据流

### 1. 投递申请流程

```
1. Candidate 创建投递
   ├─ POST /applications
   │  └─ Body: { job_id, resume_file }
   │
2. API 处理
   ├─ 上传简历到 MinIO
   ├─ 创建 Application 记录（状态：RESUME_UPLOADED）
   ├─ 提取简历文本
   ├─ 更新状态为 PARSING
   └─ 将 parse_application_task 推入 RQ 队列
   │
3. Worker 处理
   ├─ parse_application_task
   │  ├─ 调用 LLM 解析简历
   │  ├─ 保存 resume_json
   │  ├─ 更新状态为 PARSED
   │  └─ 触发 score_application_task
   │
   ├─ score_application_task
   │  ├─ 调用 LLM 评分
   │  ├─ 保存 score_json
   │  ├─ 更新状态为 SCORED
   │  └─ 触发 generate_questions_task
   │
   └─ generate_questions_task
      ├─ 调用 LLM 生成题目
      ├─ 保存 questions_json
      └─ 更新状态为 QUESTIONS_READY
   │
4. Candidate 查询状态
   └─ GET /applications/{id}
      └─ 返回当前状态和结果
```

### 2. 实时对话流程

```
1. Candidate 建立连接
   ├─ WebSocket: /ws/chat/{session_id}?token=xxx
   │
2. 发送文本消息
   ├─ Client → Server: { "type": "text", "content": "你好" }
   ├─ Server 处理
   │  ├─ 保存用户消息到数据库
   │  ├─ 调用 LLM 生成回复
   │  ├─ 保存 AI 消息到数据库
   │  └─ Server → Client: { "type": "text", "content": "您好，我是..." }
   │
3. 发送语音消息
   ├─ Client → Server: { "type": "audio", "audio_data": "base64..." }
   ├─ Server 处理
   │  ├─ ASR（语音 → 文字）
   │  ├─ 调用 LLM 生成回复
   │  ├─ TTS（文字 → 语音）
   │  ├─ 上传语音文件到 MinIO
   │  ├─ 保存消息到数据库
   │  └─ Server → Client: { "type": "audio", "text": "...", "audio_url": "..." }
   │
4. 心跳机制
   ├─ Client → Server: { "type": "ping" }
   └─ Server → Client: { "type": "pong" }
```

---

## 安全设计

### 1. 认证与授权

- **JWT**: 无状态认证，7 天过期
- **RBAC**: 基于角色的权限控制（candidate/admin）
- **密码**: bcrypt 哈希 + 自动加盐

### 2. API 安全

- **CORS**: 配置允许的源（`CORS_ORIGINS`）
- **请求限速**: 防止 DDoS（待实现）
- **输入验证**: Pydantic 强类型校验
- **SQL 注入**: SQLAlchemy ORM 自动防护

### 3. 文件安全

- **类型检查**: 限制上传文件类型（PDF/DOCX/TXT）
- **大小限制**: 最大 10MB（`MAX_UPLOAD_SIZE`）
- **路径隔离**: 每个用户独立的 MinIO 路径

### 4. 错误处理

- **统一响应格式**:
  ```json
  {
    "code": 0,           // 0=成功, 其他=错误码
    "message": "ok",
    "data": {...},
    "request_id": "uuid"
  }
  ```
- **敏感信息隐藏**: 不暴露堆栈信息到客户端
- **日志记录**: 记录所有异常（带 request_id）

---

## 性能考虑

### 1. 异步处理

- **FastAPI**: 原生支持 `async/await`
- **RQ**: 耗时任务移到后台
- **并发**: Worker 可水平扩展

### 2. 数据库优化

- **索引**:
  - `User.email` (UNIQUE)
  - `Application.user_id`, `Application.job_id`
  - `ChatMessage.session_id`, `ChatMessage.created_at`
- **连接池**: SQLAlchemy 默认连接池
- **查询优化**: 使用 `joinedload` 减少 N+1 查询

### 3. 缓存策略

- **Redis**: 
  - 会话缓存（未实现）
  - 热门岗位缓存（未实现）
- **CDN**: 静态资源（前端）

### 4. 文件存储

- **MinIO**: 
  - 对象存储，支持大文件
  - 分布式，支持水平扩展
- **预签名 URL**: 直接从 MinIO 下载（减轻 API 负担）

### 5. LLM 调用优化

- **超时控制**: 60 秒
- **重试机制**: 指数退避
- **任务队列**: 削峰填谷

---

## 扩展性

### 1. 水平扩展

- **API Service**: 无状态，可部署多实例 + 负载均衡
- **Worker Service**: 增加 Worker 数量处理更多任务
- **MySQL**: 主从复制 + 读写分离
- **Redis**: Redis Cluster

### 2. 微服务化

当前是单体应用，未来可拆分为：
- **User Service**: 用户认证
- **Job Service**: 岗位管理
- **Application Service**: 投递管理
- **Chat Service**: 实时对话
- **LLM Gateway**: 统一 LLM 调用

### 3. 消息队列

当前使用 RQ，未来可迁移到：
- **RabbitMQ**: 更强大的消息路由
- **Kafka**: 高吞吐量、持久化

---

## 监控与日志

### 1. 日志

- **格式**: JSON 结构化日志
- **级别**: INFO（正常）、ERROR（异常）
- **输出**: 控制台（Docker）、文件（生产环境）

### 2. 监控指标（待实现）

- **API**: 请求速率、响应时间、错误率
- **Worker**: 队列长度、任务执行时间、失败率
- **数据库**: 连接数、查询时间
- **外部服务**: LLM API 可用性、响应时间

### 3. 告警（待实现）

- **错误率** > 5%
- **队列积压** > 1000
- **API 响应时间** > 3s

---

## 相关文档

- [数据库设计](./DATABASE.md)
- [快速开始](./QUICKSTART.md)
- [API 参考](./docs/frontend/API_REFERENCE.md)
- [Docker 部署](./docs/deployment/DOCKER.md)
- [测试指南](./TESTING.md)

---

**最后更新**: 2026-02-01
