# hereOffer 测试文档

## 📋 目录

- [测试概述](#测试概述)
- [测试文件列表](#测试文件列表)
- [快速开始](#快速开始)
- [测试分类](#测试分类)
- [测试说明](#测试说明)
- [故障排查](#故障排查)

---

## 📝 测试概述

hereOffer 项目包含完整的自动化测试套件，覆盖单元测试、功能测试、集成测试和端到端测试。

### 测试统计

| 测试类型 | 文件数 | 覆盖率 |
|---------|--------|--------|
| 单元测试 | 2 | 基础模块 |
| 功能测试 | 7 | 核心功能 |
| 集成测试 | 1 | 异步任务链 |
| 端到端测试 | 1 | 完整流程 |
| **总计** | **11** | **全面** |

---

## 📁 测试文件列表

### 1. 单元测试（tests/ 目录）

| 文件名 | 说明 |
|--------|------|
| `tests/test_basic.py` | 基础功能单元测试 |
| `tests/test_state_machine.py` | 状态机单元测试 |

### 2. 功能测试（Feature Tests）

| 文件名 | 测试模块 | 说明 |
|--------|---------|------|
| `test_storage_minio.py` | MinIO 文件存储 | 文件上传、下载、列表 |
| `test_llm_resume_parse.py` | LLM 简历解析 | 简历解析、评分 |
| `test_llm_questions_gen.py` | LLM 题目生成 | 面试题生成 |
| `test_api_applications.py` | 投递管理 API | 候选人投递 CRUD |
| `test_api_jobs.py` | 岗位管理 API | 岗位和题库管理 |
| `test_api_admin_applications.py` | Admin 投递管理 | 管理员查询、统计 |
| `test_api_chat_realtime.py` | 实时对话 | HTTP/WebSocket 对话 |

### 3. 集成测试（Integration Tests）

| 文件名 | 说明 |
|--------|------|
| `test_integration_async_chain.py` | 异步任务链端到端测试 |

### 4. 端到端测试（E2E Tests）

| 文件名 | 说明 |
|--------|------|
| `test_e2e_full_flow.sh` | 完整招聘流程测试 |

---

## 🚀 快速开始

### 方法 1：运行所有测试

```bash
# 自动运行所有测试并生成报告
python run_all_tests.py
```

### 方法 2：运行单个测试

```bash
# MinIO 文件存储测试
python test_storage_minio.py

# LLM 简历解析测试
python test_llm_resume_parse.py

# 实时对话测试
python test_api_chat_realtime.py
```

### 方法 3：运行端到端测试

```bash
# Windows PowerShell
bash test_e2e_full_flow.sh

# Linux/Mac
./test_e2e_full_flow.sh
```

---

## 📊 测试分类

### 按功能模块分类

```
用户认证
├── test_api_applications.py ✅
├── test_api_jobs.py ✅
└── test_api_admin_applications.py ✅

文件处理
├── test_storage_minio.py ✅
└── test_llm_resume_parse.py ✅

智能分析
├── test_llm_resume_parse.py ✅
└── test_llm_questions_gen.py ✅

业务流程
├── test_api_applications.py ✅
├── test_api_jobs.py ✅
├── test_api_admin_applications.py ✅
└── test_integration_async_chain.py ✅

实时通信
└── test_api_chat_realtime.py ✅
```

### 按测试类型分类

```
单元测试（Unit Tests）
├── test_basic.py
└── test_state_machine.py

功能测试（Feature Tests）
├── test_storage_minio.py
├── test_llm_resume_parse.py
├── test_llm_questions_gen.py
├── test_api_applications.py
├── test_api_jobs.py
├── test_api_admin_applications.py
└── test_api_chat_realtime.py

集成测试（Integration Tests）
└── test_integration_async_chain.py

端到端测试（E2E Tests）
└── test_e2e_full_flow.sh
```

---

## 📖 测试说明

### test_storage_minio.py

**测试目标**：MinIO 对象存储功能

**测试步骤**：
1. 上传简历文件到 MinIO
2. 列出用户的所有文件
3. 下载文件并验证内容

**前置条件**：
- MinIO 服务运行
- 有效的 JWT Token
- 存在测试文件 `test_resume_zh.txt`

**运行时间**：~5 秒

---

### test_llm_resume_parse.py

**测试目标**：LLM 简历解析和评分

**测试步骤**：
1. 上传简历并调用 LLM 解析
2. 提取结构化信息（姓名、教育、经验等）
3. 根据岗位要求进行智能评分
4. 生成优势/不足分析和建议

**前置条件**：
- LLM 服务（DashScope）运行
- 有效的 API Key
- 存在测试简历文件

**运行时间**：~60 秒

---

### test_llm_questions_gen.py

**测试目标**：LLM 面试题目生成

**测试步骤**：
1. 使用解析后的简历数据
2. 调用 LLM 生成个性化面试题
3. 验证题目数量（≥20道）
4. 检查题目分类和难度

**前置条件**：
- 完成简历解析测试
- LLM 服务运行

**运行时间**：~90 秒

---

### test_api_applications.py

**测试目标**：候选人投递管理

**测试步骤**：
1. 注册候选人并登录
2. 创建投递（上传简历）
3. 查询投递状态
4. 更新投递状态

**前置条件**：
- API 服务运行
- 存在测试简历文件

**运行时间**：~10 秒

---

### test_api_jobs.py

**测试目标**：岗位和题库管理

**测试步骤**：
1. 管理员创建岗位
2. 更新岗位题库（20道题）
3. 候选人查看岗位列表
4. 候选人通过 job_id 投递

**前置条件**：
- API 服务运行
- 管理员和候选人账号

**运行时间**：~15 秒

---

### test_api_admin_applications.py

**测试目标**：管理员投递管理

**测试步骤**：
1. 创建多个测试投递
2. 测试投递列表查询
3. 测试多维度筛选（岗位、状态、分数）
4. 查看投递详情
5. 手动更新投递状态
6. 查询统计信息

**前置条件**：
- API 服务运行
- 存在测试投递数据

**运行时间**：~20 秒

---

### test_api_chat_realtime.py

**测试目标**：实时对话功能

**测试步骤**：
1. HTTP API 测试
   - 创建文本/语音会话
   - 发送消息并获取回复
   - 获取消息历史
   - 查询所有会话
2. WebSocket 测试
   - 建立 WebSocket 连接
   - 实时文本对话
   - 心跳机制
   - 语音消息（Mock）

**前置条件**：
- API 服务运行
- WebSocket 支持
- LLM 服务运行

**运行时间**：~30 秒

---

### test_integration_async_chain.py

**测试目标**：异步任务链完整流程

**测试步骤**：
1. 创建投递（触发任务链）
2. 等待简历解析完成
3. 等待简历评分完成
4. 等待题目生成完成
5. 验证最终状态和数据

**前置条件**：
- 所有服务运行（API、Worker、Redis、MySQL）
- LLM 服务运行

**运行时间**：~120 秒

---

### test_e2e_full_flow.sh

**测试目标**：完整招聘流程

**测试步骤**：
1. 健康检查
2. 用户注册和登录
3. 创建岗位
4. 提交投递
5. 查询投递状态
6. 管理员查看投递
7. 完整流程验证

**前置条件**：
- 所有服务运行
- 能够执行 bash 脚本

**运行时间**：~60 秒

---

## 🔍 故障排查

### 测试失败：连接被拒绝

**问题**：`Connection refused` 或 `Connection reset`

**解决方案**：
```bash
# 检查服务是否运行
docker-compose ps

# 重启服务
docker-compose restart api

# 查看日志
docker-compose logs api
```

---

### 测试失败：Token 无效

**问题**：`Invalid token` 或 `401 Unauthorized`

**解决方案**：
```bash
# 重新登录获取新 Token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# 更新测试文件中的 TOKEN 变量
```

---

### 测试失败：LLM 超时

**问题**：`Timeout` 或 `LLM 调用失败`

**解决方案**：
```bash
# 检查 LLM_MOCK 配置
echo $LLM_MOCK

# 使用 Mock 模式
export LLM_MOCK=1

# 或检查 DashScope API Key
echo $DASHSCOPE_API_KEY
```

---

### 测试失败：数据库错误

**问题**：`Unknown column` 或 `Table doesn't exist`

**解决方案**：
```bash
# 重建数据库
docker-compose down -v
docker-compose up -d

# 等待服务启动
sleep 15
```

---

## 📊 测试覆盖矩阵

| 功能模块 | 单元测试 | 功能测试 | 集成测试 | E2E测试 |
|---------|---------|---------|---------|---------|
| 用户认证 | ✅ | ✅ | ✅ | ✅ |
| 文件存储 | - | ✅ | ✅ | ✅ |
| 简历解析 | - | ✅ | ✅ | ✅ |
| 简历评分 | - | ✅ | ✅ | ✅ |
| 题目生成 | - | ✅ | ✅ | ✅ |
| 投递管理 | - | ✅ | ✅ | ✅ |
| 岗位管理 | - | ✅ | - | ✅ |
| Admin 管理 | - | ✅ | - | ✅ |
| 实时对话 | - | ✅ | - | - |
| WebSocket | - | ✅ | - | - |
| 状态机 | ✅ | ✅ | ✅ | ✅ |
| 异步任务 | - | - | ✅ | ✅ |

---

## 🎯 测试最佳实践

### 1. 测试前准备

```bash
# 确保所有服务运行
docker-compose ps

# 检查服务健康
curl http://localhost:8000/healthz
```

### 2. 运行测试

```bash
# 推荐：使用测试运行器
python run_all_tests.py

# 或逐个运行
python test_storage_minio.py
python test_llm_resume_parse.py
# ...
```

### 3. 查看结果

- 控制台输出：实时查看测试进度
- 测试日志：详细的执行信息
- 返回码：0=全部通过，1=有失败

### 4. 持续集成

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d
          sleep 30
          python run_all_tests.py
```

---

## 📝 补充说明

### 旧文件命名对照表

| 旧文件名 | 新文件名 | 说明 |
|---------|---------|------|
| `test_t05_auto.py` | `test_storage_minio.py` | 更清晰的命名 |
| `test_t07_auto.py` | `test_llm_resume_parse.py` | 表明测试内容 |
| `test_t09_auto.py` | `test_llm_questions_gen.py` | 功能导向 |
| `test_t10_auto.py` | `test_api_applications.py` | API 层次清晰 |
| `test_t13_jobs.py` | `test_api_jobs.py` | 统一命名风格 |
| `test_t21_admin_apps.py` | `test_api_admin_applications.py` | 完整描述 |
| `test_realtime_chat.py` | `test_api_chat_realtime.py` | 分类明确 |
| `test_async_chain.py` | `test_integration_async_chain.py` | 测试类型明确 |
| `test_e2e.sh` | `test_e2e_full_flow.sh` | 描述性更强 |

### 文件清理

旧的测试文件可以安全删除：

```bash
# 备份旧文件（可选）
mkdir old_tests
mv test_t*.py old_tests/
mv test_async_chain.py old_tests/
mv test_realtime_chat.py old_tests/
mv test_e2e.sh old_tests/

# 或直接删除
rm test_t*.py test_async_chain.py test_realtime_chat.py test_e2e.sh
```

---

## 🔗 相关文档

- [TESTS_INDEX.md](TESTS_INDEX.md) - 测试文件索引
- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构文档

---

**最后更新**: 2026-02-01  
**维护者**: hereOffer Team
