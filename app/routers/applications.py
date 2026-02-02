"""投递管理路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import Application, User, Job
from app.auth import get_current_user
from app.schemas import ApiResponse
from app.constants import ApplicationStatus, FileType
from app.utils.file_extraction import extract_text
from app.services.file_storage import upload_resume_file
from app.services.llm_service import parse_resume, score_resume
from app.services.state_machine import transition_status
from app.task_queue import enqueue_task
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])


class CreateApplicationRequest(BaseModel):
    """创建投递请求"""
    job_title: str
    job_description: str


class ApplicationResponse(BaseModel):
    """投递响应"""
    id: int
    user_id: int
    job_title: str
    status: str
    resume_text: Optional[str] = None
    resume_json: Optional[dict] = None
    score_json: Optional[dict] = None
    questions_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    """投递列表响应"""
    applications: List[ApplicationResponse]
    total: int


@router.post("")
async def create_application(
    file: UploadFile = File(...),
    job_id: Optional[int] = Form(None),
    job_title: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ApplicationResponse]:
    """
    创建投递记录并上传简历
    
    两种方式：
    1. 指定 job_id：从岗位表获取信息
    2. 自定义：提供 job_title 和 job_description
    
    流程：
    1. 创建投递记录（状态: PARSING）
    2. 上传简历文件到 MinIO
    3. 触发异步解析任务
    """
    try:
        user_id = current_user["user_id"]
        
        # 方式1：从岗位表获取
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="岗位不存在")
            if not job.is_active:
                raise HTTPException(status_code=400, detail="该岗位已关闭")
            
            final_job_title = job.title
            final_job_description = job.description
        # 方式2：自定义
        elif job_title and job_description:
            final_job_title = job_title
            final_job_description = job_description
            job_id = None
        else:
            raise HTTPException(
                status_code=400,
                detail="必须提供 job_id 或者 (job_title + job_description)"
            )
        
        # 1. 创建投递记录
        application = Application(
            user_id=user_id,
            job_id=job_id,
            job_title=final_job_title,
            job_description=final_job_description,
            status=ApplicationStatus.PARSING.value,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        
        logger.info(f"创建投递记录: application_id={application.id}, user_id={user_id}, job_id={job_id}")
        
        # 2. 上传文件到 MinIO
        file_bytes = await file.read()
        filename = file.filename or "resume.pdf"
        
        # 判断文件类型
        file_ext = filename.split(".")[-1].lower()
        if file_ext not in ["pdf", "docx", "txt"]:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        object_name = upload_resume_file(
            user_id=user_id,
            application_id=application.id,
            file_bytes=file_bytes,
            filename=filename,
        )
        
        # 3. 更新简历路径
        application.resume_path = object_name
        db.commit()
        db.refresh(application)
        
        logger.info(f"简历上传完成: application_id={application.id}, path={object_name}")
        
        # 4. 触发异步解析任务
        job = enqueue_task("parse_application_task", application.id)
        logger.info(f"解析任务已入队: application_id={application.id}, job_id={job.id}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=ApplicationResponse(
                id=application.id,
                user_id=application.user_id,
                job_title=application.job_title,
                status=application.status,
                resume_text=application.resume_text[:500] if application.resume_text else None,
                resume_json=application.resume_json,
                score_json=application.score_json,
                questions_json=application.questions_json,
                created_at=application.created_at,
                updated_at=application.updated_at,
            ),
        )
        
    except Exception as e:
        logger.error(f"创建投递失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建投递失败: {str(e)}")


@router.get("/{application_id}")
async def get_application(
    application_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ApplicationResponse]:
    """获取投递详情"""
    user_id = current_user["user_id"]
    
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == user_id,
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    
    return ApiResponse(
        code=0,
        message="success",
        data=ApplicationResponse(
            id=application.id,
            user_id=application.user_id,
            job_title=application.job_title,
            status=application.status,
            resume_text=application.resume_text[:500] if application.resume_text else None,
            resume_json=application.resume_json,
            score_json=application.score_json,
            questions_json=application.questions_json,
            created_at=application.created_at,
            updated_at=application.updated_at,
        ),
    )


@router.get("")
async def list_applications(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ApplicationListResponse]:
    """获取投递列表"""
    user_id = current_user["user_id"]
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(Application).filter(Application.user_id == user_id).count()
    
    return ApiResponse(
        code=0,
        message="success",
        data=ApplicationListResponse(
            applications=[
                ApplicationResponse(
                    id=app.id,
                    user_id=app.user_id,
                    job_title=app.job_title,
                    status=app.status,
                    resume_text=app.resume_text[:200] if app.resume_text else None,
                    resume_json=app.resume_json,
                    score_json=app.score_json,
                    questions_json=app.questions_json,
                    created_at=app.created_at,
                    updated_at=app.updated_at,
                )
                for app in applications
            ],
            total=total,
        ),
    )


class UpdateStatusRequest(BaseModel):
    """更新状态请求"""
    new_status: str


@router.post("/{application_id}/status")
async def update_application_status(
    application_id: int,
    request: UpdateStatusRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ApplicationResponse]:
    """
    更新投递状态
    
    使用状态机验证状态转移是否合法
    """
    user_id = current_user["user_id"]
    
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == user_id,
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    
    try:
        # 使用状态机进行状态转移
        new_status = transition_status(application.status, request.new_status)
        application.status = new_status
        db.commit()
        db.refresh(application)
        
        logger.info(f"状态更新成功: application_id={application_id}, {application.status} -> {new_status}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=ApplicationResponse(
                id=application.id,
                user_id=application.user_id,
                job_title=application.job_title,
                status=application.status,
                resume_text=application.resume_text[:500] if application.resume_text else None,
                resume_json=application.resume_json,
                score_json=application.score_json,
                questions_json=application.questions_json,
                created_at=application.created_at,
                updated_at=application.updated_at,
            ),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"状态更新失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"状态更新失败: {str(e)}")
