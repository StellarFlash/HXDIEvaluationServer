import json
from fastapi import APIRouter, Depends, HTTPException
from app.database import Database,get_database
from api.dependencies import get_database, run_in_threadpool

router = APIRouter()
database = get_database()

@router.post("/init_database/")
async def init_database(
    databse: Database = Depends(get_database)
):
    try:
        await run_in_threadpool(databse.init_database)
        return {
            "success": True,
            "message": "数据库初始化成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据库初始化失败: {str(e)}"
        ) from e
