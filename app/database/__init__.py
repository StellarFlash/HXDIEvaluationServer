from .database import Database
from .evaluation_spec_operation import store_evaluation_spec, search_evaluation_spec, batch_search_evaluation_spec, retrieve_evidence_by_spec, dump_evaluation_spec
from .evidence_operation import store_evidence, search_evidence, batch_search_evidence 
from typing import Dict, List, Any

database = Database()

def get_database():
    return database

def store_data(data: Dict[str, Any], collection_type: str = "evidence") -> str:
    """
    存储数据到数据库
    
    Args:
        data: 要存储的数据字典
        collection_type: 集合类型，可选值为"evidence"或"evaluation_spec"
    
    Returns:
        存储数据的ID
    """
    return database.store_data(data, collection_type)


def search_data(query: Dict[str, Any], collection_type: str = "evidence", top_k: int = 10) -> List[Dict[str, Any]]:
    """
    在数据库中搜索相似数据
    
    Args:
        query: 查询字典
        collection_type: 集合类型
        top_k: 返回结果数量
    
    Returns:
        包含匹配结果的列表
    """
    return database.search_data(query, collection_type, top_k)



__all__ = ['Database', 'get_database', 'store_data', 'search_data',
           'store_evaluation_spec', 'search_evaluation_spec', 'batch_search_evaluation_spec', 'retrieve_evidence_by_spec',
           'store_evidence', 'search_evidence', 'batch_search_evidence', 'dump_evaluation_spec']