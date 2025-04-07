from typing import Dict, Any, List
import uuid
import json

from .database import Database


    
def store_evidence(database, evidence: Dict[str, Any]) -> str:
    """存储证明材料"""
    evidence_id = str(uuid.uuid4())
    evidence_data = {
        'id': evidence_id,
        'keywords_embedding': evidence.get('keywords_embedding'),
        'summary_embedding': evidence.get('summary_embedding'),
        'metadata': json.dumps(evidence)
    }
    return database.store_data(evidence_data, collection_type="evidence")
    
def search_evidence(database, query: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    搜索证明材料
    
    Args:
        query: 查询字典，可包含keywords_embedding和/或summary_embedding字段
        top_k: 返回的结果数量
        
    Returns:
        匹配的证明材料列表
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
    return database.search_data(query = combined_embedding, evidence_type="evidence", top_k = top_k)
    
def batch_search_evidence(database, queries: List[Dict[str, Any]], top_k: int = 10) -> List[List[Dict[str, Any]]]:
    """
    批量搜索证明材料
    
    Args:
        queries: 查询字典列表，每个字典可包含keywords_embedding和/或summary_embedding字段
        top_k: 每个查询返回的结果数量
        
    Returns:
        包含多个查询结果的列表，每个元素是对应查询的结果列表
    """
    return [search_evidence(query, top_k) for query in queries]