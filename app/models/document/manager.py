from pathlib import Path
from typing import Optional
import logging
import time
from datetime import datetime
from app.models.document.models import DocumentItem
from app.models.document.parser import DocumentParser

logger = logging.getLogger(__name__)

class DocumentManager:
    """管理文档解析和存储"""
    
    def __init__(self, upload_dir: str = "data/upload"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file, filename: str) -> Path:
        """保存上传的文件"""
        # 处理文件名冲突
        base_name = Path(filename).stem
        ext = Path(filename).suffix
        counter = 1
        while True:
            file_path = self.upload_dir / filename
            if not file_path.exists():
                break
            filename = f"{base_name}_{counter}{ext}"
            counter += 1

        start_time = time.time()
        logger.info(f"开始保存文件: {filename}")
        
        try:
            with file_path.open("wb") as buffer:
                file_content = await file.read()
                buffer.write(file_content)
                
            logger.info(f"文件保存成功: {filename} (大小: {len(file_content)} bytes, 耗时: {time.time() - start_time:.2f}s)")
            return file_path
        except Exception as e:
            logger.error(f"文件保存失败: {filename}, 错误: {str(e)}")
            raise
    
    def parse_document(self, file_path: Path) -> Optional[DocumentItem]:
        """解析上传的文档"""
        start_time = time.time()
        logger.info(f"开始解析文档: {file_path.name}")
        
        try:
            parser = DocumentParser(source_dir=str(file_path.parent))
            result = parser.parse_document(file_path)
            
            logger.info(f"文档解析成功: {file_path.name} (耗时: {time.time() - start_time:.2f}s)")
            return result
        except Exception as e:
            logger.error(f"文档解析失败: {file_path.name}, 错误: {str(e)}")
            raise
    
    def cleanup_uploaded_file(self, file_path: Path):
        """清理上传的文件"""
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"文件清理成功: {file_path.name}")
            except Exception as e:
                logger.error(f"文件清理失败: {file_path.name}, 错误: {str(e)}")
