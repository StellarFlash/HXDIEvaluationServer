from pickle import FALSE
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EvidenceItem(BaseModel):
    """证明材料项类"""
    id: Optional[str] = None  # 唯一标识，由manager分配
    created_at: Optional[str] = None  # 创建时间
    filename: str  # 文件名
    file_format: str  # 文件格式
    collection_time: datetime  # 采集时间
    collector: str  # 采集人员
    project: str  # 所属项目
    evidence_type: str  # 类型
    content: str  # 内容
    summary: Optional[str] = ""  # 摘要
    summary_embedding: Optional[List[float]] = None  # 摘要向量
    keywords: Optional[List[str]] = []  # 关键词
    keywords_embedding: Optional[List[float]] = None

    def to_dict(self, embeddings: bool = False) -> dict:
        """将证明材料项转换为字典"""
        data = {
            "id": self.id,
            "filename": self.filename,
            "file_format": self.file_format,
            "collection_time": self.collection_time.isoformat(),
            "collector": self.collector,
            "project": self.project,
            "evidence_type": self.evidence_type,
            "content": self.content,
            "summary": self.summary,
            "keywords": self.keywords,
            "created_at": self.created_at
        }
        
        if embeddings:
            if self.keywords_embedding is not None:
                data["keywords_embedding"] = (
                    self.keywords_embedding["vector"] 
                    if isinstance(self.keywords_embedding, dict) 
                    else self.keywords_embedding
                )
            if self.summary_embedding is not None:
                data["summary_embedding"] = (
                    self.summary_embedding["vector"]
                    if isinstance(self.summary_embedding, dict)
                    else self.summary_embedding
                )
        
        return data
