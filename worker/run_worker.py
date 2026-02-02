"""RQ Worker 启动脚本"""
import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redis import Redis
from rq import Worker, Queue
from app.config import settings

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 连接 Redis
redis_conn = Redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    logger.info("启动 RQ Worker...")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    
    # 监听队列
    queues = [Queue("default", connection=redis_conn)]
    
    # 启动 Worker
    worker = Worker(queues, connection=redis_conn)
    
    logger.info("RQ Worker 已启动，等待任务...")
    worker.work(with_scheduler=True)
