"""
对话服务模块
管理聊天会话和消息
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import ChatSession, ChatMessage, Job
from app.services.llm_service import llm_service
from app.services.voice_service import voice_service
from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务类"""
    
    async def create_session(
        self,
        db: Session,
        user_id: int,
        job_id: Optional[int] = None,
        session_type: str = "text"
    ) -> ChatSession:
        """
        创建聊天会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            job_id: 岗位ID（可选）
            session_type: 会话类型（text/voice）
        
        Returns:
            创建的会话
        """
        session = ChatSession(
            user_id=user_id,
            job_id=job_id,
            session_type=session_type,
            is_active=True,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"创建聊天会话: session_id={session.id}, user_id={user_id}, type={session_type}")
        return session
    
    async def get_session(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[ChatSession]:
        """获取会话（验证所有权）"""
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        return session
    
    async def get_user_sessions(
        self,
        db: Session,
        user_id: int,
        limit: int = 20
    ) -> List[ChatSession]:
        """获取用户的所有会话"""
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.created_at.desc()).limit(limit).all()
        return sessions
    
    async def add_message(
        self,
        db: Session,
        session_id: int,
        role: str,
        content: str,
        message_type: str = "text",
        audio_url: Optional[str] = None,
        audio_duration: Optional[float] = None,
        citations: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
    ) -> ChatMessage:
        """
        添加消息到会话
        
        Args:
            db: 数据库会话
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
            message_type: 消息类型（text/audio）
            audio_url: 音频URL
            audio_duration: 音频时长
            citations: 引用来源
            metadata: 元数据
        
        Returns:
            创建的消息
        """
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            audio_url=audio_url,
            audio_duration=audio_duration,
            citations_json=citations,
            metadata_json=metadata,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.info(f"添加消息: session_id={session_id}, role={role}, type={message_type}")
        return message
    
    async def get_session_messages(
        self,
        db: Session,
        session_id: int,
        limit: int = 100
    ) -> List[ChatMessage]:
        """获取会话的所有消息"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
        return messages
    
    async def process_user_message(
        self,
        db: Session,
        session_id: int,
        user_message: str,
        job_id: Optional[int] = None
    ) -> tuple[str, Optional[List[Dict]]]:
        """
        处理用户消息并生成回复
        
        Args:
            db: 数据库会话
            session_id: 会话ID
            user_message: 用户消息
            job_id: 岗位ID（用于获取上下文）
        
        Returns:
            (回复内容, 引用来源)
        """
        try:
            # 获取对话历史
            history_messages = await self.get_session_messages(db, session_id, limit=10)
            
            # 从知识库检索相关信息（RAG）- 无论是否有job_id都要检索
            kb_results = await self._search_knowledge_base(user_message)
            
            # 构建上下文（包含岗位信息和知识库信息）
            context = await self._build_context(db, job_id, user_message, kb_results)
            
            # 构建对话历史
            messages = []
            
            # 添加系统提示（包含知识库内容）
            system_prompt = self._build_system_prompt(context, kb_results)
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史消息（最多10条）
            for msg in history_messages[-10:]:
                messages.append({
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content
                })
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 调用LLM生成回复
            response = await llm_service.chat_completion(messages, model="qwen-plus")
            
            # 获取RAG检索结果作为引用
            citations = await self._get_citations(user_message)
            
            return response, citations
            
        except Exception as e:
            logger.error(f"处理用户消息失败: {e}", exc_info=True)
            return "抱歉，我遇到了一些问题，请稍后再试。", None
    
    async def _get_citations(self, query: str) -> Optional[List[Dict]]:
        """
        获取引用来源
        
        Args:
            query: 查询文本
            
        Returns:
            引用列表
        """
        try:
            results = await knowledge_service.search(query, top_k=3)
            if not results:
                return None
            
            citations = []
            for result in results:
                citations.append({
                    "text": result["text"][:200],  # 截取前200字符
                    "doc_id": result["doc_id"],
                    "chunk_id": result["chunk_id"],
                    "score": float(result["score"])
                })
            
            return citations
            
        except Exception as e:
            logger.error(f"获取引用失败: {e}", exc_info=True)
            return None
    
    def _build_system_prompt(self, context: Optional[str] = None, kb_results: Optional[str] = None) -> str:
        """构建系统提示"""
        prompt = """你是一个专业的AI客服助手，负责回答用户的问题。

请遵循以下原则：
1. 友好、专业、准确
2. 优先使用提供的知识库内容来回答问题
3. 如果不确定答案，请诚实告知
4. 引用相关的岗位信息和公司介绍（如果有）
5. 避免做出无法兑现的承诺
6. 鼓励用户提问"""

        # 添加知识库内容（优先）
        if kb_results:
            prompt += f"\n\n【知识库内容】请优先使用以下知识库内容来回答问题：\n{kb_results}\n"
            prompt += "注意：如果知识库中有相关信息，请直接使用知识库内容回答，不要编造信息。\n"
        
        # 添加其他上下文（岗位信息等）
        if context:
            prompt += f"\n\n【其他相关信息】\n{context}"
        
        return prompt
    
    async def _build_context(
        self,
        db: Session,
        job_id: Optional[int],
        user_message: str,
        kb_results: Optional[str] = None
    ) -> Optional[str]:
        """构建上下文信息"""
        context_parts = []
        
        # 如果有岗位ID，获取岗位信息
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                context_parts.append(f"""岗位信息：
职位：{job.title}
部门：{job.department}
地点：{job.location}
薪资范围：{job.salary_range}

职位描述：
{job.description}

职位要求：
{job.requirements}

工作职责：
{job.responsibilities}
""")
        
        # 知识库内容已经在process_user_message中检索，这里不需要重复检索
        # kb_results会单独传递给_build_system_prompt
        
        if context_parts:
            return "\n".join(context_parts)
        return None
    
    async def _search_knowledge_base(self, query: str) -> Optional[str]:
        """
        从知识库检索相关信息
        
        Args:
            query: 查询文本
            
        Returns:
            检索到的相关信息文本
        """
        try:
            # 检索相关知识
            results = await knowledge_service.search(query, top_k=3)
            
            if not results:
                return None
            
            # 格式化检索结果
            kb_text = ""
            for idx, result in enumerate(results, 1):
                kb_text += f"\n[{idx}] {result['text']}\n"
            
            return kb_text
            
        except Exception as e:
            logger.error(f"知识库检索失败: {e}", exc_info=True)
            return None
    
    async def process_voice_message(
        self,
        db: Session,
        session_id: int,
        audio_data: bytes,
        audio_format: str = "pcm",
        job_id: Optional[int] = None
    ) -> tuple[Optional[str], Optional[bytes], Optional[List[Dict]]]:
        """
        处理语音消息
        
        Args:
            db: 数据库会话
            session_id: 会话ID
            audio_data: 音频数据
            audio_format: 音频格式
            job_id: 岗位ID
        
        Returns:
            (识别的文本, 回复音频, 引用来源)
        """
        try:
            # 1. 语音识别
            text = await voice_service.speech_to_text(audio_data, audio_format)
            if not text:
                logger.error("语音识别失败")
                return None, None, None
            
            logger.info(f"语音识别结果: {text}")
            
            # 2. 处理文本消息
            response_text, citations = await self.process_user_message(
                db, session_id, text, job_id
            )
            
            # 3. 文本转语音
            response_audio = await voice_service.text_to_speech(response_text)
            
            return text, response_audio, citations
            
        except Exception as e:
            logger.error(f"处理语音消息失败: {e}", exc_info=True)
            return None, None, None


# 全局实例
chat_service = ChatService()
