from app.db.database import Database

def test_similarity():
    """测试同类数据之间的召回效果"""
    db = Database(test_mode=True)
    
    # 获取所有评估规范
    result = db.es.search(
        index="test_evaluation_specifications",
        body={"size": 100, "query": {"match_all": {}}}
    )
    
    if result['hits']['total']['value'] == 0:
        print("没有可用的评估规范")
        return
        
    # 选择第一个评估规范作为查询
    query_spec = result['hits']['hits'][0]
    print(f"使用评估规范进行查询: {query_spec['_id']} - {query_spec['_source']['primary_title']}")
    
    # 查询同类数据
    query = {
        "size": 5,
        "query": {
            "bool": {
                "must_not": [{"term": {"_id": query_spec['_id']}}],  # 排除自身
                "should": [
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": """
                                    (0.5 * cosineSimilarity(params.spec_summary, 'summary_embedding')) +
                                    (0.5 * cosineSimilarity(params.spec_keywords, 'keywords_embedding'))
                                """,
                                "params": {
                                    "spec_summary": query_spec['_source']['summary_embedding'],
                                    "spec_keywords": query_spec['_source']['keywords_embedding']
                                }
                            }
                        }
                    },
                    {
                        "match": {
                            "keywords": {
                                "query": " ".join(query_spec['_source']['keywords']),
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
    test_similarity()
