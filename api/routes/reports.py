import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.models.report.manager import ReportManager
from api.dependencies import get_report_manager, run_in_threadpool
from api.schemas.reports import ReportResponse, ReportListResponse

router = APIRouter()

@router.get("/", response_model=ReportListResponse)
async def get_reports(
    start: int = 0,
    end: int = 9,
    manager: ReportManager = Depends(get_report_manager)
):
    try:
        result = await run_in_threadpool(
            manager.get_reports,
            start,
            end
        )
        # 转换 evaluation_spec 和 evidences 为字符串
        for report in result["reports"]:
            if report["evaluation_spec"]:
                eval_spec = report["evaluation_spec"]
                report["evaluation_spec"] = json.dumps(
                    eval_spec if isinstance(eval_spec, dict) else eval_spec.to_dict(embeddings=False),
                    ensure_ascii=False
                )
            if report["evidences"]:
                report["evidences"] = [
                    json.dumps(
                        e if isinstance(e, dict) else e.to_dict(embeddings=False),
                        ensure_ascii=False
                    ) for e in report["evidences"]
                ]
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取报告列表失败: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    manager: ReportManager = Depends(get_report_manager)
):
    try:
        result = await run_in_threadpool(
            manager.get_report,
            report_id
        )
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"未找到ID为{report_id}的报告"
            )
        # 转换 evaluation_spec 和 evidences 为字符串
        if result["evaluation_spec"]:
            eval_spec = result["evaluation_spec"]
            result["evaluation_spec"] = json.dumps(
                eval_spec if isinstance(eval_spec, dict) else eval_spec.to_dict(embeddings=False),
                ensure_ascii=False
            )
        if result["evidences"]:
            result["evidences"] = [
                json.dumps(
                    e if isinstance(e, dict) else e.to_dict(embeddings=False),
                    ensure_ascii=False
                ) for e in result["evidences"]
            ]
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取报告详情失败: {str(e)}"
        )
        
@router.post("/generate/")  # 设置5分钟超时 # pylint: disable=unexpected-keyword-arg
def generate_reports(
    manager: ReportManager = Depends(get_report_manager)
):
    try:
        result = manager.generate_report()
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "报告生成失败")
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"报告生成失败: {str(e)}"
        )

@router.post("/reload-data/")
async def reload_data(
    manager: ReportManager = Depends(get_report_manager)
):
    try:
        result = await run_in_threadpool(
            manager.load_data
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "数据重载失败")
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据重载失败: {str(e)}"
        )
