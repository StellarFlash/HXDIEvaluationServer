from ast import List
import uuid
import json
from pymilvus import connections, Collection, utility
from pymilvus.orm import collection
from app.config.__init__ import get_config
from typing import List, Dict, Tuple, Any, TYPE_CHECKING, Optional

config = get_config()

class Database:
    def __init__(self):
        print("Initializing Milvus database...")

        # 初始化Milvus连接
        try:
            connections.connect(
                "default",
                host=config.MILVUS_HOST,
                port=config.MILVUS_PORT,
                user=config.MILVUS_USER,
                password=config.MILVUS_PASSWORD
            )
            if not connections.has_connection("default"):
                raise ConnectionError("无法连接到Milvus")
        except Exception as e:
            raise ConnectionError(f"Milvus连接失败: {str(e)}")
        
        self.drop_collection(collection_type="evidence")
        self.drop_collection(collection_type="evaluation_spec")
        # 初始化集合
        self.evidence_collection, self.evaluation_spec_collection = self._setup_collections()
        
        
        
        # 确保索引已创建
        if not self.evidence_collection.has_index():
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.evidence_collection.create_index(
                field_name="keywords_embedding",
                index_params=index_params,
                index_name="evidence_collection_keywords_index"
            )
            self.evidence_collection.create_index(
                field_name="summary_embedding",
                index_params=index_params,
                index_name="evidence_collection_summary_index"
            )
        
        if not self.evaluation_spec_collection.has_index():
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            self.evaluation_spec_collection.create_index(
                field_name="keywords_embedding",
                index_params=index_params,
                index_name="evaluation_spec_collection_keywords_index"
            )
            self.evaluation_spec_collection.create_index(
                field_name="summary_embedding",
                index_params=index_params,
                index_name="evaluation_spec_collection_summary_index"
            )
        
        self.evidence_collection.load()
        self.evaluation_spec_collection.load()

    def _create_collection(self, name: str) -> Collection:
        """创建新的Milvus集合"""
        from pymilvus import FieldSchema, CollectionSchema, DataType
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="keywords_embedding", dtype=DataType.FLOAT_VECTOR, dim=int(config.EMBEDDING_DIM)),
            FieldSchema(name="summary_embedding", dtype=DataType.FLOAT_VECTOR, dim=int(config.EMBEDDING_DIM)),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
        ]
        print(f"Creating collection {name} with embedding dimension {config.EMBEDDING_DIM}")
        schema = CollectionSchema(fields, description="")
        return Collection(name, schema)

    def _setup_collections(self) -> Tuple[Collection, Collection]:
        """初始化Milvus集合（证明材料和评估规范）"""
        def _init_collection(name: str) -> Collection:
            if utility.has_collection(name):
                print(f"{name} exists")
                collection = Collection(name)
                # 确保索引存在
                if not collection.has_index():
                    print(f"Creating index for {name}")
                    index_params = {
                        "metric_type": "L2",
                        "index_type": "IVF_FLAT",
                        "params": {"nlist": 128}
                    }
                    collection.create_index(
                        field_name="keywords_embedding", 
                        index_params=index_params,
                        index_name=f"{name}_keywords_index"
                    )
                    collection.create_index(
                        field_name="summary_embedding", 
                        index_params=index_params,
                        index_name=f"{name}_summary_index"
                    )
                return collection
            print(f"Creating new {name}")
            return self._create_collection(name)
            
        return _init_collection("evidence_collection"), _init_collection("evaluation_spec_collection")

    def store_data(self, data: Dict[str, Any], collection_type: str = "evidence") -> str:
        """存储数据到Milvus
        
        Args:
            data: 要存储的数据字典
            collection_type: 集合类型，可选值为"evidence"或"evaluation_spec"
        """
        # 准备数据
        data_id = data.get('id', str(uuid.uuid4()))
        keywords_embedding = data["keywords_embedding"]
        summary_embedding = data["summary_embedding"]
        metadata = data.get("metadata", "")
        
        entities = [[data_id], [keywords_embedding], [summary_embedding], [metadata]]
        
        # 根据collection_type选择目标集合
        if collection_type == "evidence":
            self.evidence_collection.insert(entities)
        elif collection_type == "evaluation_spec":
            self.evaluation_spec_collection.insert(entities)
        else:
            raise ValueError(f"无效的collection_type: {collection_type}")
        
        return data_id
               
    def search_data(self, query: Dict[str, Any], collection_type: str = "evidence", top_k: int = 10) -> List[Dict[str, Any]]:
        """在指定集合中搜索相似数据
        
        Args:
            query: 查询字典，可包含keywords_embedding和/或summary_embedding字段
            collection_type: 集合类型，可选值为"evidence"或"evaluation_spec"
            top_k: 返回结果数量
            
        Returns:
            包含匹配结果及其metadata的列表
        """
        
    
        # 获取目标集合
        if collection_type == "evidence":
            collection = self.evidence_collection
        elif collection_type == "evaluation_spec":
            collection = self.evaluation_spec_collection
        else:
            raise ValueError(f"无效的collection_type: {collection_type}")
            
        # 检查查询向量
        has_keywords = "keywords_embedding" in query
        has_summary = "summary_embedding" in query
        
        if not has_keywords and not has_summary:
            raise ValueError("查询中必须包含keywords_embedding或summary_embedding字段")
            
        # 设置搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        # 执行单字段或混合搜索
        if has_keywords and has_summary:
            # 混合搜索
            weights = query.get("weights", [0.5, 0.5])  # 默认权重
            if len(weights) != 2 or sum(weights) != 1.0:
                weights = [0.5, 0.5]  # 重置为默认权重
                
            # 执行混合搜索
            results = collection.search(
                data=[query["keywords_embedding"], query["summary_embedding"]],
                anns_field=["keywords_embedding", "summary_embedding"],
                param=search_params,
                limit=top_k,
                output_fields=["id", "metadata"],
                expr=None,
                consistency_level=None,
                partition_names=None,
                round_decimal=-1,
                weight=weights
            )
        else:
            # 单字段搜索
            search_field = "keywords_embedding" if has_keywords else "summary_embedding"
            search_vector = query[search_field]
            
            results = collection.search(
                data=[search_vector],
                anns_field=search_field,
                param=search_params,
                limit=top_k,
                output_fields=["id", "metadata"]
            )
        
        # 格式化结果
        return [{"id": hit.id, "metadata": json.loads(hit.entity.get("metadata")), "score": hit.score} 
                for hit in results[0]]

    
    def dump(self, collection_type: str = "evidence", limit: int = 1000) -> List[Dict[str, Any]]:
        """导出指定集合中的数据
        
        Args:
            collection_type: 集合类型，可选值为"evidence"或"evaluation_spec"
            limit: 最大返回记录数，默认为1000
            
        Returns:
            包含集合中所有文档的列表
        """
        # 获取目标集合
        if collection_type == "evidence":
            collection = self.evidence_collection
        elif collection_type == "evaluation_spec":
            collection = self.evaluation_spec_collection
        else:
            raise ValueError(f"无效的collection_type: {collection_type}")
            
        # 查询数据
        results = collection.query(
            expr="",
            output_fields=["id", "keywords_embedding", "summary_embedding", "metadata"],
            limit=limit
        )
        
        # 格式化结果
        return [{
            "id": item["id"],
            "keywords_embedding": item["keywords_embedding"],
            "summary_embedding": item["summary_embedding"],
            "metadata": json.loads(item["metadata"]) if item["metadata"] else {}
        } for item in results]
        
    def delete_all_data(self, collection_type: str = "evidence") -> None:
        """删除指定集合中的所有数据
        
        Args:
            collection_type: 集合类型，可选值为"evidence"或"evaluation_spec"
        """
        # 获取目标集合
        if collection_type == "evidence":
            collection = self.evidence_collection
        elif collection_type == "evaluation_spec":
            collection = self.evaluation_spec_collection
        else:
            raise ValueError(f"无效的collection_type: {collection_type}")
            
        # 删除所有数据
        collection.delete(expr="id in [\"\"]")
        
    def drop_collection(self, collection_type: str = "evidence") -> None:
        """彻底删除指定集合，包括数据结构和所有数据
        
        Args:
            collection_type: 集合类型，可选值为"evidence"或"evaluation_spec"
        """
        # 获取目标集合名称
        if collection_type == "evidence":
            collection_name = "evidence_collection"
        elif collection_type == "evaluation_spec":
            collection_name = "evaluation_spec_collection"
        else:
            raise ValueError(f"无效的collection_type: {collection_type}")
            
        # 检查集合是否存在
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"已删除集合 {collection_name}")
        else:
            print(f"集合 {collection_name} 不存在，无需删除")
