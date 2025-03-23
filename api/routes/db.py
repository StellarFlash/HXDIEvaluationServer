import json
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import Database
from api.dependencies import get_db, run_in_threadpool

router = APIRouter()

@router.post("/init-db/")
async def init_db(
    db: Database = Depends(get_db)
):
    try:
        await run_in_threadpool(db.init_db)
        return {
            "success": True,
            "message": "数据库初始化成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据库初始化失败: {str(e)}"
        )
