from pydantic import BaseModel
from typing import List, Optional

class EvaluationSpecResponse(BaseModel):
    id: str
    primary_title: str
    secondary_title: str
    tertiary_title: str
    content: str
    evaluation_guidelines: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    created_at: str

class EvaluationSpecListResponse(BaseModel):
    evaluation_specs: List[EvaluationSpecResponse]
    total: int
