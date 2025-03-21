from app.db.database import Database

def test_evidence_similarity():
    """测试证明材料之间的召回效果"""
    db = Database(test_mode=True)
    
    # 获取所有证明材料
    result = db.es.search(
        index="test_evidence",
        body={"size": 100, "query": {"match_all": {}}}
    )
    
    if result['hits']['total']['value'] == 0:
        print("没有可用的证明材料")
        return
        
    # 选择第一个证明材料作为查询
    query_evidence = result['hits']['hits'][0]
    print(f"使用证明材料进行查询: {query_evidence['_id']} - {query_evidence['_source']['filename']}")
    
    # 查询相似证明材料
    query = {
        "size": 5,
        "query": {
            "bool": {
                "must_not": [{"term": {"_id": query_evidence['_id']}}],  # 排除自身
                "should": [
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": """
                                    (0.5 * cosineSimilarity(params.evidence_summary, 'summary_embedding')) +
                                    (0.5 * cosineSimilarity(params.evidence_keywords, 'keywords_embedding'))
                                """,
                                "params": {
                                    "evidence_summary": query_evidence['_source']['summary_embedding'],
                                    "evidence_keywords": query_evidence['_source']['keywords_embedding']
                                }
                            }
                        }
                    },
                    {
                        "match": {
                            "keywords": {
                                "query": " ".join(query_evidence['_source']['keywords']),
                                "operator": "or",
                                "minimum_should_match": "30%"
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
    }
    
    result = db.es.search(
        index="test_evidence",
        body=query
    )
    
    if result['hits']['total']['value'] > 0:
        print("找到相似证明材料:")
        for hit in result['hits']['hits']:
            print(f"ID: {hit['_id']}, 文件名: {hit['_source']['filename']}, 得分: {hit['_score']}")
    else:
        print("未找到相似证明材料")

if __name__ == "__main__":
    test_evidence_similarity()
