"""MinIO 文件存储服务"""
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from typing import Optional
import io
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# MinIO 客户端
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,  # 本地开发使用 HTTP
)

# 存储桶名称
RESUME_BUCKET = "resumes"


def init_buckets():
    """初始化存储桶"""
    try:
        if not minio_client.bucket_exists(RESUME_BUCKET):
            minio_client.make_bucket(RESUME_BUCKET)
            logger.info(f"创建存储桶: {RESUME_BUCKET}")
        else:
            logger.info(f"存储桶已存在: {RESUME_BUCKET}")
    except S3Error as e:
        logger.error(f"初始化存储桶失败: {e}")
        raise


def upload_resume_file(
    user_id: int, application_id: int, file_bytes: bytes, filename: str
) -> str:
    """
    上传简历文件到 MinIO
    
    Args:
        user_id: 用户 ID
        application_id: 投递记录 ID
        file_bytes: 文件内容（字节）
        filename: 原始文件名
        
    Returns:
        str: 文件在 MinIO 中的对象名（路径）
        
    Raises:
        Exception: 上传失败时抛出异常
    """
    try:
        # 生成对象名：user_{user_id}/application_{application_id}/原始文件名
        object_name = f"user_{user_id}/application_{application_id}/{filename}"
        
        # 上传文件
        file_stream = io.BytesIO(file_bytes)
        file_size = len(file_bytes)
        
        minio_client.put_object(
            bucket_name=RESUME_BUCKET,
            object_name=object_name,
            data=file_stream,
            length=file_size,
        )
        
        logger.info(f"文件上传成功: {object_name}, 大小: {file_size} bytes")
        return object_name
        
    except S3Error as e:
        logger.error(f"上传文件到 MinIO 失败: {e}")
        raise Exception(f"文件上传失败: {str(e)}")


def download_resume_file(object_name: str) -> bytes:
    """
    从 MinIO 下载简历文件
    
    Args:
        object_name: 文件在 MinIO 中的对象名
        
    Returns:
        bytes: 文件内容
        
    Raises:
        Exception: 下载失败时抛出异常
    """
    try:
        response = minio_client.get_object(RESUME_BUCKET, object_name)
        file_bytes = response.read()
        response.close()
        response.release_conn()
        
        logger.info(f"文件下载成功: {object_name}, 大小: {len(file_bytes)} bytes")
        return file_bytes
        
    except S3Error as e:
        logger.error(f"从 MinIO 下载文件失败: {e}")
        raise Exception(f"文件下载失败: {str(e)}")


def get_presigned_url(object_name: str, expires: timedelta = timedelta(hours=1)) -> str:
    """
    生成预签名 URL（可选功能，用于直接访问文件）
    
    Args:
        object_name: 文件对象名
        expires: URL 过期时间，默认 1 小时
        
    Returns:
        str: 预签名 URL
    """
    try:
        url = minio_client.presigned_get_object(
            RESUME_BUCKET, object_name, expires=expires
        )
        logger.info(f"生成预签名 URL: {object_name}")
        return url
    except S3Error as e:
        logger.error(f"生成预签名 URL 失败: {e}")
        raise Exception(f"生成 URL 失败: {str(e)}")


def delete_resume_file(object_name: str) -> bool:
    """
    删除简历文件（可选功能）
    
    Args:
        object_name: 文件对象名
        
    Returns:
        bool: 是否删除成功
    """
    try:
        minio_client.remove_object(RESUME_BUCKET, object_name)
        logger.info(f"文件删除成功: {object_name}")
        return True
    except S3Error as e:
        logger.error(f"删除文件失败: {e}")
        return False


def list_user_resumes(user_id: int) -> list[str]:
    """
    列出用户的所有简历文件（可选功能）
    
    Args:
        user_id: 用户 ID
        
    Returns:
        list[str]: 文件对象名列表
    """
    try:
        prefix = f"user_{user_id}/"
        objects = minio_client.list_objects(RESUME_BUCKET, prefix=prefix, recursive=True)
        file_list = [obj.object_name for obj in objects]
        logger.info(f"列出用户 {user_id} 的文件: {len(file_list)} 个")
        return file_list
    except S3Error as e:
        logger.error(f"列出文件失败: {e}")
        return []
