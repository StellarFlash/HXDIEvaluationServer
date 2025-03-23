from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv(override=True)

class Config:
    # LLM 配置
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    LLM_API_KEY = os.getenv('LLM_API_KEY') 
    LLM_MODEL = os.getenv('LLM_MODEL')

    # VLM 配置
    VLM_BASE_URL = os.getenv('VLM_BASE_URL')
    VLM_API_KEY = os.getenv('VLM_API_KEY')
    VLM_MODEL = os.getenv('VLM_MODEL')

    # Embedding 配置
    EMBEDDING_BASE_URL = os.getenv('EMBEDDING_BASE_URL')
    EMBEDDING_API_KEY = os.getenv('EMBEDDING_API_KEY')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')

    # Elasticsearch 配置
    ES_SCHEME = os.getenv('ES_SCHEME', 'https')
    ES_HOST = os.getenv('ES_HOST', 'localhost')
    ES_PORT = int(os.getenv('ES_PORT', "9200"))
    ES_USER = os.getenv('ES_USER')
    ES_PASSWORD = os.getenv('ES_PASSWORD')

    # 文档存储路径配置
    document_storage_path = os.getenv('DOCUMENT_STORAGE_PATH', 'data/documents')

# 创建全局配置实例
config = Config()
