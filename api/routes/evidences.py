from fastapi import APIRouter, Depends, HTTPException
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.models.evidence.manager import EvidenceManager
from api.dependencies import get_evidence_manager, run_in_threadpool
from api.schemas.evidences import EvidenceResponse, EvidenceListResponse

router = APIRouter()

@router.get("/", response_model=EvidenceListResponse)
async def get_evidences(
    start: int = 0,
    end: int = 9,
    manager: EvidenceManager = Depends(get_evidence_manager)
):
    try:
        return await run_in_threadpool(
            manager.get_evidences,
            start,
            end
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取证明材料列表失败: {str(e)}"
        )

@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: int = 0,
    manager: EvidenceManager = Depends(get_evidence_manager)
):
    try:
        result = await run_in_threadpool(
            manager.get_evidence,
            evidence_id
        )
        if not result:
            raise HTTPException(
                status_code=404,
                detail="证明材料未找到"
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取证明材料详情失败: {str(e)}"
        )
