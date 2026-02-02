"""
向量化服务模块
使用模型生成文本向量
"""
import logging
from typing import List
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """向量化服务类"""
    
    def __init__(self):
        self.model = settings.EMBEDDING_MODEL
        self.dim = settings.EMBEDDING_DIM
        # 使用DashScope的embedding API
        self.api_key = settings.DASHSCOPE_API_KEY
        # DashScope embedding API endpoint
        self.api_base = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY未设置，返回零向量")
            return [0.0] * self.dim
        
        try:
            # 使用DashScope的embedding API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_base,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": {
                            "texts": [text]
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # DashScope返回格式：{"output":{"embeddings":[{"embedding":[...]}]}}
                if "output" in result and "embeddings" in result["output"]:
                    embeddings = result["output"]["embeddings"]
                    if embeddings and len(embeddings) > 0:
                        embedding = embeddings[0].get("embedding", [])
                        if embedding:
                            return embedding
                
                logger.error(f"Embedding API返回格式错误: {result}")
                raise Exception("Embedding API返回格式错误")
                    
        except Exception as e:
            logger.error(f"生成向量失败: {e}", exc_info=True)
            # 返回零向量作为fallback
            return [0.0] * self.dim


# 全局实例
embedding_service = EmbeddingService()
