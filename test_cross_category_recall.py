from app.db.database import Database

def test_cross_category_recall():
    """测试跨类双向召回效果"""
    db = Database(test_mode=True)
    
    # 测试从评估规范到证明材料的召回
    print("\n测试从评估规范到证明材料的召回:")
    test_spec_to_evidence(db)
    
    # 测试从证明材料到评估规范的召回
    print("\n测试从证明材料到评估规范的召回:")
    test_evidence_to_spec(db)

def test_spec_to_evidence(db):
    """从评估规范到证明材料的召回测试"""
    # 获取评估规范
    result = db.es.search(
        index="test_evaluation_specifications",
        body={"size": 1, "query": {"match_all": {}}}
    )
    
    if result['hits']['total']['value'] == 0:
        print("没有可用的评估规范")
        return
        
    # 选择第一个评估规范作为查询
    query_spec = result['hits']['hits'][0]
    print(f"使用评估规范进行查询: {query_spec['_id']} - {query_spec['_source']['primary_title']}")
    
    # 使用database中的方法召回证明材料
    result = db.retrieve_evidence_by_spec(query_spec['_id'])
    
    if result['hits']['total']['value'] > 0:
        print("找到相似证明材料:")
        for hit in result['hits']['hits']:
            print(f"ID: {hit['_id']}, 文件名: {hit['_source']['filename']}, 得分: {hit['_score']}")
    else:
        print("未找到相似证明材料")

def test_evidence_to_spec(db):
    """从证明材料到评估规范的召回测试"""
    # 获取证明材料
    result = db.es.search(
        index="test_evidence",
        body={"size": 1, "query": {"match_all": {}}}
    )
    
    if result['hits']['total']['value'] == 0:
        print("没有可用的证明材料")
        return
        
    # 选择第一个证明材料作为查询
    query_evidence = result['hits']['hits'][0]
    print(f"使用证明材料进行查询: {query_evidence['_id']} - {query_evidence['_source']['filename']}")
    
    # 查询相似评估规范
    query = {
        "size": 5,
        "query": {
            "bool": {
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
        index="test_evaluation_specifications",
        body=query
    )
    
    if result['hits']['total']['value'] > 0:
        print("找到相似评估规范:")
        for hit in result['hits']['hits']:
            print(f"ID: {hit['_id']}, 标题: {hit['_source']['primary_title']}, 得分: {hit['_score']}")
    else:
        print("未找到相似评估规范")

if __name__ == "__main__":
    test_cross_category_recall()
