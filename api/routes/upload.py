from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from typing import List
from app.models.document.manager import DocumentManager
from api.dependencies import get_document_manager

router = APIRouter(prefix="/evidences", tags=["evidences"])

@router.post("/upload", response_model=List[str])
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
        from api.managers import report_manager,evidence_manager
        evidence_manager.load_from_json(file_path = "data/evidence.json")
        evidence_manager.generate_index()
        print("Evidence Updated.")
        print(str(evidence_manager.evidences.__sizeof__()) + " evidence in total.")
        
        report_manager.load_data()
        
        
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
