"""Alembic 环境配置"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import Base

# 此对象用于 autogenerate 支持
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线迁移模式"""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线迁移模式"""
    configuration = context.config

    # 从 env 读取 DATABASE_URL
    configuration.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
