"""异步任务定义 - 简历处理链路"""
import logging
from rq import get_current_job
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Application, TaskRun
from app.constants import ApplicationStatus, TaskStatus
from app.services.llm_service import parse_resume, score_resume, generate_interview_questions
from app.utils.file_extraction import extract_text
from app.services.file_storage import download_resume_file
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # 不要在这里关闭，由任务函数处理


def record_task_run(db: Session, application_id: int, task_name: str, status: str, result: dict = None, error: str = None):
    """记录任务执行"""
    import hashlib
    import json
    
    # 生成输入哈希（用于幂等性检查）
    input_data = f"{task_name}_{application_id}"
    input_hash = hashlib.md5(input_data.encode()).hexdigest()
    
    task_run = TaskRun(
        application_id=application_id,
        task_name=task_name,
        input_hash=input_hash,
        status=status,
        last_error=error,
    )
    db.add(task_run)
    db.commit()
    return task_run


def parse_application_task(application_id: int) -> dict:
    """
    异步任务：解析简历
    
    流程：
    1. 检查幂等性（已解析则跳过）
    2. 从 MinIO 下载简历文件
    3. 提取文本
    4. 调用 LLM 解析结构化数据
    5. 更新状态为 PARSED
    6. 触发评分任务
    
    重试机制：最多 3 次，指数退避
    失败处理：进入 HUMAN_REVIEW 状态
    """
    db = SessionLocal()
    job = get_current_job()
    
    try:
        logger.info(f"开始解析任务: application_id={application_id}, job_id={job.id if job else 'local'}")
        
        # 1. 获取投递记录
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise ValueError(f"投递记录不存在: {application_id}")
        
        # 2. 幂等性检查：已解析则跳过
        if application.status not in [ApplicationStatus.PARSING.value]:
            logger.info(f"投递已解析，跳过: application_id={application_id}, status={application.status}")
            return {"status": "skipped", "reason": "already_parsed"}
        
        # 3. 检查是否已有结果（幂等）
        if application.resume_json:
            logger.info(f"简历已解析，直接进入评分: application_id={application_id}")
            application.status = ApplicationStatus.PARSED.value
            db.commit()
            
            # 触发评分任务
            from app.task_queue import enqueue_task
            enqueue_task("score_application_task", application_id)
            
            return {"status": "success", "reason": "already_parsed", "resume_json": application.resume_json}
        
        # 4. 提取文本（如果还没有）
        if not application.resume_text:
            if not application.resume_path:
                raise ValueError(f"简历文件路径为空: application_id={application_id}")
            
            # 从 MinIO 下载文件
            file_bytes = download_resume_file(application.resume_path)
            
            # 提取文本
            file_ext = application.resume_path.split(".")[-1].lower()
            resume_text = extract_text(file_ext, file_bytes)
            
            application.resume_text = resume_text
            db.commit()
            logger.info(f"文本提取完成: application_id={application_id}, length={len(resume_text)}")
        
        # 5. 调用 LLM 解析
        resume_json = parse_resume(application.resume_text)
        
        # 6. 保存结果并更新状态
        application.resume_json = resume_json
        application.status = ApplicationStatus.PARSED.value
        db.commit()
        
        # 7. 记录任务成功
        record_task_run(db, application_id, "parse_application_task", TaskStatus.SUCCESS.value, 
                       result={"parsed": True})
        
        logger.info(f"解析任务完成: application_id={application_id}")
        
        # 8. 触发评分任务
        from app.task_queue import enqueue_task
        enqueue_task("score_application_task", application_id)
        
        return {"status": "success", "application_id": application_id, "resume_json": resume_json}
        
    except Exception as e:
        logger.error(f"解析任务失败: application_id={application_id}, error={e}", exc_info=True)
        
        try:
            # 更新状态为人工审核
            application = db.query(Application).filter(Application.id == application_id).first()
            if application:
                application.status = ApplicationStatus.HUMAN_REVIEW.value
                application.error_detail = str(e)
                db.commit()
            
            # 记录任务失败
            record_task_run(db, application_id, "parse_application_task", TaskStatus.FAILED.value,
                           error=str(e))
        except Exception as record_error:
            logger.error(f"记录失败信息出错: {record_error}")
        
        raise
        
    finally:
        db.close()


