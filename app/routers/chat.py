"""
聊天对话 HTTP API 路由
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.schemas import ApiResponse
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    job_id: Optional[int] = None
    session_type: str = "text"  # text or voice


class SessionResponse(BaseModel):
    """会话响应"""
    id: int
    user_id: int
    job_id: Optional[int]
    session_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    session_id: int
    role: str
    content: str
    message_type: str
    audio_url: Optional[str]
    audio_duration: Optional[float]
    citations: Optional[List[dict]]
    created_at: datetime


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str


@router.post("/sessions")
async def create_chat_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[SessionResponse]:
    """
    创建聊天会话
    
    支持创建文本或语音对话会话
    """
    try:
        session = await chat_service.create_session(
            db,
            user_id=current_user["user_id"],
            job_id=request.job_id,
            session_type=request.session_type
        )
        
        return ApiResponse(
            code=0,
            message="success",
            data=SessionResponse(
                id=session.id,
                user_id=session.user_id,
                job_id=session.job_id,
                session_type=session.session_type,
                is_active=session.is_active,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        )
    
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/sessions")
async def list_chat_sessions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[SessionResponse]]:
    """获取用户的所有聊天会话"""
    try:
        sessions = await chat_service.get_user_sessions(
            db,
            user_id=current_user["user_id"]
        )
        
        return ApiResponse(
            code=0,
            message="success",
            data=[
                SessionResponse(
                    id=s.id,
                    user_id=s.user_id,
                    job_id=s.job_id,
                    session_type=s.session_type,
                    is_active=s.is_active,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in sessions
            ]
        )
    
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[SessionResponse]:
    """获取会话详情"""
    try:
        session = await chat_service.get_session(
            db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return ApiResponse(
            code=0,
            message="success",
            data=SessionResponse(
                id=session.id,
                user_id=session.user_id,
                job_id=session.job_id,
                session_type=session.session_type,
                is_active=session.is_active,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[MessageResponse]]:
    """获取会话的所有消息"""
    try:
        # 验证会话所有权
        session = await chat_service.get_session(
            db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取消息
        messages = await chat_service.get_session_messages(db, session_id)
        
        return ApiResponse(
            code=0,
            message="success",
            data=[
                MessageResponse(
                    id=m.id,
                    session_id=m.session_id,
                    role=m.role,
                    content=m.content,
                    message_type=m.message_type,
                    audio_url=m.audio_url,
                    audio_duration=m.audio_duration,
                    citations=m.citations_json,
                    created_at=m.created_at,
                )
                for m in messages
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取消息列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取消息列表失败: {str(e)}")


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageResponse]:
    """
    发送文本消息（HTTP接口）
    
    注意：实时对话请使用 WebSocket（/ws/chat/{session_id}）
    """
    try:
        # 验证会话所有权
        session = await chat_service.get_session(
            db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 保存用户消息
        user_msg = await chat_service.add_message(
            db,
            session_id=session_id,
            role="user",
            content=request.content,
            message_type="text"
        )
        
        # 处理消息并生成回复
        response_text, citations = await chat_service.process_user_message(
            db, session_id, request.content, session.job_id
        )
        
        # 保存AI回复
        ai_msg = await chat_service.add_message(
            db,
            session_id=session_id,
            role="assistant",
            content=response_text,
            message_type="text",
            citations=citations
        )
        
        return ApiResponse(
            code=0,
            message="success",
            data=MessageResponse(
                id=ai_msg.id,
                session_id=ai_msg.session_id,
                role=ai_msg.role,
                content=ai_msg.content,
                message_type=ai_msg.message_type,
                audio_url=ai_msg.audio_url,
                audio_duration=ai_msg.audio_duration,
                citations=ai_msg.citations_json,
                created_at=ai_msg.created_at,
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")
