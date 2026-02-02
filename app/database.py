"""数据库连接配置"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话的依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
