from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from typing import List
from app.models.document.manager import DocumentManager
from api.dependencies import get_document_manager

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/documents", response_model=List[str])
def upload_documents(
    files: List[UploadFile] = File(...),
    document_manager: DocumentManager = Depends(get_document_manager)
):
    """上传文档文件接口"""
    try:
        # 确保上传目录存在
        upload_dir = Path("data/upload")
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for file in files:
            # 验证文件类型
            if not file.filename.endswith(".docx"):
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {file.filename}"
                )

            # 保存文件到上传目录
            file_path = upload_dir / file.filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 调用DocumentManager处理文件
            document_item = document_manager.parse_document(file_path)
            saved_files.append(str(file_path))

        # 重新初始化管理器实例
        from api.managers import document_manager, evidence_manager
        document_manager = document_manager.__class__()
        evidence_manager = evidence_manager.__class__()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "文件上传成功",
                "files": saved_files
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )
