"""任务队列工厂"""
from redis import Redis
from rq import Queue
from rq.job import Job
from rq import Retry
from app.config import settings
import logging

logger = logging.getLogger(__name__)

redis_conn = Redis.from_url(settings.REDIS_URL)


def get_queue(name: str = "default") -> Queue:
    """获取任务队列"""
    return Queue(name, connection=redis_conn)


def enqueue_task(task_name: str, *args, retry_on_failure: int = 3, **kwargs):
    """
    入队任务
    
    Args:
        task_name: 任务名称（对应 worker/tasks.py 中的函数）
        *args: 任务参数
        retry_on_failure: 失败重试次数
        **kwargs: 任务关键字参数
        
    Returns:
        Job: RQ Job 对象
    """
    queue = get_queue()
    
    # 动态导入任务函数
    from worker import tasks
    task_func = getattr(tasks, task_name)
    
    # 配置重试
    retry_strategy = Retry(max=retry_on_failure) if retry_on_failure > 0 else None
    
    # 入队
    job = queue.enqueue(
        task_func,
        *args,
        retry=retry_strategy,
        **kwargs
    )
    
    logger.info(f"任务已入队: task={task_name}, job_id={job.id}, args={args}")
    return job


def get_job_status(job_id: str) -> dict:
    """
    获取任务状态
    
    Args:
        job_id: Job ID
        
    Returns:
        dict: 任务状态信息
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "job_id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "error": str(job.exc_info) if job.exc_info else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }
    except Exception as e:
        logger.error(f"获取任务状态失败: job_id={job_id}, error={e}")
        return {"job_id": job_id, "status": "unknown", "error": str(e)}
