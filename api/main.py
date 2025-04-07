from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import reports_router, evidences_router, evaluation_specs_router, upload_router, database_router


app = FastAPI(
    title="HXAgent API",
    description="HXAgent系统API接口",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(evidences_router, prefix="/api/v1/evidences", tags=["evidences"])
app.include_router(evaluation_specs_router, prefix="/api/v1/evaluation_specs", tags=["evaluation_specs"])
app.include_router(upload_router, prefix="/api/v1", tags=["evidences"])
app.include_router(database_router, prefix="/api/v1/database", tags=["database"])

if __name__ == "__main__":
    import uvicorn
    # 在启动应用前显式初始化数据
    uvicorn.run(app, host="0.0.0.0", port=8000)
