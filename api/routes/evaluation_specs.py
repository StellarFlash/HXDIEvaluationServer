from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.models.evaluation_spec.manager import EvaluationSpecManager
from api.dependencies import get_evaluation_spec_manager, run_in_threadpool
from api.schemas.evaluation_specs import EvaluationSpecResponse, EvaluationSpecListResponse
import json
import os

router = APIRouter()

@router.post("/upload", response_model=EvaluationSpecListResponse)
async def upload_evaluation_spec(
    file: UploadFile = File(...),
    manager: EvaluationSpecManager = Depends(get_evaluation_spec_manager)
):
    """上传评估规范文件"""
    
    # 验证文件类型
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=400,
            detail="仅支持JSON文件上传"
        )
    
    try:
        # 读取文件内容
        content = await file.read()
        data = json.loads(content)
        
        # 直接写入evaluation_spec.json
        spec_file = "data/evaluation_spec.json"
        with open(spec_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        # 处理文件
        manager.load_from_json(spec_file)
        manager.generate_index()
        
        # 返回处理结果
        return {
            "evaluation_specs": [spec.to_dict() for spec in manager.specs],
            "total": len(manager.specs)
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="无效的JSON格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件处理失败: {str(e)}"
        )

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