def score_application_task(application_id: int) -> dict:
    """
    异步任务：评分简历
    
    流程：
    1. 检查幂等性（已评分则跳过）
    2. 获取简历结构化数据和 JD
    3. 调用 LLM 评分
    4. 保存评分结果
    5. 更新状态为 SCORED
    6. 判断是否达标，达标则触发题包生成
    """
    db = SessionLocal()
    job = get_current_job()
    
    try:
        logger.info(f"开始评分任务: application_id={application_id}, job_id={job.id if job else 'local'}")
        
        # 1. 获取投递记录
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise ValueError(f"投递记录不存在: {application_id}")
        
        # 2. 幂等性检查
        if application.status not in [ApplicationStatus.PARSED.value, ApplicationStatus.SCORING.value]:
            logger.info(f"投递状态不符，跳过评分: application_id={application_id}, status={application.status}")
            return {"status": "skipped", "reason": f"invalid_status: {application.status}"}
        
        if application.score_json:
            logger.info(f"简历已评分，跳过: application_id={application_id}")
            
            # 检查是否需要生成题包
            score_total = application.score_json.get("overall_score", 0)
            threshold = 60  # 默认阈值
            
            if score_total >= threshold and application.status != ApplicationStatus.QUESTIONS_READY.value:
                from app.task_queue import enqueue_task
                enqueue_task("generate_questions_task", application_id)
            
            return {"status": "success", "reason": "already_scored", "score_json": application.score_json}
        
        # 3. 检查必要数据
        if not application.resume_json:
            raise ValueError(f"简历未解析: application_id={application_id}")
        
        if not application.job_description:
            raise ValueError(f"职位描述为空: application_id={application_id}")
        
        # 4. 更新状态为评分中
        application.status = ApplicationStatus.SCORING.value
        db.commit()
        
        # 5. 调用 LLM 评分
        score_json = score_resume(application.resume_json, application.job_description)
        
        # 6. 保存结果并更新状态
        application.score_json = score_json
        application.status = ApplicationStatus.SCORED.value
        db.commit()
        
        # 7. 记录任务成功
        record_task_run(db, application_id, "score_application_task", TaskStatus.SUCCESS.value,
                       result={"score_total": score_json.get("overall_score")})
        
        logger.info(f"评分任务完成: application_id={application_id}, score={score_json.get('overall_score')}")
        
        # 8. 判断是否达标
        score_total = score_json.get("overall_score", 0)
        threshold = 60  # 默认阈值，可以从 job 配置读取
        
        if score_total >= threshold:
            logger.info(f"达标，触发题包生成: application_id={application_id}, score={score_total}")
            from app.task_queue import enqueue_task
            enqueue_task("generate_questions_task", application_id)
        else:
            logger.info(f"未达标，不生成题包: application_id={application_id}, score={score_total}")
        
        return {"status": "success", "application_id": application_id, "score_json": score_json}
        
    except Exception as e:
        logger.error(f"评分任务失败: application_id={application_id}, error={e}", exc_info=True)
        
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if application:
                application.status = ApplicationStatus.HUMAN_REVIEW.value
                application.error_detail = str(e)
                db.commit()
            
            record_task_run(db, application_id, "score_application_task", TaskStatus.FAILED.value,
                           error=str(e))
        except Exception as record_error:
            logger.error(f"记录失败信息出错: {record_error}")
        
        raise
        
    finally:
        db.close()


def generate_questions_task(application_id: int) -> dict:
    """
    异步任务：生成面试题包
    
    流程：
    1. 检查幂等性（已生成则跳过）
    2. 检查评分是否达标
    3. 获取简历和 JD
    4. 调用 LLM 生成题包
    5. 保存题包
    6. 更新状态为 QUESTIONS_READY
    """
    db = SessionLocal()
    job = get_current_job()
    
    try:
        logger.info(f"开始生成题包: application_id={application_id}, job_id={job.id if job else 'local'}")
        
        # 1. 获取投递记录
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise ValueError(f"投递记录不存在: {application_id}")
        
        # 2. 幂等性检查
        if application.status == ApplicationStatus.QUESTIONS_READY.value:
            logger.info(f"题包已生成，跳过: application_id={application_id}")
            return {"status": "success", "reason": "already_generated", "questions_json": application.questions_json}
        
        if application.questions_json:
            logger.info(f"题包已存在，更新状态: application_id={application_id}")
            application.status = ApplicationStatus.QUESTIONS_READY.value
            db.commit()
            return {"status": "success", "reason": "already_generated", "questions_json": application.questions_json}
        
        # 3. 检查状态和分数
        if application.status != ApplicationStatus.SCORED.value:
            raise ValueError(f"投递状态不符: {application.status}")
        
        if not application.score_json:
            raise ValueError(f"评分数据不存在: application_id={application_id}")
        
        score_total = application.score_json.get("overall_score", 0)
        threshold = 60
        
        if score_total < threshold:
            logger.info(f"分数未达标，不生成题包: application_id={application_id}, score={score_total}")
            return {"status": "skipped", "reason": f"score_below_threshold: {score_total} < {threshold}"}
        
        # 4. 检查必要数据
        if not application.resume_json:
            raise ValueError(f"简历未解析: application_id={application_id}")
        
        if not application.job_description:
            raise ValueError(f"职位描述为空: application_id={application_id}")
        
        # 5. 调用 LLM 生成题包
        questions_json = generate_interview_questions(
            resume_data=application.resume_json,
            job_description=application.job_description,
            num_questions=5,
        )
        
        # 6. 保存结果并更新状态
        application.questions_json = questions_json
        application.status = ApplicationStatus.QUESTIONS_READY.value
        db.commit()
        
        # 7. 记录任务成功
        record_task_run(db, application_id, "generate_questions_task", TaskStatus.SUCCESS.value,
                       result={"num_questions": len(questions_json.get("questions", []))})
        
        logger.info(f"题包生成完成: application_id={application_id}, num={len(questions_json.get('questions', []))}")
        
        return {"status": "success", "application_id": application_id, "questions_json": questions_json}
        
    except Exception as e:
        logger.error(f"题包生成失败: application_id={application_id}, error={e}", exc_info=True)
        
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if application:
                application.error_detail = str(e)
                db.commit()
            
            record_task_run(db, application_id, "generate_questions_task", TaskStatus.FAILED.value,
                           error=str(e))
        except Exception as record_error:
            logger.error(f"记录失败信息出错: {record_error}")
        
        raise
        
    finally:
        db.close()
