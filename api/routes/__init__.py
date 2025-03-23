# 路由模块初始化文件
from api.routes.reports import router as reports_router
from api.routes.evidences import router as evidences_router
from api.routes.evaluation_specs import router as evaluation_specs_router
from api.routes.upload import router as upload_router
from api.routes.db import router as db_router

__all__ = ["reports_router", "evidences_router", "evaluation_specs_router", "upload_router", "db_router"]
