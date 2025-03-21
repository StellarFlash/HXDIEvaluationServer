import os
import shutil
from app.config.config import config
from app.db.database import es_client

def save_document_to_storage(file_path: str) -> str:
    """将文件保存到配置的存储路径"""
    file_name = os.path.basename(file_path)
    storage_path = os.path.join(config.document_storage_path, file_name)
    os.makedirs(config.document_storage_path, exist_ok=True)
    shutil.copy(file_path, storage_path)
    return storage_path

def save_document_metadata(file_name: str, storage_path: str):
    """将文件元数据保存到 ES"""
    doc = {
        "file_name": file_name,
        "storage_path": storage_path,
        "timestamp": "now"
    }
    es_client.index(index="documents", body=doc)

def process_document(file_path: str):
    # 1. 将原始文件存储到本地文件系统
    storage_path = save_document_to_storage(file_path)
    
    # 2. 将文件元数据存储到 ES 中
    save_document_metadata(os.path.basename(file_path), storage_path)
    
    # 3. TODO: 实现文档处理的逻辑，例如格式转换、切片、构建语义索引、存储向量数据库等
    return {"document_info": f"文档已存储到 {storage_path}"}
