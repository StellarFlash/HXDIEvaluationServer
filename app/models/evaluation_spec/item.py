from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

class EvaluationSpecItem(BaseModel):
    """评估规范项类"""
    id: str = Field(default_factory=lambda: str(uuid4()))  # 唯一标识
    primary_title: str  # 一级标题
    secondary_title: str  # 二级标题
    tertiary_title: str  # 三级标题
    content: str  # 内容
    evaluation_guidelines: List[str]  # 评估指南
    summary: str = ""  # 摘要
    summary_embedding: Optional[List[float]] = None  # 摘要向量
    keywords: List[str] = [] # 关键词
    keywords_embedding: Optional[List[float]] = None  # 关键词向量
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())  # 创建时间
    
    def to_dict(self, embeddings: bool = False) -> Dict[str, any]:
        """将评估规范项转换为字典
        Args:
            embeddings: 是否包含向量数据，默认为False
        Returns:
            包含评估规范数据的字典
        """
        data = {
            "id": self.id,
            "primary_title": self.primary_title,
            "secondary_title": self.secondary_title,
            "tertiary_title": self.tertiary_title,
            "content": self.content,
            "evaluation_guidelines": self.evaluation_guidelines,
            "keywords": self.keywords,
            "created_at": self.created_at
        }
        if embeddings:
            if self.keywords_embedding is not None:
                data["keywords_embedding"] = self.keywords_embedding
            if self.summary_embedding is not None:
                data["summary_embedding"] = self.summary_embedding
        return data
