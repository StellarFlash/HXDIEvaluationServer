from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.models.evaluation_spec.manager import EvaluationSpecManager
from api.dependencies import get_evaluation_spec_manager, run_in_threadpool
from api.schemas.evaluation_specs import EvaluationSpecResponse, EvaluationSpecListResponse

router = APIRouter()

@router.post("/generate_index", status_code=status.HTTP_202_ACCEPTED)
async def generate_evaluation_spec_index(
    manager: EvaluationSpecManager = Depends(get_evaluation_spec_manager)
):
    """生成评估规范索引"""
    try:
        return await run_in_threadpool(manager.generate_index)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成评估规范索引失败: {str(e)}"
        )


@router.get("/", response_model=EvaluationSpecListResponse)
async def get_evaluation_specs(
    start: int = 0,
    end: int = 9,
    manager: EvaluationSpecManager = Depends(get_evaluation_spec_manager)
):
    try:
        return await run_in_threadpool(
            manager.get_evaluation_specs,
            start,
            end
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取评估规范列表失败: {str(e)}"
        )

@router.get("/{spec_id}", response_model=EvaluationSpecResponse)
async def get_evaluation_spec(
    spec_id: int = 0,
    manager: EvaluationSpecManager = Depends(get_evaluation_spec_manager)
):
    try:
        result = await run_in_threadpool(
            manager.get_evaluation_spec,
            spec_id
        )
        if not result:
            raise HTTPException(
                status_code=404,
                detail="评估规范未找到"
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取评估规范详情失败: {str(e)}"
        )
