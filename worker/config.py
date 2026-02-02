"""RQ Worker 配置"""
import os
from redis import Redis
from app.config import settings

# Redis 连接
redis_conn = Redis.from_url(settings.REDIS_URL)

# 任务队列设置
RQ_QUEUE_NAME = "default"
RQ_RESULT_TTL = 500
RQ_FAILURE_TTL = 86400

# Worker 设置
WORKER_NAME = os.getenv("WORKER_NAME", "recruit_flow_worker")
WORKER_RESULT_TTL = 500
WORKER_FAILURE_TTL = 86400
WORKER_JOB_MONITORING_INTERVAL = 30
WORKER_DEFAULT_RESULT_TTL = 500
