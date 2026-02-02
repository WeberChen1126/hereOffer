"""Admin 投递管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import io

from app.database import get_db
from app.models import Application, User, Job
from app.auth import get_current_user
from app.schemas import ApiResponse
from app.constants import UserType, ApplicationStatus
from app.services.file_storage import download_resume_file
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/applications", tags=["Admin - Applications"])


def check_admin(current_user: dict):
    """检查是否为管理员"""
    if current_user.get("user_type") != UserType.ADMIN.value:
        raise HTTPException(status_code=403, detail="需要管理员权限")


class ApplicationDetailResponse(BaseModel):
    """投递详情响应（Admin 视图）"""
    id: int
    user_id: int
    job_id: Optional[int]
    job_title: str
    job_description: Optional[str]
    resume_path: Optional[str]
    resume_text: Optional[str]
    resume_json: Optional[dict]
    score_json: Optional[dict]
    questions_json: Optional[dict]
    status: str
    error_detail: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # 候选人信息
    candidate_email: Optional[str] = None
    
    # 岗位信息
    job_info: Optional[dict] = None


class ApplicationListItemResponse(BaseModel):
    """投递列表项响应"""
    id: int
    user_id: int
    job_id: Optional[int]
    job_title: str
    status: str
    score_total: Optional[int] = None
    questions_json: Optional[dict] = None  # 添加题包字段
    created_at: datetime
    updated_at: datetime
    
    # 候选人信息
    candidate_email: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """投递列表响应"""
    applications: List[ApplicationListItemResponse]
    total: int
    page: int
    page_size: int


@router.get("")
async def list_applications(
    job_id: Optional[int] = Query(None, description="岗位ID"),
    status: Optional[str] = Query(None, description="状态"),
    score_min: Optional[int] = Query(None, description="最低分数"),
    score_max: Optional[int] = Query(None, description="最高分数"),
    user_id: Optional[int] = Query(None, description="候选人ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ApplicationListResponse]:
    """
    获取投递列表（管理员）
    
    支持筛选：
    - job_id: 岗位筛选
    - status: 状态筛选（PARSING/PARSED/SCORING/SCORED/QUESTIONS_READY/HUMAN_REVIEW等）
    - score_min/score_max: 分数范围
    - user_id: 候选人筛选
    """
    check_admin(current_user)
    
    try:
        # 构建查询
        query = db.query(Application)
        
        # 筛选条件
        if job_id is not None:
            query = query.filter(Application.job_id == job_id)
        
        if status is not None:
            query = query.filter(Application.status == status)
        
        if user_id is not None:
            query = query.filter(Application.user_id == user_id)
        
        # 分数筛选（需要 JSON 查询）
        if score_min is not None or score_max is not None:
            # 只筛选已评分的
            query = query.filter(Application.score_json.isnot(None))
            
            # SQLAlchemy JSON 查询
            if score_min is not None:
                query = query.filter(
                    Application.score_json['overall_score'].astext.cast(db.bind.dialect.NUMERIC) >= score_min
                )
            if score_max is not None:
                query = query.filter(
                    Application.score_json['overall_score'].astext.cast(db.bind.dialect.NUMERIC) <= score_max
                )
        
        # 总数
        total = query.count()
        
        # 分页
        skip = (page - 1) * page_size
        applications = query.order_by(Application.created_at.desc()).offset(skip).limit(page_size).all()
        
        # 获取候选人信息
        user_ids = [app.user_id for app in applications]
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        user_map = {user.id: user for user in users}
        
        # 构建响应
        items = []
        for app in applications:
            user = user_map.get(app.user_id)
            
            # 提取总分
            score_total = None
            if app.score_json:
                score_total = app.score_json.get("overall_score")
            
            items.append(ApplicationListItemResponse(
                id=app.id,
                user_id=app.user_id,
                job_id=app.job_id,
                job_title=app.job_title,
                status=app.status,
                score_total=score_total,
                questions_json=app.questions_json,  # 添加题包数据
                created_at=app.created_at,
                updated_at=app.updated_at,
                candidate_email=user.email if user else None,
            ))
        
        logger.info(f"Admin 查询投递列表: total={total}, page={page}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=ApplicationListResponse(
                applications=items,
                total=total,
                page=page,
                page_size=page_size,
            ),
        )
        
    except Exception as e:
        logger.error(f"查询投递列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{application_id}")
async def get_application_detail(
    application_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ApplicationDetailResponse]:
    """
    获取投递详情（管理员）
    
    包含：
    - 完整简历数据
    - 评分详情
    - 面试题包
    - 候选人信息
    - 岗位信息
    """
    check_admin(current_user)
    
    try:
        # 获取投递
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="投递记录不存在")
        
        # 获取候选人信息
        user = db.query(User).filter(User.id == application.user_id).first()
        
        # 获取岗位信息
        job_info = None
        if application.job_id:
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if job:
                job_info = {
                    "id": job.id,
                    "title": job.title,
                    "department": job.department,
                    "location": job.location,
                    "threshold_score": job.threshold_score,
                }
        
        logger.info(f"Admin 查询投递详情: application_id={application_id}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=ApplicationDetailResponse(
                id=application.id,
                user_id=application.user_id,
                job_id=application.job_id,
                job_title=application.job_title,
                job_description=application.job_description,
                resume_path=application.resume_path,
                resume_text=application.resume_text[:1000] if application.resume_text else None,  # 只返回前1000字
                resume_json=application.resume_json,
                score_json=application.score_json,
                questions_json=application.questions_json,
                status=application.status,
                error_detail=application.error_detail,
                created_at=application.created_at,
                updated_at=application.updated_at,
                candidate_email=user.email if user else None,
                job_info=job_info,
            ),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询投递详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


class UpdateStatusRequest(BaseModel):
    """更新状态请求"""
    new_status: str
    note: Optional[str] = None


@router.post("/{application_id}/status")
async def update_application_status(
    application_id: int,
    request: UpdateStatusRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """
    更新投递状态（管理员）
    
    允许管理员手动更改状态，例如：
    - HUMAN_REVIEW -> PARSING（重新处理）
    - 任意状态 -> REJECTED/NEXT_ROUND
    """
    check_admin(current_user)
    
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="投递记录不存在")
        
        old_status = application.status
        
        # 验证状态值
        try:
            ApplicationStatus(request.new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {request.new_status}")
        
        # 更新状态
        application.status = request.new_status
        
        # 如果有备注，追加到 error_detail
        if request.note:
            if application.error_detail:
                application.error_detail += f"\n[Admin操作] {request.note}"
            else:
                application.error_detail = f"[Admin操作] {request.note}"
        
        db.commit()
        
        logger.info(f"Admin 更新投递状态: application_id={application_id}, {old_status} -> {request.new_status}")
        
        return ApiResponse(
            code=0,
            message="success",
            data={
                "application_id": application_id,
                "old_status": old_status,
                "new_status": request.new_status,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新状态失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/stats/summary")
async def get_application_stats(
    job_id: Optional[int] = Query(None, description="岗位ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """
    获取投递统计信息（管理员）
    
    返回：
    - 总投递数
    - 各状态数量
    - 平均分数
    - 达标率
    """
    check_admin(current_user)
    
    try:
        # 构建基础查询
        base_query = db.query(Application)
        if job_id is not None:
            base_query = base_query.filter(Application.job_id == job_id)
        
        # 总数
        total = base_query.count()
        
        # 各状态统计
        status_stats = {}
        for status in ApplicationStatus:
            count = base_query.filter(Application.status == status.value).count()
            status_stats[status.value] = count
        
        # 已评分的数量和平均分
        scored_apps = base_query.filter(Application.score_json.isnot(None)).all()
        scored_count = len(scored_apps)
        
        avg_score = None
        pass_count = 0
        if scored_apps:
            scores = [app.score_json.get("overall_score", 0) for app in scored_apps if app.score_json]
            avg_score = sum(scores) / len(scores) if scores else None
            
            # 达标数（假设阈值60）
            pass_count = sum(1 for score in scores if score >= 60)
        
        pass_rate = (pass_count / scored_count * 100) if scored_count > 0 else None
        
        logger.info(f"Admin 查询统计: job_id={job_id}, total={total}")
        
        return ApiResponse(
            code=0,
            message="success",
            data={
                "total": total,
                "status_stats": status_stats,
                "scored_count": scored_count,
                "avg_score": round(avg_score, 2) if avg_score else None,
                "pass_count": pass_count,
                "pass_rate": round(pass_rate, 2) if pass_rate else None,
            },
        )
        
    except Exception as e:
        logger.error(f"查询统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{application_id}/resume")
async def download_application_resume(
    application_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    下载投递的简历文件（管理员）
    
    返回简历文件的二进制流，浏览器会自动下载。
    """
    check_admin(current_user)
    
    try:
        # 查询投递记录
        application = db.query(Application).filter(Application.id == application_id).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="投递记录不存在")
        
        if not application.resume_path:
            raise HTTPException(status_code=404, detail="该投递没有上传简历文件")
        
        # 从 MinIO 下载文件
        try:
            file_bytes = download_resume_file(application.resume_path)
        except Exception as e:
            logger.error(f"从 MinIO 下载文件失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="下载文件失败")
        
        # 获取原始文件名
        filename = application.resume_path.split('/')[-1] if '/' in application.resume_path else application.resume_path
        
        # 对文件名进行 URL 编码（处理中文文件名）
        from urllib.parse import quote
        encoded_filename = quote(filename.encode('utf-8'))
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载简历失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

