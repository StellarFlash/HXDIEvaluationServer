import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv(override=True)

class Config:
    def __init__(self):
        # LLM 配置
        self.LLM_BASE_URL = os.getenv('LLM_BASE_URL')
        self.LLM_API_KEY = os.getenv('LLM_API_KEY')
        self.LLM_MODEL = os.getenv('LLM_MODEL')

        # VLM 配置
        self.VLM_BASE_URL = os.getenv('VLM_BASE_URL')
        self.VLM_API_KEY = os.getenv('VLM_API_KEY')
        self.VLM_MODEL = os.getenv('VLM_MODEL')

        # Embedding 配置
        self.EMBEDDING_BASE_URL = os.getenv('EMBEDDING_BASE_URL')
        self.EMBEDDING_API_KEY = os.getenv('EMBEDDING_API_KEY')
        self.EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')

        # Milvus 配置
        self.MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
        self.MILVUS_PORT = int(os.getenv('MILVUS_PORT', "19530"))
        self.MILVUS_USER = os.getenv('MILVUS_USER')
        self.MILVUS_PASSWORD = os.getenv('MILVUS_PASSWORD')
        self.EMBEDDING_DIM = int(os.getenv('EMBEDDING_DIM', "1024"))
        
        # 文档存储路径配置
        self.document_storage_path = os.getenv('DOCUMENT_STORAGE_PATH', 'data/documents')
