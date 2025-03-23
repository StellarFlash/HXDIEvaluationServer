import uuid
from elasticsearch import Elasticsearch
from app.config.config import Config
from typing import Dict, Any, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from app.config.config import Config as ConfigType
    config: ConfigType
else:
    config = Config

class Database:
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        print(config.__dict__)
        self.es = Elasticsearch(
            hosts=[{"host": config.ES_HOST, "port": config.ES_PORT, "scheme": getattr(config, "ES_SCHEME", "https")}],
            http_auth=(config.ES_USER, config.ES_PASSWORD) if config.ES_USER and config.ES_PASSWORD else None,
            verify_certs=False,  # 禁用证书验证
            ssl_show_warn=False  # 禁用SSL警告
        )
        
        # 清理评估规范索引
        eval_spec_index = self._get_index_name("evaluation_specifications")
        if self.es.indices.exists(index=eval_spec_index):
            self.es.delete_by_query(
                index=eval_spec_index,
                body={"query": {"match_all": {}}}
            )
        
    def _get_index_name(self, base_name: str) -> str:
        """根据test_mode获取索引名称"""
        # 如果索引名已经以'test_'开头，则直接返回
        if base_name.startswith('test_'):
            return base_name
        return f"test_{base_name}" if self.test_mode else base_name

    def store_evidence(self, evidence: Dict[str, Any]) -> str:
        """存储证明材料
        Args:
            evidence: 证明材料字典
        Returns:
            存储的文档ID
        """
        evidence_id = str(uuid.uuid4())
        self.es.index(
            index=self._get_index_name("evidence_metadata"),
            id=evidence_id,
            body=evidence
        )
        return evidence_id

    def store_evaluation_spec(self, spec: Dict[str, Any]) -> str:
        """存储评估规范
        Args:
            spec: 评估规范字典
        Returns:
            存储的文档ID
        """
        spec_id = str(uuid.uuid4())
        self.es.index(
            index=self._get_index_name("evaluation_specifications"),
            id=spec_id,
            body=spec
        )
        return spec_id

    def search_evidence(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """搜索证明材料
        支持以下查询方式：
        1. 向量相似度查询：使用summary_embedding或keywords_embedding字段
        2. 关键词匹配查询：使用keywords字段
        3. 混合查询：结合向量和关键词查询

        Args:
            query: Elasticsearch查询DSL，例如：
                {
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'summary_embedding') + 1.0",
                                "params": {"query_vector": [0.1, 0.2, ...]}
                            }
                        }
                    }
                }

        Returns:
            包含命中文档的查询结果，格式：
            {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_id": "1",
                            "_score": 0.95,
                            "_source": {...}
                        }
                    ]
                }
            }
        """
        return self.es.search(
            index=self._get_index_name("evidence_metadata"),
            body=query
        )

    def search_evaluation_spec(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """搜索评估规范
        支持以下查询方式：
        1. 向量相似度查询：使用summary_embedding或keywords_embedding字段
        2. 关键词匹配查询：使用keywords字段
        3. 混合查询：结合向量和关键词查询

        Args:
            query: Elasticsearch查询DSL，例如：
                {
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'summary_embedding') + 1.0",
                                "params": {"query_vector": [0.1, 0.2, ...]}
                            }
                        }
                    }
                }

        Returns:
            包含命中文档的查询结果，格式：
            {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_id": "1",
                            "_score": 0.95,
                            "_source": {...}
                        }
                    ]
                }
            }
        """
        return self.es.search(
            index=self._get_index_name("evaluation_specifications"),
            body=query
        )

    def retrieve_evidence_by_spec(
        self,
        spec_id: str,
        summary_weight: float = 0.3,
        keywords_weight: float = 0.7,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """根据评估规范召回证明材料
        使用摘要向量和关键词向量进行召回，支持权重配置

        Args:
            spec_id: 评估规范ID
            summary_weight: 摘要向量权重，默认0.3
            keywords_weight: 关键词向量权重，默认0.7
            top_k: 返回的证明材料数量，默认5

        Returns:
            包含命中文档的查询结果，格式：
            {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_id": "1",
                            "_score": 0.95,
                            "_source": {...}
                        }
                    ]
                }
            }
        """
        try:
            # 获取评估规范的向量
            spec = self.es.get(
                index=self._get_index_name("evaluation_specifications"),
                id=spec_id
            )['_source']

            query = {
                "size": top_k,
                "min_score": 0.3,  # 设置相似度阈值
                "query": {
                    "bool": {
                        "should": [
                            {
                                "script_score": {
                                    "query": {"match_all": {}},
                                    "script": {
                                        "source": """
                                            (params.summary_weight * cosineSimilarity(params.spec_summary, 'summary_embedding')) +
                                            (params.keywords_weight * cosineSimilarity(params.spec_keywords, 'keywords_embedding'))
                                        """,
                                        "params": {
                                            "spec_summary": spec['summary_embedding'],
                                            "spec_keywords": spec['keywords_embedding'],
                                            "summary_weight": summary_weight,
                                            "keywords_weight": keywords_weight
                                        }
                                    }
                                }
                            },
                            {
                                "match": {
                                    "keywords": {
                                        "query": " ".join(spec['keywords']),
                                        "operator": "or",
                                        "minimum_should_match": "50%"
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                }
            }

            return self.es.search(
                index=self._get_index_name("test_evidence"),
                body=query
            )
        except Exception as e:
            print(f"Error retrieving evidence for spec {spec_id}: {str(e)}")
            return {"hits": {"total": {"value": 0}, "hits": []}}

    def init_db(self) -> None:
        """初始化测试数据库"""
        print("Initializing test database...")
        
        # 需要创建的索引及其配置
        indices = {
            self._get_index_name("evidence_metadata"): {
                "mappings": {
                    "properties": {
                        "id": { "type": "keyword" },
                        "url": { "type": "keyword" },
                        "filename": { "type": "keyword" },
                        "format": { "type": "keyword" },
                        "type": { "type": "keyword" },
                        "collection_time": { "type": "date" },
                        "collector": { "type": "keyword" },
                        "operator": { "type": "keyword" },
                        "project": { "type": "keyword" },
                        "content": { "type": "text" },
                        "keywords": { "type": "keyword" },
                        "summary_embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        },
                        "keywords_embedding": {
                            "type": "dense_vector", 
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        },
                        "summary": {
                            "type": "text"
                        }
                    }
                }
            },
            self._get_index_name("evidence_metadata_summary"): {
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        }
                    }
                }
            },
            self._get_index_name("evidence_metadata_keywords"): {
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        }
                    }
                }
            },
            self._get_index_name("evaluation_specifications"): {
                "mappings": {
                    "properties": {
                        "id": { "type": "keyword" },
                        "title_level_1": { "type": "keyword" },
                        "title_level_2": { "type": "keyword" },
                        "title_level_3": { "type": "keyword" },
                        "content": { "type": "text" },
                        "comments": { "type": "text" },
                        "keywords": { "type": "keyword" },
                        "summary_embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        },
                        "keywords_embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        },
                        "summary": {
                            "type": "text"
                        }
                    }
                }
            },
            self._get_index_name("evaluation_specifications_summary"): {
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        }
                    }
                }
            },
            self._get_index_name("evaluation_specifications_keywords"): {
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1024,
                            "index": "true",
                            "similarity": "cosine"
                        }
                    }
                }
            }
        }
        
        # 创建缺失的索引
        for index_name, index_body in indices.items():
            if not self.es.indices.exists(index=index_name):
                try:
                    print(f"Creating index {index_name}...")
                    self.es.indices.create(index=index_name, body=index_body)
                    print(f"Successfully created index {index_name}")
                except Exception as e:
                    print(f"Failed to create index {index_name}: {str(e)}")
            else:
                print(f"Index {index_name} already exists, skipping creation")

    def insert_evaluation_spec(self, spec: Dict[str, Any]) -> str:
        """插入评估规范到测试数据库
        Args:
            spec: 评估规范字典，必须包含summary_embedding和keywords_embedding字段
        Returns:
            存储的文档ID
        """
        if 'summary_embedding' not in spec or 'keywords_embedding' not in spec:
            raise ValueError("spec must contain both summary_embedding and keywords_embedding")
            
        print(f"Inserting evaluation spec {spec.get('id')}...")
        # 使用bulk API同时插入主索引和向量索引
        actions = [
            {"index": {"_index": self._get_index_name("evaluation_specifications"), "_id": spec.get("id")}},
            spec,
            {"index": {"_index": self._get_index_name("evaluation_specifications_summary"), "_id": spec.get("id")}},
            {"embedding": spec["summary_embedding"]},
            {"index": {"_index": self._get_index_name("evaluation_specifications_keywords"), "_id": spec.get("id")}},
            {"embedding": spec["keywords_embedding"]}
        ]
        
        response = self.es.bulk(body=actions)
        if response['errors']:
            print(f"Failed to insert evaluation spec {spec.get('id')}: {response}")
            raise RuntimeError(f"Failed to insert evaluation spec: {response}")
            
        # 检查每个插入操作的结果
        for item in response['items']:
            index = item['index']['_index']
            status = item['index']['status']
            print(f"Insert result - index: {index}, status: {status}")
            
        print(f"Successfully inserted evaluation spec {spec.get('id')}")
        return response['items'][0]['index']['_id']

    def insert_evidence(self, evidence: Dict[str, Any]) -> str:
        """插入证明材料到测试数据库
        Args:
            evidence: 证明材料字典，必须包含summary_embedding和keywords_embedding字段
        Returns:
            存储的文档ID
        """
        if 'summary_embedding' not in evidence or 'keywords_embedding' not in evidence:
            raise ValueError("evidence must contain both summary_embedding and keywords_embedding")
            
        # 使用bulk API同时插入主索引和向量索引
        actions = [
            {"index": {"_index": self._get_index_name("evidence"), "_id": evidence.get("id")}},
            evidence,
            {"index": {"_index": self._get_index_name("evidence_summary"), "_id": evidence.get("id")}},
            {"embedding": evidence["summary_embedding"]},
            {"index": {"_index": self._get_index_name("evidence_keywords"), "_id": evidence.get("id")}},
            {"embedding": evidence["keywords_embedding"]}
        ]
        
        response = self.es.bulk(body=actions)
        if response['errors']:
            raise RuntimeError(f"Failed to insert evidence: {response}")
            
        return response['items'][0]['index']['_id']

database = Database(test_mode=True)
es_client = database.es
