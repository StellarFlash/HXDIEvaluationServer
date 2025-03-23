from dataclasses import dataclass
from typing import Dict, List
import hashlib
from datetime import datetime

@dataclass
class DocumentChunk:
    hash: str
    url: str = ""
    content: str = ""
    index: int = 0
    collector: str = ""
    project: str = ""
    evidence_type: str = ""

@dataclass
class DocumentImage:
    hash: str
    url: str = ""
    content: str = ""
    description: str = ""
    name: str = ""
    index: int = 0
    collector: str = ""
    project: str = ""
    evidence_type: str = ""

@dataclass
class DocumentItem:
    hash: str
    url: str
    chunks: List[DocumentChunk]
    images: List[DocumentImage]

    @staticmethod
    def compute_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def to_evidence_json(self, filename: str) -> List[Dict]:
        """将文档项转换为证据JSON格式"""
        evidences = []
        
        # 添加chunks证据
        for i, chunk in enumerate(self.chunks):
            evidences.append({
                "filename": f"{filename}_chunk_{i+1}",
                "file_format": "MARKDOWN",
                "collection_time": datetime.now().isoformat(),
                "collector": chunk.collector,
                "project": chunk.project,
                "evidence_type": chunk.evidence_type,
                "content": chunk.content,
                "summary": "",
                "keywords": []
            })
        
        # 添加images证据
        for image in self.images:
            evidences.append({
                "filename": image.name,
                "file_format": "PNG",
                "collection_time": datetime.now().isoformat(),
                "collector": image.collector,
                "project": image.project,
                "evidence_type": "Image",
                "content": image.description,
                "summary": image.description,
                "keywords": []
            })
            
        return evidences
