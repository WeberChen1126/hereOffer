"""岗位管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import Job, User
from app.auth import get_current_user
from app.schemas import ApiResponse
from app.constants import UserType
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/jobs", tags=["Admin - Jobs"])


class CreateJobRequest(BaseModel):
    """创建岗位请求"""
    title: str
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    threshold_score: int = 60
    is_active: bool = True


class UpdateJobRequest(BaseModel):
    """更新岗位请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    threshold_score: Optional[int] = None
    is_active: Optional[bool] = None


class QuestionBankRequest(BaseModel):
    """题库请求"""
    version: int
    questions: List[dict]


class JobResponse(BaseModel):
    """岗位响应"""
    id: int
    title: str
    description: str
    requirements: Optional[str]
    responsibilities: Optional[str]
    department: Optional[str]
    location: Optional[str]
    salary_range: Optional[str]
    threshold_score: int
    question_bank_json: Optional[dict]
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    """岗位列表响应"""
    jobs: List[JobResponse]
    total: int


def check_admin(current_user: dict):
    """检查是否为管理员"""
    if current_user.get("user_type") != UserType.ADMIN.value:
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.post("")
async def create_job(
    request: CreateJobRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[JobResponse]:
    """创建岗位（仅管理员）"""
    check_admin(current_user)
    
    try:
        job = Job(
            title=request.title,
            description=request.description,
            requirements=request.requirements,
            responsibilities=request.responsibilities,
            department=request.department,
            location=request.location,
            salary_range=request.salary_range,
            threshold_score=request.threshold_score,
            is_active=request.is_active,
            created_by=current_user["user_id"],
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"创建岗位成功: job_id={job.id}, title={job.title}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=JobResponse(
                id=job.id,
                title=job.title,
                description=job.description,
                requirements=job.requirements,
                responsibilities=job.responsibilities,
                department=job.department,
                location=job.location,
                salary_range=job.salary_range,
                threshold_score=job.threshold_score,
                question_bank_json=job.question_bank_json,
                is_active=job.is_active,
                created_by=job.created_by,
                created_at=job.created_at,
                updated_at=job.updated_at,
            ),
        )
    except Exception as e:
        logger.error(f"创建岗位失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建岗位失败: {str(e)}")


@router.put("/{job_id}")
async def update_job(
    job_id: int,
    request: UpdateJobRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[JobResponse]:
    """更新岗位（仅管理员）"""
    check_admin(current_user)
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    try:
        # 更新字段
        if request.title is not None:
            job.title = request.title
        if request.description is not None:
            job.description = request.description
        if request.requirements is not None:
            job.requirements = request.requirements
        if request.responsibilities is not None:
            job.responsibilities = request.responsibilities
        if request.department is not None:
            job.department = request.department
        if request.location is not None:
            job.location = request.location
        if request.salary_range is not None:
            job.salary_range = request.salary_range
        if request.threshold_score is not None:
            job.threshold_score = request.threshold_score
        if request.is_active is not None:
            job.is_active = request.is_active
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"更新岗位成功: job_id={job_id}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=JobResponse(
                id=job.id,
                title=job.title,
                description=job.description,
                requirements=job.requirements,
                responsibilities=job.responsibilities,
                department=job.department,
                location=job.location,
                salary_range=job.salary_range,
                threshold_score=job.threshold_score,
                question_bank_json=job.question_bank_json,
                is_active=job.is_active,
                created_by=job.created_by,
                created_at=job.created_at,
                updated_at=job.updated_at,
            ),
        )
    except Exception as e:
        logger.error(f"更新岗位失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新岗位失败: {str(e)}")


@router.put("/{job_id}/question_bank")
async def update_question_bank(
    job_id: int,
    request: QuestionBankRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """更新岗位题库（仅管理员，至少20道题）"""
    check_admin(current_user)
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    # 验证题目数量
    if len(request.questions) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"题库至少需要20道题，当前只有 {len(request.questions)} 道"
        )
    
    try:
        # 保存题库
        job.question_bank_json = {
            "version": request.version,
            "questions": request.questions,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        db.commit()
        
        logger.info(f"更新题库成功: job_id={job_id}, count={len(request.questions)}")
        
        return ApiResponse(
            code=0,
            message="success",
            data={
                "job_id": job_id,
                "version": request.version,
                "question_count": len(request.questions),
            },
        )
    except Exception as e:
        logger.error(f"更新题库失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新题库失败: {str(e)}")


@router.get("")
async def list_jobs(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[JobListResponse]:
    """获取岗位列表（管理员可查看全部，候选人只能看开放的）"""
    
    query = db.query(Job)
    
    # 候选人只能看开放的岗位
    if current_user.get("user_type") != UserType.ADMIN.value:
        query = query.filter(Job.is_active == True)
    elif is_active is not None:
        query = query.filter(Job.is_active == is_active)
    
    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    return ApiResponse(
        code=0,
        message="success",
        data=JobListResponse(
            jobs=[
                JobResponse(
                    id=job.id,
                    title=job.title,
                    description=job.description,
                    requirements=job.requirements,
                    responsibilities=job.responsibilities,
                    department=job.department,
                    location=job.location,
                    salary_range=job.salary_range,
                    threshold_score=job.threshold_score,
                    question_bank_json=job.question_bank_json,
                    is_active=job.is_active,
                    created_by=job.created_by,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                )
                for job in jobs
            ],
            total=total,
        ),
    )


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[JobResponse]:
    """获取岗位详情"""
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    # 候选人只能看开放的岗位
    if current_user.get("user_type") != UserType.ADMIN.value and not job.is_active:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    return ApiResponse(
        code=0,
        message="success",
        data=JobResponse(
            id=job.id,
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            department=job.department,
            location=job.location,
            salary_range=job.salary_range,
            threshold_score=job.threshold_score,
            question_bank_json=job.question_bank_json,
            is_active=job.is_active,
            created_by=job.created_by,
            created_at=job.created_at,
            updated_at=job.updated_at,
        ),
    )
