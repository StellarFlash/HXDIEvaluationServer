import os
import shutil
import json
from typing import Dict, Any, List, Union
from abc import ABC
from markitdown import MarkItDown
import app.config as get_config
from app.database.es_database import es_client

config = get_config()
class DocumentItem(ABC):
    """文档元素基类"""
    def __init__(self):
        self.uuid: str = ""
        self.metadata: dict = {}
        self.index: int = 0

class DocumentChunk(DocumentItem):
    """文档文本块"""
    def __init__(self):
        super().__init__()
        self.content: str = ""
        self.annotations: List[dict] = []

class DocumentImage(DocumentItem):
    """文档图像元素"""
    def __init__(self):
        super().__init__()
        self.description: str = ""
        self.url: str = ""
        self.alt_text: str = ""

class ParsedDocument:
    """解析后的完整文档"""
    def __init__(self):
        self.file_hash: str = ""
        self.chunks: List[DocumentChunk] = []
        self.images: List[DocumentImage] = []
        self.doc_metadata: dict = {}
        self.storage_path: str = ""

    def get_combined_index(self) -> List[Union[DocumentChunk, DocumentImage]]:
        """获取按原始排版顺序排列的元素列表"""
        return sorted(
            self.chunks + self.images,
            key=lambda x: x.index
        )

class DocumentParser:
    """旧版文档解析器（保持兼容性）"""
    def __init__(self):
        self.converter = MarkItDown(enable_plugins=False)

    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析文档并返回结构化数据"""
        result = self.converter.convert(file_path)
        return {
            "raw_content": result.text_content,
            "metadata": result.metadata
        }

    def extract_evidence_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取证据元数据"""
        from app.utils.maas_client import maas_client
        
        # 获取基础信息
        file_name = os.path.basename(file_path)
        file_format = file_name.split('.')[-1].upper()
        
        # 调用MaaSClient提取关键信息
        prompt = f'''请从以下文档内容中提取关键信息：
{self.parse(file_path)['raw_content']}

根据以下要求返回JSON格式：
{{
    "content": "文档核心内容摘要（200字内）",
    "summary": "关键结论摘要（100字内）", 
    "keywords": ["关键词1", "关键词2"],
    "evidence_type": "报告类型"
}}'''
        
        # 获取LLM提取结果
        llm_result = maas_client.chat_completion(prompt, output_format='json')
        
        return {
            "filename": file_name,
            "file_format": file_format,
            "collection_time": "now",
            "collector": "测试用户",  # 默认值，待身份认证功能实现后更新
            "project": "默认项目",   # 默认值，待项目管理系统实现后更新
            "evidence_type": llm_result.get("evidence_type", "未知类型"),
            "content": llm_result.get("content", ""),
            "summary": llm_result.get("summary", ""),
            "keywords": llm_result.get("keywords", [])
        }


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
    # 1. 文件存储
    storage_path = save_document_to_storage(file_path)
    
    # 2. 元数据存储
    save_document_metadata(os.path.basename(file_path), storage_path)
    
    # 3. 文档解析
    parser = DocumentParser()
    parsed_data = parser.parse(file_path)
    evidence_metadata = parser.extract_evidence_metadata(file_path)
    
    # 保存证据元数据到ES
    es_client.index(index="evidence", body=evidence_metadata)
    
    # 保存证据元数据到文件
    evidence_file_path = os.path.join(config.document_storage_path, "evidence.json")
    if os.path.exists(evidence_file_path):
        with open(evidence_file_path, 'r', encoding='utf-8') as f:
            evidence_list = json.load(f)
    else:
        evidence_list = []
    
    evidence_list.append(evidence_metadata)
    
    with open(evidence_file_path, 'w', encoding='utf-8') as f:
        json.dump(evidence_list, f, ensure_ascii=False, indent=4)
    
    return {
        "storage_path": storage_path,
        "parsed_data": parsed_data,
        "evidence_metadata": evidence_metadata
    }
