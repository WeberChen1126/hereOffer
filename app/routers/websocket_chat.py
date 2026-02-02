"""
实时对话 WebSocket 路由
支持文本和语音实时对话
"""
import logging
import json
import base64
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatSession, User
from app.services.chat_service import chat_service
from app.services.voice_service import voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    
    async def connect(self, session_id: int, websocket: WebSocket):
        """建立连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket 连接建立: session_id={session_id}")
    
    def disconnect(self, session_id: int):
        """断开连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket 连接断开: session_id={session_id}")
    
    async def send_message(self, session_id: int, message: dict):
        """发送消息"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(..., description="JWT Token"),
):
    """
    WebSocket 实时对话端点
    
    消息格式：
    
    客户端 -> 服务器（文本消息）:
    {
        "type": "text",
        "content": "你好，请问这个岗位的工作地点在哪里？"
    }
    
    客户端 -> 服务器（语音消息）:
    {
        "type": "voice",
        "audio": "base64编码的音频数据",
        "format": "pcm|wav|opus"
    }
    
    服务器 -> 客户端（文本响应）:
    {
        "type": "text",
        "content": "这个岗位的工作地点在北京海淀区。",
        "citations": [...]  // 可选的引用来源
    }
    
    服务器 -> 客户端（语音响应）:
    {
        "type": "voice",
        "text": "这个岗位的工作地点在北京海淀区。",
        "audio": "base64编码的音频数据",
        "citations": [...]
    }
    
    服务器 -> 客户端（错误）:
    {
        "type": "error",
        "message": "错误信息"
    }
    """
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 验证token并获取用户信息
        from app.auth import decode_token
        try:
            payload = decode_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # 验证会话所有权
        session = await chat_service.get_session(db, session_id, user_id)
        if not session:
            await websocket.close(code=4004, reason="Session not found or access denied")
            return
        
        # 建立连接
        await manager.connect(session_id, websocket)
        
        # 发送欢迎消息
        await manager.send_message(session_id, {
            "type": "system",
            "message": "连接成功！您可以开始提问了。"
        })
        
        # 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "text":
                # 处理文本消息
                await handle_text_message(db, session_id, session.job_id, data, websocket)
            
            # 语音功能暂时禁用
            # elif message_type == "voice":
            #     # 处理语音消息
            #     await handle_voice_message(db, session_id, session.job_id, data, websocket)
            
            elif message_type == "ping":
                # 心跳
                await manager.send_message(session_id, {"type": "pong"})
            
            else:
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": f"未知的消息类型: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket 客户端主动断开: session_id={session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        manager.disconnect(session_id)
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


async def handle_text_message(
    db: Session,
    session_id: int,
    job_id: Optional[int],
    data: dict,
    websocket: WebSocket
):
    """处理文本消息"""
    try:
        user_message = data.get("content", "").strip()
        if not user_message:
            await manager.send_message(session_id, {
                "type": "error",
                "message": "消息内容不能为空"
            })
            return
        
        # 保存用户消息
        await chat_service.add_message(
            db,
            session_id=session_id,
            role="user",
            content=user_message,
            message_type="text"
        )
        
        # 发送"正在输入"状态
        await manager.send_message(session_id, {
            "type": "typing",
            "message": "AI 正在思考..."
        })
        
        # 处理消息并生成回复
        response_text, citations = await chat_service.process_user_message(
            db, session_id, user_message, job_id
        )
        
        # 保存AI回复
        await chat_service.add_message(
            db,
            session_id=session_id,
            role="assistant",
            content=response_text,
            message_type="text",
            citations=citations
        )
        
        # 发送回复
        await manager.send_message(session_id, {
            "type": "text",
            "content": response_text,
            "citations": citations
        })
        
    except Exception as e:
        logger.error(f"处理文本消息失败: {e}", exc_info=True)
        await manager.send_message(session_id, {
            "type": "error",
            "message": "处理消息时出错，请稍后再试"
        })


# 语音功能暂时禁用
"""
async def handle_voice_message(
    db: Session,
    session_id: int,
    job_id: Optional[int],
    data: dict,
    websocket: WebSocket
):
    处理语音消息（已禁用）
    pass
"""
