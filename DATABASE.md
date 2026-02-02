# 数据库设计文档

## 📋 目录

- [概述](#概述)
- [数据库选型](#数据库选型)
- [数据表设计](#数据表设计)
- [ER 图](#er-图)
- [索引设计](#索引设计)
- [数据迁移](#数据迁移)

---

## 概述

hereOffer 使用 MySQL 8.0 作为主数据库，存储用户、岗位、投递、简历等核心业务数据。

### 设计原则

- **规范化设计** - 遵循第三范式，减少数据冗余
- **索引优化** - 为高频查询字段添加索引
- **JSON 存储** - 灵活的非结构化数据使用 JSON 类型
- **软删除** - 重要数据采用状态标记而非物理删除
- **时间戳** - 所有表都有 created_at 和 updated_at

---

## 数据库选型

### MySQL 8.0

**选择原因**：
- ✅ 成熟稳定，生态完善
- ✅ JSON 类型支持良好
- ✅ 事务支持完整（ACID）
- ✅ 索引优化强大
- ✅ 主从复制方便

**配置要求**：
- 版本：8.0+
- 字符集：utf8mb4
- 排序规则：utf8mb4_unicode_ci
- 最大连接数：1000+

---

## 数据表设计

### 1. users（用户表）

**用途**：存储系统用户信息（候选人和管理员）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 用户ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | 邮箱（登录名） |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| user_type | VARCHAR(50) | NOT NULL | 用户类型：candidate/admin |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'active' | 状态：active/disabled |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX idx_email (email)
- INDEX idx_user_type (user_type)

---

### 2. jobs（岗位表）

**用途**：存储招聘岗位信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 岗位ID |
| title | VARCHAR(255) | NOT NULL | 职位名称 |
| description | TEXT | NOT NULL | 职位描述/JD |
| requirements | TEXT | NULL | 职位要求 |
| responsibilities | TEXT | NULL | 工作职责 |
| department | VARCHAR(100) | NULL | 部门 |
| location | VARCHAR(100) | NULL | 工作地点 |
| salary_range | VARCHAR(100) | NULL | 薪资范围 |
| threshold_score | INT | NOT NULL, DEFAULT 60 | 评分阈值 |
| question_bank_json | JSON | NULL | 题库（JSON数组） |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否开放 |
| created_by | INT | NOT NULL | 创建者（Admin ID） |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_is_active (is_active)
- INDEX idx_created_by (created_by)

---

### 3. applications（投递表）

**用途**：存储候选人投递记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 投递ID |
| user_id | INT | NOT NULL, INDEX | 候选人ID |
| job_id | INT | NULL, INDEX | 岗位ID（可选） |
| job_title | VARCHAR(255) | NOT NULL | 职位名称 |
| job_description | TEXT | NULL | 职位描述 |
| resume_path | VARCHAR(500) | NULL | 简历文件路径 |
| resume_text | TEXT | NULL | 简历文本 |
| resume_json | JSON | NULL | 结构化简历数据 |
| score_json | JSON | NULL | 评分数据 |
| questions_json | JSON | NULL | 面试题数据 |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'PARSING' | 处理状态 |
| error_detail | TEXT | NULL | 错误详情 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_user_id (user_id)
- INDEX idx_job_id (job_id)
- INDEX idx_status (status)
- INDEX idx_created_at (created_at)

**状态流转**：
```
PARSING → PARSED → SCORING → SCORED → QUESTIONS_READY
                                    ↓
                              HUMAN_REVIEW
                                    ↓
                          REJECTED / NEXT_ROUND
```

---

### 4. resumes（简历表）

**用途**：存储简历文件元数据和解析结果

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 简历ID |
| owner_user_id | INT | NOT NULL, INDEX | 所属用户ID |
| file_name | VARCHAR(255) | NOT NULL | 文件名 |
| file_type | VARCHAR(50) | NOT NULL | 文件类型：pdf/docx/txt |
| storage_url | VARCHAR(500) | NOT NULL | 存储路径（MinIO） |
| extracted_text | TEXT | NULL | 提取的文本 |
| parse_result_json | JSON | NULL | 解析结果 |
| parse_confidence | FLOAT | NULL | 解析置信度 |
| parser_version | VARCHAR(50) | NULL | 解析器版本 |
| error_detail | TEXT | NULL | 错误详情 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_owner_user_id (owner_user_id)

---

### 5. chat_sessions（聊天会话表）

**用途**：存储对话会话信息

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 会话ID |
| user_id | INT | NOT NULL, INDEX | 用户ID |
| job_id | INT | NULL, INDEX | 关联岗位ID |
| session_type | VARCHAR(50) | NOT NULL, DEFAULT 'text' | 类型：text/voice |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否活跃 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_user_id (user_id)
- INDEX idx_job_id (job_id)

---

### 6. chat_messages（聊天消息表）

**用途**：存储对话消息内容

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 消息ID |
| session_id | INT | NOT NULL, INDEX | 会话ID |
| role | VARCHAR(50) | NOT NULL | 角色：user/assistant |
| content | TEXT | NOT NULL | 消息内容 |
| message_type | VARCHAR(50) | NOT NULL, DEFAULT 'text' | 类型：text/audio |
| audio_url | VARCHAR(500) | NULL | 音频URL |
| audio_duration | FLOAT | NULL | 音频时长（秒） |
| citations_json | JSON | NULL | 引用来源 |
| metadata_json | JSON | NULL | 元数据 |
| created_at | DATETIME | NOT NULL | 创建时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_session_id (session_id)
- INDEX idx_created_at (created_at)

---

### 7. task_runs（任务执行记录表）

**用途**：记录异步任务执行情况，实现幂等性

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 记录ID |
| task_name | VARCHAR(100) | NOT NULL | 任务名称 |
| application_id | INT | NOT NULL, INDEX | 投递ID |
| input_hash | VARCHAR(255) | NOT NULL | 输入哈希 |
| status | VARCHAR(50) | NOT NULL | 状态：pending/success/failed |
| last_error | TEXT | NULL | 最后错误 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_application_id (application_id)
- INDEX idx_task_name_input_hash (task_name, input_hash)

---

## ER 图

```
┌─────────────┐
│   users     │
│─────────────│
│ id (PK)     │
│ email       │
│ user_type   │
└──────┬──────┘
       │
       │ 1:N
       │
       ▼
┌─────────────────┐
│  applications   │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │◄───────┐
│ job_id (FK)     │        │
│ status          │        │
│ resume_json     │        │
│ score_json      │        │
└─────────────────┘        │
       ▲                   │
       │                   │
       │ 1:N               │
       │                   │
┌──────┴──────┐            │
│  task_runs  │            │
│─────────────│            │
│ id (PK)     │            │
│ app_id (FK) │            │
└─────────────┘            │
                           │
                           │ N:1
                           │
                    ┌──────┴──────┐
                    │    jobs     │
                    │─────────────│
                    │ id (PK)     │
                    │ title       │
                    │ is_active   │
                    └─────────────┘

┌──────────────────┐
│  chat_sessions   │
│──────────────────│
│ id (PK)          │
│ user_id (FK)     │
│ job_id (FK)      │
└────────┬─────────┘
         │
         │ 1:N
         │
         ▼
┌──────────────────┐
│  chat_messages   │
│──────────────────│
│ id (PK)          │
│ session_id (FK)  │
│ role             │
│ content          │
└──────────────────┘
```

---

## 索引设计

### 查询优化

#### 高频查询

1. **按用户查询投递**
```sql
SELECT * FROM applications WHERE user_id = ? ORDER BY created_at DESC;
```
索引：`idx_user_id`, `idx_created_at`

2. **按岗位查询投递**
```sql
SELECT * FROM applications WHERE job_id = ? AND status = ?;
```
索引：`idx_job_id`, `idx_status`

3. **管理员查询投递列表**
```sql
SELECT * FROM applications 
WHERE job_id = ? AND status = ? 
  AND JSON_EXTRACT(score_json, '$.overall_score') >= ?
ORDER BY created_at DESC;
```
索引：`idx_job_id`, `idx_status`, `idx_created_at`

#### 复合索引

```sql
-- 投递查询优化
CREATE INDEX idx_app_query ON applications(user_id, status, created_at);

-- 任务幂等性检查
CREATE INDEX idx_task_idempotent ON task_runs(task_name, input_hash);

-- 会话消息查询
CREATE INDEX idx_msg_query ON chat_messages(session_id, created_at);
```

---

## 数据迁移

### Alembic 配置

使用 Alembic 进行数据库版本管理：

```bash
# 创建迁移
alembic revision --autogenerate -m "Add new table"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 初始化脚本

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS hereoffer 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS 'recruit_user'@'%' 
  IDENTIFIED BY 'recruit_password';

-- 授权
GRANT ALL PRIVILEGES ON hereoffer.* 
  TO 'recruit_user'@'%';

FLUSH PRIVILEGES;
```

---

## JSON 数据结构

### resume_json（简历数据）

```json
{
  "name": "张三",
  "contact": {
    "email": "zhangsan@example.com",
    "phone": "138-0000-0000"
  },
  "education": [
    {
      "school": "清华大学",
      "degree": "硕士",
      "major": "计算机科学",
      "start_year": 2022,
      "end_year": 2024,
      "gpa": "3.9/4.0"
    }
  ],
  "work_experience": [
    {
      "company": "阿里巴巴",
      "position": "高级后端工程师",
      "start_date": "2024-06",
      "end_date": "至今",
      "description": "负责电商核心系统开发..."
    }
  ],
  "skills": ["Python", "FastAPI", "MySQL", "Redis"]
}
```

### score_json（评分数据）

```json
{
  "overall_score": 85,
  "education_score": 90,
  "experience_score": 80,
  "skills_score": 85,
  "match_analysis": "候选人综合素质优秀...",
  "strengths": ["学历优秀", "技术栈匹配"],
  "weaknesses": ["缺少分布式经验"],
  "recommendation": "PASS"
}
```

### questions_json（题目数据）

```json
{
  "questions": [
    {
      "id": 1,
      "category": "Python基础",
      "question": "请解释Python的GIL机制",
      "difficulty": "中等",
      "reference_answer": "...",
      "scoring_points": ["理解GIL概念", "知道影响", "能举例"]
    }
  ],
  "total_count": 20,
  "version": 1
}
```

---

## 性能优化

### 查询优化建议

1. **避免全表扫描** - 为常用查询字段添加索引
2. **JSON 查询优化** - 使用虚拟列或生成列
3. **分页查询** - 使用 LIMIT + OFFSET
4. **读写分离** - 主从复制架构
5. **连接池** - 使用 SQLAlchemy 连接池

### 监控指标

- 慢查询日志（>1秒）
- 索引使用率
- 表锁等待时间
- 连接池状态

---

## 备份策略

### 定时备份

```bash
# 每天凌晨 2 点全量备份
mysqldump -u root -p hereoffer > backup_$(date +%Y%m%d).sql

# 保留最近 30 天
find /backup -name "backup_*.sql" -mtime +30 -delete
```

### 恢复

```bash
# 恢复数据库
mysql -u root -p hereoffer < backup_20260201.sql
```

---

**最后更新**: 2026-02-01  
**维护者**: hereOffer Team
