import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://recruit_user:recruit_password@localhost:3306/recruit_flow",
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )

    # LLM (DashScope)
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", os.getenv("API_KEY", ""))
    LLM_TIMEOUT_S: int = int(os.getenv("LLM_TIMEOUT_S", "60"))
    LLM_MOCK: bool = os.getenv("LLM_MOCK", "1").lower() == "1"

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "recruit-flow")
    MINIO_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

    # Milvus
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_COLLECTION_NAME: str = os.getenv("MILVUS_COLLECTION_NAME", "recruit_kb")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "bge-base-zh-v1.5")

    # 应用
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    
    # 阿里云语音服务
    ALIYUN_ASR_APPKEY: str = os.getenv("ALIYUN_ASR_APPKEY", "")
    ALIYUN_ASR_TOKEN: str = os.getenv("ALIYUN_ASR_TOKEN", "")
    ALIYUN_TTS_APPKEY: str = os.getenv("ALIYUN_TTS_APPKEY", "")
    ALIYUN_TTS_TOKEN: str = os.getenv("ALIYUN_TTS_TOKEN", "")
    VOICE_MOCK: bool = os.getenv("VOICE_MOCK", "1").lower() == "1"  # 语音服务Mock模式

    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
