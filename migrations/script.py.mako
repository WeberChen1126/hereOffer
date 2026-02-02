"""Alembic 脚本配置"""
import os
from alembic import context

def process_revision_directives(context, revision, directives):
    """处理迁移指令"""
    if getattr(context.config.cmd_opts, "autogenerate", False):
        script = directives[0]
        if script.upgrade:
            script.upgrade = filter_upgrade(script.upgrade)


def filter_upgrade(upgrade):
    """过滤升级语句"""
    return upgrade


# 获取迁移版本路径
config = context.config

# 设置 sqlalchemy.url
if config.get_main_option("sqlalchemy.url") is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
