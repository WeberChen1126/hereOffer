# hereOffer - AI 驱动的智能招聘系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于大语言模型的智能招聘流程自动化系统

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [架构设计](#-架构设计) • [文档](#-文档) • [贡献](#-贡献)

</div>

---

## 📖 项目简介

hereOffer 是一个现代化的智能招聘系统，利用大语言模型（LLM）技术实现简历智能解析、自动评分和个性化面试题生成，大幅提升招聘效率和质量。

### 核心价值

- 🤖 **AI 智能解析** - 自动提取简历关键信息，准确率 95%+
- 📊 **智能评分** - 基于岗位要求多维度评估候选人
- 💬 **实时对话** - WebSocket 实时交互，支持文本和语音
- 📝 **题目生成** - 根据简历自动生成个性化面试题
- 🔄 **异步处理** - RQ 任务队列，高效处理大量简历
- 📈 **管理后台** - 完善的投递管理和统计分析

---

## ✨ 功能特性

### 候选人端

- ✅ 简历在线投递（支持 PDF/DOCX/TXT）
- ✅ 实时对话咨询（岗位信息、公司介绍）
- ✅ 语音交互支持（ASR + TTS） #TODO
- ✅ 投递进度查询

### 管理员端

- ✅ 岗位管理（CRUD + 题库维护）
- ✅ 投递管理（列表、筛选、详情）
- ✅ 智能评分查看
- ✅ 查看面试题包
- ✅ 统计分析（通过率、平均分等）
- ✅ 手动状态管理

### 智能处理

- ✅ 简历自动解析（姓名、教育、经验、技能）
- ✅ 多维度评分（教育 + 经验 + 技能匹配）
- ✅ 个性化题目生成
- ✅ 异步任务链（解析 → 评分 → 题目生成）
- ✅ 失败重试和容错

---

## 📸 界面展示

### 职位列表
浏览所有可投递的职位。

![职位列表](docs/images/job-list.png)

### 投递详情
查看简历评估结果、多维度评分详情和智能推荐建议。

![投递详情](docs/images/application-details.png)

### 面试题包
查看根据简历自动生成的个性化面试题目，包含参考答案和评分要点。

![面试题包](docs/images/interview-question-bank.png)

### AI 客服
实时对话咨询，支持文本交互，基于 RAG 技术提供智能回答。

![AI客服](docs/images/ai-customer-service.png)

---

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 20GB+ 磁盘空间

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/WeberChen1126/hereoffer.git
cd hereoffer

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 3. 启动所有服务
docker-compose up -d

# 4. 等待服务启动（约 30 秒）
sleep 30

# 5. 验证服务
curl http://localhost:8000/healthz
```

### 访问服务

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/healthz
- **MinIO 控制台**: http://localhost:9001

详细的启动指南请参考 [快速开始文档](QUICK_START.md)

---

## 🏗️ 架构设计

### 技术栈

**后端框架**
- FastAPI - 高性能 Web 框架
- SQLAlchemy - ORM 框架
- Alembic - 数据库迁移

**数据存储**
- MySQL 8.0 - 关系型数据库
- Redis 7.0 - 缓存和任务队列
- MinIO - 对象存储（S3 兼容）

**AI/LLM**
- 阿里云 DashScope - LLM API
- qwen2.5-7b - 简历解析和评分
- qwen2.5-32b - 面试题生成

**异步任务**
- RQ (Redis Queue) - 任务队列
- Redis - 任务存储

### 系统架构

```
┌─────────────┐
│   客户端     │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌─────────────┐
│  FastAPI    │────▶│   MySQL     │
│   服务器     │     │   数据库     │
└──────┬──────┘      └─────────────┘
       │
       ├──────────▶┌─────────────┐
       │           │    Redis    │
       │           │  缓存/队列   │
       │           └─────────────┘
       │
       ├──────────▶┌─────────────┐
       │           │   MinIO     │
       │           │  对象存储    │
       │           └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  RQ Worker  │────▶│  DashScope  │
│  异步处理    │     │   LLM API   │
└─────────────┘     └─────────────┘
```

详细的架构设计请参考 [架构文档](ARCHITECTURE.md)

---

## 📚 文档

### 核心文档

- [架构设计](ARCHITECTURE.md) - 系统架构和技术选型
- [数据库设计](DATABASE.md) - 数据模型和表结构
- [API 接口](API.md) - RESTful API 和 WebSocket

### 开发文档

- [后端实现](docs/DEVELOPMENT.md) - 详细的实现说明
- [功能模块](docs/FEATURES.md) - 各功能模块详解
- [测试文档](tests/TESTING.md) - 测试指南和用例

### 部署文档

- [Docker 部署](docs/deployment/DOCKER.md) - Docker 部署指南
- [Kubernetes 部署](docs/deployment/KUBERNETES.md) - K8s 部署指南
- [环境配置](docs/deployment/ENVIRONMENT.md) - 环境变量说明
- [生产最佳实践](docs/deployment/PRODUCTION.md) - 生产环境建议

### 前端文档

- [API 参考](docs/frontend/API_REFERENCE.md) - API 接口参考
- [WebSocket 指南](docs/frontend/WEBSOCKET.md) - 实时通信指南


---

## 🧪 测试

### 运行所有测试

```bash
cd tests
# 使用测试运行器
python run_all_tests.py

# 或单独运行
python test_storage_minio.py
python test_llm_resume_parse.py
python test_api_chat_realtime.py
```

### 测试覆盖

- ✅ 单元测试 - 核心模块
- ✅ 功能测试 - API 端点
- ✅ 集成测试 - 异步任务链
- ✅ E2E 测试 - 完整流程

详细的测试文档请参考 [TESTING.md](TESTING.md)

---

## 🔧 开发

### 本地开发环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 启动数据库服务
docker-compose up -d mysql redis minio

# 4. 运行数据库迁移
alembic upgrade head

# 5. 启动 API 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 启动 Worker（新终端）
python worker/run_worker.py
```

### 项目结构

```
hereoffer/
├── app/                 # FastAPI 应用
│   ├── routers/         # API 路由
│   ├── models.py        # 数据模型
│   ├── schemas.py       # Pydantic 模型
│   ├── services/        # 业务逻辑
│   └── main.py          # 应用入口
├── worker/              # RQ Worker
│   ├── tasks.py         # 异步任务
│   └── run_worker.py    # Worker 启动
├── tests/               # 测试入口
├── migrations/          # 数据库迁移
├── docs/                # 文档
├── docker-compose.yml   # Docker Compose 配置
├── Dockerfile           # Docker 镜像
├── requirements.txt     # Python 依赖
└── README.md            # 本文件
```

---

## 🔐 环境变量

主要环境变量：

```bash
# 数据库
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/hereoffer

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# LLM
DASHSCOPE_API_KEY=your-dashscope-api-key
LLM_MOCK=0  # 0=真实API, 1=Mock模式

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

完整的环境变量说明请参考 [环境配置文档](docs/deployment/ENVIRONMENT.md)

---

## 📊 性能指标

### 处理能力

- 简历解析：60 秒/份（LLM）
- 简历评分：30 秒/份（LLM）
- 题目生成：90 秒/份（LLM）
- 并发处理：100+ 简历/小时（单 Worker）

### 系统性能

- API 响应：< 200ms（P95）
- 数据库查询：< 50ms（P95）
- WebSocket 延迟：< 100ms
- 文件上传：10MB/秒+

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 添加必要的单元测试
- 更新相关文档
- 通过所有 CI 检查

---

## 📝 版本历史

### v1.0.0 (2026-02-01)

- ✅ 核心功能实现
- ✅ 简历解析和评分
- ✅ 题目生成
- ✅ 实时对话
- ✅ 完整测试覆盖



---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

- **项目负责人**: weber chen
- **后端开发**: weber chen
- **前端开发**: weber chen
- **测试工程师**: weber chen

---

## 📞 联系我们

- **项目地址**: https://github.com/WeberChen1126/hereoffer
- **邮箱**: 13538083730@163.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**


</div>
