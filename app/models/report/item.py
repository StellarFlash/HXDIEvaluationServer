from typing import List
from pydantic import BaseModel
from sympy import false
from app.models.evaluation_spec.item import EvaluationSpecItem
from app.models.evidence.item import EvidenceItem

class ReportItem(BaseModel):
    """报告项"""
    spec: EvaluationSpecItem  # 评估规范
    evidences: List[EvidenceItem]  # 召回的证明材料
    is_qualified: bool = False  # 是否合格
    conclusion: str = ""  # 评估结论

    def to_dict(self, embeddings = False) -> dict:
        """转换为字典"""
        return {
            "spec": self.spec.to_dict(embeddings=false),
            "evidences": [e.to_dict(embeddings=false) for e in self.evidences],
            "is_qualified": self.is_qualified,
            "conclusion": self.conclusion
        }
