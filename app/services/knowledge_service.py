"""
知识库服务模块
处理文档向量化、存储和检索
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import hashlib
import json

from app.models import KBDocument, KBChunk
from app.config import settings
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库服务类"""
    
    def __init__(self):
        self.chunk_size = 500  # 文本块大小
        self.chunk_overlap = 50  # 重叠大小
    
    async def process_document(
        self,
        db: Session,
        document_id: int,
        text: str
    ) -> None:
        """
        处理文档：分块、向量化、存储
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            text: 文档文本内容
        """
        try:
            # 1. 文本分块
            chunks = self._split_text(text)
            logger.info(f"文档 {document_id} 分块完成，共 {len(chunks)} 个块")
            
            # 2. 为每个块生成向量并存储
            for idx, chunk_text in enumerate(chunks):
                # 生成向量
                embedding = await embedding_service.get_embedding(chunk_text)
                
                # 创建chunk记录
                chunk = KBChunk(
                    doc_id=document_id,
                    chunk_text=chunk_text,
                    metadata_json={
                        "chunk_index": idx,
                        "chunk_size": len(chunk_text)
                    }
                )
                db.add(chunk)
                db.flush()  # 获取chunk.id
                
                # 存储到Milvus
                milvus_id = await self._store_to_milvus(
                    chunk.id,
                    embedding,
                    chunk_text,
                    document_id
                )
                
                # 更新chunk的milvus_id
                chunk.milvus_id = milvus_id
                db.commit()
            
            logger.info(f"文档 {document_id} 处理完成")
            
        except Exception as e:
            logger.error(f"处理文档失败: {e}", exc_info=True)
            db.rollback()
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """
        将文本分割成块
        
        Args:
            text: 原始文本
            
        Returns:
            文本块列表
        """
        # 简单的按段落和句子分割
        # 可以改进为更智能的分割策略
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前块加上新段落超过大小限制，保存当前块
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 如果块太大，进一步分割
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                # 按句子分割
                sentences = chunk.split('。')
                temp_chunk = ""
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) > self.chunk_size:
                        if temp_chunk:
                            final_chunks.append(temp_chunk.strip() + '。')
                        temp_chunk = sentence
                    else:
                        temp_chunk += sentence + '。'
                if temp_chunk:
                    final_chunks.append(temp_chunk.strip())
        
        return final_chunks
    
    async def _store_to_milvus(
        self,
        chunk_id: int,
        embedding: List[float],
        text: str,
        doc_id: int
    ) -> str:
        """
        存储向量到Milvus
        
        Args:
            chunk_id: 块ID
            embedding: 向量
            text: 文本内容
            doc_id: 文档ID
            
        Returns:
            Milvus ID
        """
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
            
            # 连接Milvus
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            
            # 获取或创建集合
            collection = self._get_or_create_collection()
            
            # 准备数据
            milvus_id = f"chunk_{chunk_id}"
            data = [{
                "id": milvus_id,
                "embedding": embedding,
                "text": text[:1000],  # Milvus可能有长度限制
                "doc_id": doc_id,
                "chunk_id": chunk_id
            }]
            
            # 插入数据
            collection.insert(data)
            collection.flush()
            
            logger.info(f"向量存储成功: chunk_id={chunk_id}, milvus_id={milvus_id}")
            return milvus_id
            
        except Exception as e:
            logger.error(f"存储向量失败: {e}", exc_info=True)
            raise
    
    def _get_or_create_collection(self):
        """获取或创建Milvus集合"""
        from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
        
        try:
            collection = Collection(settings.MILVUS_COLLECTION_NAME)
            return collection
        except:
            # 创建集合
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="doc_id", dtype=DataType.INT64),
                FieldSchema(name="chunk_id", dtype=DataType.INT64),
            ]
            schema = CollectionSchema(fields, "知识库向量集合")
            collection = Collection(settings.MILVUS_COLLECTION_NAME, schema)
            
            # 创建索引
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index("embedding", index_params)
            
            return collection
    
    async def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回top k个结果
            
        Returns:
            检索结果列表，每个结果包含：text, doc_id, chunk_id, score
        """
        try:
            # 1. 生成查询向量
            query_embedding = await embedding_service.get_embedding(query)
            
            # 2. 从Milvus检索
            from pymilvus import connections, Collection
            
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            
            collection = Collection(settings.MILVUS_COLLECTION_NAME)
            collection.load()
            
            # 搜索
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "doc_id", "chunk_id"]
            )
            
            # 格式化结果
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "text": hit.entity.get("text"),
                        "doc_id": hit.entity.get("doc_id"),
                        "chunk_id": hit.entity.get("chunk_id"),
                        "score": hit.score
                    })
            
            logger.info(f"检索完成: query={query[:50]}, results={len(search_results)}")
            return search_results
            
        except Exception as e:
            logger.error(f"检索失败: {e}", exc_info=True)
            return []
    
    async def delete_document(
        self,
        db: Session,
        document_id: int
    ) -> None:
        """
        删除文档及其所有相关数据
        
        Args:
            db: 数据库会话
            document_id: 文档ID
        """
        try:
            # 1. 获取所有chunks
            chunks = db.query(KBChunk).filter(KBChunk.doc_id == document_id).all()
            logger.info(f"找到 {len(chunks)} 个chunks需要删除，文档ID: {document_id}")
            
            # 2. 从Milvus删除向量
            milvus_ids = [chunk.milvus_id for chunk in chunks if chunk.milvus_id]
            if milvus_ids:
                try:
                    from pymilvus import connections, Collection
                    
                    connections.connect(
                        alias="default",
                        host=settings.MILVUS_HOST,
                        port=settings.MILVUS_PORT
                    )
                    
                    collection = Collection(settings.MILVUS_COLLECTION_NAME)
                    collection.load()  # 确保collection已加载
                    
                    # Milvus删除表达式格式：id in ["id1", "id2", ...]
                    # 对于单个ID，也可以使用：id == "id1"
                    if len(milvus_ids) == 1:
                        expr = f'id == "{milvus_ids[0]}"'
                    else:
                        # 多个ID使用 in 表达式
                        ids_str = '", "'.join(milvus_ids)
                        expr = f'id in ["{ids_str}"]'
                    
                    logger.info(f"Milvus删除表达式: {expr}")
                    collection.delete(expr)
                    collection.flush()
                    logger.info(f"从Milvus删除 {len(milvus_ids)} 个向量成功")
                except Exception as milvus_error:
                    # Milvus删除失败不影响数据库删除，记录错误但继续
                    logger.warning(f"从Milvus删除向量失败（继续删除数据库记录）: {milvus_error}", exc_info=True)
            
            # 3. 删除数据库中的chunks
            for chunk in chunks:
                db.delete(chunk)
            
            db.commit()
            logger.info(f"文档 {document_id} 及其相关数据删除完成")
            
        except Exception as e:
            logger.error(f"删除文档数据失败: {e}", exc_info=True)
            db.rollback()
            raise


# 全局实例
knowledge_service = KnowledgeService()
