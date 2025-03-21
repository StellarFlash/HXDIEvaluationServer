import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends
from api.managers import report_manager, evidence_manager, evaluation_spec_manager
from app.models.report.manager import ReportManager
from app.models.evidence.manager import EvidenceManager
from app.models.evaluation_spec.manager import EvaluationSpecManager

executor = ThreadPoolExecutor(max_workers=4)

async def get_report_manager() -> ReportManager:
    """获取全局ReportManager实例"""
    return report_manager

async def get_evidence_manager() -> EvidenceManager:
    """获取全局EvidenceManager实例"""
    return evidence_manager

async def get_evaluation_spec_manager() -> EvaluationSpecManager:
    """获取全局EvaluationSpecManager实例"""
    return evaluation_spec_manager



async def run_in_threadpool(func, *args):
    """在线程池中执行同步函数"""
    return await asyncio.get_event_loop().run_in_executor(executor, func, *args)
