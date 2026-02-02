"""初始迁移：创建所有表

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级迁移"""
    # users 表
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("user_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # candidates 表
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidates_user_id"), "candidates", ["user_id"])

    # jobs 表
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("jd_text", sa.Text(), nullable=False),
        sa.Column("threshold_score", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # question_banks 表
    op.create_table(
        "question_banks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("questions_json", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_banks_job_id"), "question_banks", ["job_id"])

    # resumes 表
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("storage_url", sa.String(500), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("parse_result_json", sa.JSON(), nullable=True),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("parser_version", sa.String(50), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_owner_user_id"), "resumes", ["owner_user_id"])

    # applications 表
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PARSING"),
        sa.Column("score_total", sa.Float(), nullable=True),
        sa.Column("score_breakdown_json", sa.JSON(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"])
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"])

    # interview_question_packs 表
    op.create_table(
        "interview_question_packs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("pack_json", sa.JSON(), nullable=False),
        sa.Column("generator_version", sa.String(50), nullable=True),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interview_question_packs_application_id"),
        "interview_question_packs",
        ["application_id"],
    )

    # chat_sessions 表
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"])
    op.create_index(op.f("ix_chat_sessions_job_id"), "chat_sessions", ["job_id"])

    # chat_messages 表
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"])

    # kb_documents 表
    op.create_table(
        "kb_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # kb_chunks 表
    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("milvus_id", sa.String(255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_kb_chunks_doc_id"), "kb_chunks", ["doc_id"])

    # audit_logs 表
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # task_runs 表
    op.create_table(
        "task_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(100), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("input_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_runs_application_id"), "task_runs", ["application_id"])


def downgrade() -> None:
    """降级迁移"""
    op.drop_table("task_runs")
    op.drop_table("audit_logs")
    op.drop_table("kb_chunks")
    op.drop_table("kb_documents")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("interview_question_packs")
    op.drop_table("applications")
    op.drop_table("resumes")
    op.drop_table("question_banks")
    op.drop_table("jobs")
    op.drop_table("candidates")
    op.drop_table("users")
