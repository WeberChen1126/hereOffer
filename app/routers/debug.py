"""调试和测试路由"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
import io

from app.auth import get_current_user
from app.schemas import ApiResponse
from app.utils.file_extraction import extract_text
from app.services.file_storage import (
    upload_resume_file,
    download_resume_file,
    list_user_resumes,
)
from app.services.llm_service import parse_resume, score_resume, generate_interview_questions

router = APIRouter(prefix="/debug", tags=["Debug"])


class ExtractTextResponse(BaseModel):
    """文本提取响应"""
    text: str
    length: int
    file_type: str


@router.post("/extract_text")
async def extract_text_endpoint(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ExtractTextResponse]:
    """
    测试文件文本提取
    
    支持 PDF、DOCX、TXT 格式
    """
    try:
        # 读取文件内容
        file_bytes = await file.read()
        
        # 提取文本
        extracted_text = extract_text(file_type, file_bytes)
        
        return ApiResponse(
            code=0,
            message="success",
            data=ExtractTextResponse(
                text=extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""),
                length=len(extracted_text),
                file_type=file_type,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本提取失败: {str(e)}")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    object_name: str
    file_size: int
    filename: str


@router.post("/upload_file")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    application_id: int = Form(...),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[FileUploadResponse]:
    """
    测试文件上传到 MinIO
    """
    try:
        # 读取文件内容
        file_bytes = await file.read()
        file_size = len(file_bytes)
        
        # 上传到 MinIO
        object_name = upload_resume_file(
            user_id=current_user["user_id"],
            application_id=application_id,
            file_bytes=file_bytes,
            filename=file.filename or "resume.pdf",
        )
        
        return ApiResponse(
            code=0,
            message="success",
            data=FileUploadResponse(
                object_name=object_name,
                file_size=file_size,
                filename=file.filename or "resume.pdf",
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/download_file")
async def download_file_endpoint(
    object_name: str,
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """
    测试从 MinIO 下载文件
    """
    try:
        # 从 MinIO 下载
        file_bytes = download_resume_file(object_name)
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{object_name.split("/")[-1]}"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


class UserFilesResponse(BaseModel):
    """用户文件列表响应"""
    files: list[str]
    count: int


@router.get("/list_files")
async def list_files_endpoint(
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[UserFilesResponse]:
    """
    列出当前用户的所有文件
    """
    try:
        files = list_user_resumes(current_user["user_id"])
        
        return ApiResponse(
            code=0,
            message="success",
            data=UserFilesResponse(
                files=files,
                count=len(files),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")


class ParseResumeResponse(BaseModel):
    """简历解析响应"""
    parsed_data: Dict[str, Any]


@router.post("/parse_resume")
async def parse_resume_endpoint(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ParseResumeResponse]:
    """
    测试简历解析（提取文本 + LLM 结构化）
    """
    try:
        # 1. 读取文件并提取文本
        file_bytes = await file.read()
        resume_text = extract_text(file_type, file_bytes)
        
        # 2. 调用 LLM 解析简历
        parsed_data = parse_resume(resume_text)
        
        return ApiResponse(
            code=0,
            message="success",
            data=ParseResumeResponse(
                parsed_data=parsed_data,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历解析失败: {str(e)}")


class ScoreResumeRequest(BaseModel):
    """简历评分请求"""
    resume_data: Dict[str, Any]
    job_description: str


class ScoreResumeResponse(BaseModel):
    """简历评分响应"""
    score_data: Dict[str, Any]


@router.post("/score_resume")
async def score_resume_endpoint(
    request: ScoreResumeRequest,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ScoreResumeResponse]:
    """
    测试简历评分（基于结构化数据 + JD）
    """
    try:
        score_data = score_resume(request.resume_data, request.job_description)
        
        return ApiResponse(
            code=0,
            message="success",
            data=ScoreResumeResponse(
                score_data=score_data,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历评分失败: {str(e)}")


class GenerateQuestionsRequest(BaseModel):
    """生成面试题请求"""
    resume_data: Dict[str, Any]
    job_description: str
    num_questions: int = 5


class GenerateQuestionsResponse(BaseModel):
    """生成面试题响应"""
    questions_data: Dict[str, Any]


@router.post("/generate_questions")
async def generate_questions_endpoint(
    request: GenerateQuestionsRequest,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[GenerateQuestionsResponse]:
    """
    测试面试题目生成（基于简历 + JD）
    """
    try:
        questions_data = generate_interview_questions(
            resume_data=request.resume_data,
            job_description=request.job_description,
            num_questions=request.num_questions,
        )
        
        return ApiResponse(
            code=0,
            message="success",
            data=GenerateQuestionsResponse(
                questions_data=questions_data,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"面试题生成失败: {str(e)}")
