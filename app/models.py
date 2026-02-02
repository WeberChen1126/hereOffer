"""基础 ORM 模型"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False)  # 'candidate' or 'admin'
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Candidate(Base):
    """候选人表"""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Resume(Base):
    """简历表"""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    storage_url = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    parse_result_json = Column(JSON, nullable=True)
    parse_confidence = Column(Float, nullable=True)
    parser_version = Column(String(50), nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Job(Base):
    """岗位表"""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)  # 职位名称
    description = Column(Text, nullable=False)  # 职位描述/JD
    requirements = Column(Text, nullable=True)  # 职位要求
    responsibilities = Column(Text, nullable=True)  # 工作职责
    department = Column(String(100), nullable=True)  # 部门
    location = Column(String(100), nullable=True)  # 工作地点
    salary_range = Column(String(100), nullable=True)  # 薪资范围
    threshold_score = Column(Integer, default=60, nullable=False)  # 评分阈值
    question_bank_json = Column(JSON, nullable=True)  # 题库（JSON 数组）
    is_active = Column(Boolean, default=True, nullable=False)  # 是否开放
    created_by = Column(Integer, nullable=False)  # 创建者（Admin user_id）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Application(Base):
    """投递表"""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    job_id = Column(Integer, nullable=True, index=True)  # 关联岗位（可选，兼容旧数据）
    job_title = Column(String(255), nullable=False)  # 职位名称
    job_description = Column(Text, nullable=True)  # 职位描述/JD
    resume_path = Column(String(500), nullable=True)  # 简历文件路径（MinIO）
    resume_text = Column(Text, nullable=True)  # 简历文本
    resume_json = Column(JSON, nullable=True)  # 结构化简历数据
    score_json = Column(JSON, nullable=True)  # 评分数据
    questions_json = Column(JSON, nullable=True)  # 面试题数据
    status = Column(String(50), default="PARSING", nullable=False)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InterviewQuestionPack(Base):
    """面试题包表"""

    __tablename__ = "interview_question_packs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=False, index=True)
    pack_json = Column(JSON, nullable=False)
    generator_version = Column(String(50), nullable=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSession(Base):
    """聊天会话表"""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    job_id = Column(Integer, nullable=True, index=True)
    session_type = Column(String(50), default="text", nullable=False)  # text, voice
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """聊天消息表"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)  # text, audio
    audio_url = Column(String(500), nullable=True)  # 音频文件URL（如果是语音消息）
    audio_duration = Column(Float, nullable=True)  # 音频时长（秒）
    citations_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # 额外元数据（如ASR置信度等）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class KBDocument(Base):
    """知识库文档表"""

    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KBChunk(Base):
    """知识库文本块表"""

    __tablename__ = "kb_chunks"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    milvus_id = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    """审计日志表"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=True)
    detail_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TaskRun(Base):
    """任务执行记录表（用于幂等性）"""

    __tablename__ = "task_runs"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100), nullable=False)
    application_id = Column(Integer, nullable=False, index=True)
    input_hash = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # pending, success, failed
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
