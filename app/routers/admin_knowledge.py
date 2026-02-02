"""
管理员知识库管理路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import KBDocument, KBChunk
from app.auth import get_current_user
from app.schemas import ApiResponse
from app.constants import UserType
from app.utils.file_extraction import extract_text
from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/knowledge", tags=["Admin - Knowledge Base"])


def check_admin(current_user: dict):
    """检查是否为管理员"""
    if current_user.get("user_type") != UserType.ADMIN.value:
        raise HTTPException(status_code=403, detail="需要管理员权限")


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    title: str
    source: str
    content: str
    metadata_json: Optional[dict]
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentResponse]
    total: int


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[DocumentResponse]:
    """
    上传知识库文档（管理员）
    
    支持格式：PDF, DOCX, TXT
    """
    check_admin(current_user)
    
    try:
        # 读取文件内容
        file_bytes = await file.read()
        
        # 提取文本（自动检测文件类型）
        text = extract_text(file_bytes=file_bytes, filename=file.filename)
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="无法从文件中提取文本或文件为空")
        
        # 创建文档记录
        document = KBDocument(
            title=file.filename,
            source="upload",
            content=text,
            metadata_json={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file_bytes)
            }
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # 处理文档：分块、向量化、存储
        await knowledge_service.process_document(db, document.id, text)
        
        logger.info(f"文档上传成功: document_id={document.id}, filename={file.filename}")
        
        return ApiResponse(
            code=0,
            message="success",
            data=DocumentResponse(
                id=document.id,
                title=document.title,
                source=document.source,
                content=document.content[:500] + "..." if len(document.content) > 500 else document.content,
                metadata_json=document.metadata_json,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/documents")
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[DocumentListResponse]:
    """获取知识库文档列表（管理员）"""
    check_admin(current_user)
    
    try:
        documents = db.query(KBDocument).order_by(KBDocument.created_at.desc()).all()
        
        return ApiResponse(
            code=0,
            message="success",
            data=DocumentListResponse(
                documents=[
                    DocumentResponse(
                        id=doc.id,
                        title=doc.title,
                        source=doc.source,
                        content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        metadata_json=doc.metadata_json,
                        created_at=doc.created_at,
                        updated_at=doc.updated_at,
                    )
                    for doc in documents
                ],
                total=len(documents),
            )
        )
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[DocumentResponse]:
    """获取文档详情（管理员）"""
    check_admin(current_user)
    
    try:
        document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return ApiResponse(
            code=0,
            message="success",
            data=DocumentResponse(
                id=document.id,
                title=document.title,
                source=document.source,
                content=document.content,
                metadata_json=document.metadata_json,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """删除文档（管理员）"""
    check_admin(current_user)
    
    try:
        document = db.query(KBDocument).filter(KBDocument.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除相关的chunks和向量数据
        await knowledge_service.delete_document(db, document_id)
        
        # 删除文档记录
        db.delete(document)
        db.commit()
        
        logger.info(f"文档删除成功: document_id={document_id}")
        
        return ApiResponse(
            code=0,
            message="success",
            data={"deleted": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
