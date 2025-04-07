from typing import Dict, Any, List

import uuid
import json

from .database import Database

def store_evaluation_spec(database, spec: Dict[str, Any]) -> str:
    """存储评估规范"""
    spec_id = str(uuid.uuid4())
    spec_data = {
        'id': spec_id,
        'keywords_embedding': spec.get('keywords_embedding'),
        'summary_embedding': spec.get('summary_embedding'),
        'metadata': json.dumps(spec)
    }
    return database.store_data(spec_data, collection_type="evaluation_spec")
        
def search_evaluation_spec(database, query: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    搜索评估规范
    
    Args:
        query: 查询字典，可包含keywords_embedding和/或summary_embedding字段
        top_k: 返回的结果数量
        
    Returns:
        匹配的评估规范列表
    """
    if 'keywords_embedding' not in query and 'summary_embedding' not in query:
        return []
        
    # 组合查询向量，默认权重为keywords:0.7, summary:0.3
    combined_embedding = [
        0.7 * x + 0.3 * y
        for x, y in zip(
            query.get('keywords_embedding', [0]*len(query.get('summary_embedding', []))),
            query.get('summary_embedding', [0]*len(query.get('keywords_embedding', [])))
        )
    ]
    return database.search_data(query = query, collection_type="evaluation_spec", top_k = top_k)
    
def batch_search_evaluation_spec(database, queries: List[Dict[str, Any]], top_k: int = 10) -> List[List[Dict[str, Any]]]:
    """
    批量搜索评估规范
    
    Args:
        queries: 查询字典列表，每个字典可包含keywords_embedding和/或summary_embedding字段
        top_k: 每个查询返回的结果数量
        
    Returns:
        包含多个查询结果的列表，每个元素是对应查询的结果列表
    """
    return [search_evaluation_spec(query, top_k) for query in queries]

def retrieve_evidence_by_spec(database, spec: Dict, 
                                summary_weight: float = 0.3, 
                                keywords_weight: float = 0.7,
                                top_k: int = 5) -> list:
    """根据评估规范召回证明材料"""
    try:
        # 获取评估规范的向量
        
        query = {
            "keywords_embedding": spec["keywords_embedding"]
        }
        
        evideces = database.search_data(query = query, collection_type = "evidence", top_k = top_k)
        
        return evideces
    except Exception as e:
        print(f"Error retrieving evidence for spec: {str(e)}")
        return []
        
def dump_evaluation_spec(database) -> List[Dict[str, Any]]:
    """
    获取所有评估规范数据
    
    Returns:
        包含所有评估规范的列表
    """
    return database.dump(collection_type = "evaluation_spec")
        
