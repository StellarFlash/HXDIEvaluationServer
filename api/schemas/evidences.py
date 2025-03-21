from pydantic import BaseModel
from typing import List, Optional

class EvidenceResponse(BaseModel):
    id: str
    filename: str
    content: str
    summary: str
    created_at: str

class EvidenceListResponse(BaseModel):
    evidences: List[EvidenceResponse]
    total: int
