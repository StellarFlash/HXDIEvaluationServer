# pylint: disable=no-self-argument
"""Disable self argument check for Pydantic field validators"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class ReportResponse(BaseModel):
    id: Optional[str] = Field(default="")
    evaluation_spec: Optional[str] = Field(default="")
    evidences: Optional[List[str]] = Field(default_factory=list)
    is_qualified: Optional[bool] = Field(default=False)
    conclusion: Optional[str] = Field(default="")
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

    @field_validator('is_qualified', mode='before')
    def parse_bool(cls, v):  # pylint: disable=no-self-argument
        """Pydantic field validator must be class method (no self)"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v = v.lower()
            if v in ('是', 'yes', 'true', 't', '1'):
                return True
            if v in ('否', 'no', 'false', 'f', '0'):
                return False
        raise ValueError('Invalid boolean value')

class ReportListResponse(BaseModel):
    reports: List[ReportResponse] = Field(default_factory=list)
    total: Optional[int] = Field(default=0)
