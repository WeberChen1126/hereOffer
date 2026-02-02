# 环境变量配置说明

## 数据库配置
- `DATABASE_URL`: MySQL 连接字符串（格式：`mysql+pymysql://user:password@host:port/database`）

## Redis 配置
- `REDIS_URL`: Redis 连接字符串（默认：`redis://localhost:6379/0`）

## JWT 认证
- `SECRET_KEY`: JWT 签名密钥（生产环境请修改）
- `ALGORITHM`: JWT 算法（默认：HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（分钟）

## 大语言模型 (LLM)
- `API_KEY`: 阿里云 DashScope API 密钥
- `LLM_TIMEOUT_S`: LLM 请求超时时间（秒）
- `LLM_MOCK`: 是否使用 Mock 模式（1 = 开启，0 = 关闭）

## MinIO 对象存储
- `MINIO_ENDPOINT`: MinIO 服务地址
- `MINIO_ACCESS_KEY`: MinIO 访问密钥
- `MINIO_SECRET_KEY`: MinIO 秘密密钥
- `MINIO_BUCKET`: 默认存储桶名称
- `MINIO_USE_SSL`: 是否使用 SSL 连接

## Milvus 向量数据库
- `MILVUS_HOST`: Milvus 服务地址
- `MILVUS_PORT`: Milvus 端口
- `MILVUS_COLLECTION_NAME`: Collection 名称
- `EMBEDDING_DIM`: 嵌入向量维度
- `EMBEDDING_MODEL`: 嵌入模型名称

## 应用配置
- `DEBUG`: 调试模式
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）
