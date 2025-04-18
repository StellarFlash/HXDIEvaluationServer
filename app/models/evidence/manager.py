from typing import List, Dict, Optional
from tqdm import tqdm
import json
from datetime import datetime
import uuid
from app.models.evidence.item import EvidenceItem
from app.utils.maas_client import MaaSClient
from app.models.evidence.prompt import DEFAULT_SUMMARY_PROMPT
from app.database import get_database, store_evidence

database = get_database()  # 获取数据库实例

class EvidenceManager:
    """证明材料管理类"""
    
    def __init__(self):
        self.evidences: List[EvidenceItem] = []
        print("Initializing EvidenceManager...")
        self.load_from_json()
        print(f"Loaded {len(self.evidences)} evidences")
        self.generate_index()
        print("EvidenceManager initialization completed")
        
    def load_from_json(self, file_path: str = "data/evidence.json") -> None:
        """
        从 JSON 文件加载所有证明材料
        :param file_path: JSON 文件路径
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 转换为 EvidenceItem 对象
            for idx, item in enumerate(data):
                # 为每个字段提供默认值，防止JSON数据缺失导致异常
                evidence = EvidenceItem(
                    id=str(uuid.uuid4()),  # 使用UUID作为ID
                    created_at=datetime.now().isoformat(),  # 设置当前时间为创建时间
                    filename=item.get("filename", "unknown"),
                    file_format=item.get("file_format", "unknown"),
                    collection_time=datetime.strptime(item.get("collection_time", "1970-01-01T00:00:00.000000"), "%Y-%m-%dT%H:%M:%S.%f"),
                    collector=item.get("collector", "unknown"),
                    project=item.get("project", "default"),
                    evidence_type=item.get("evidence_type", "unknown"),
                    content=item.get("content", ""),
                    summary=item.get("summary", ""),
                    keywords=item.get("keywords", [])
                )
                self.evidences.append(evidence)

            print(f"Loaded {len(self.evidences)} evidences from {file_path}")
        except FileNotFoundError:
            print(f"Error: File not found at path {file_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in file {file_path}")
        except KeyError as e:
            print(f"Error: Missing key in JSON data - {e}")
        except Exception as e:
            print(f"Unexpected error loading evidences: {e}")
        
    def save_to_json(self, file_path: str = "data/evidence.json") -> None:
        """将证明材料保存到json文件
        Args:
            file_path: JSON 文件路径
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([evidence.to_dict(embeddings=False) for evidence in self.evidences], f, ensure_ascii=False, indent=4)
            print(f"Saved {len(self.evidences)} evidences to {file_path}")
        except Exception as e:
            print(f"Error saving evidences: {e}")

    def generate_index(self, summary_prompt: Optional[str] = None) -> None:
        """生成证明材料索引"""
        
        if summary_prompt is None:
            summary_prompt = DEFAULT_SUMMARY_PROMPT
            
        client = MaaSClient()
        
        for evidence in tqdm(self.evidences, desc="Processing evidences", unit="evidence"):
            if evidence.summary == "" or evidence.keywords == []:
                # 构建提示词
                prompt = summary_prompt.format(
                    filename=evidence.filename,
                    file_format=evidence.file_format,
                    collection_time=evidence.collection_time,
                    collector=evidence.collector,
                    project=evidence.project,
                    evidence_type=evidence.evidence_type,
                    content=evidence.content
                )
                
                # 调用大模型接口，指定JSON格式输出
                response = client.chat_completion(prompt, output_format='json')
                
                # 更新摘要和关键词
                evidence.summary = response['summary']
                
                # 处理keywords，兼容字符串和列表
                keywords = response['keywords']
                evidence.keywords = keywords.split(',') if isinstance(keywords, str) else keywords
            
            # 获取摘要和关键词的向量
            evidence.summary_embedding = client.get_embeddings(evidence.summary)
            evidence.keywords_embedding = client.get_embeddings(' '.join(evidence.keywords))
            
            # 将证明材料插入Elasticsearch
            try:
                evidence_dict = evidence.to_dict(embeddings=True)
                # 确保embedding是列表格式
                if isinstance(evidence_dict.get("keywords_embedding"), dict):
                    evidence_dict["keywords_embedding"] = evidence_dict["keywords_embedding"]["vector"]
                if isinstance(evidence_dict.get("summary_embedding"), dict):
                    evidence_dict["summary_embedding"] = evidence_dict["summary_embedding"]["vector"]
                
                store_evidence(database = database, evidence = evidence_dict)
            except Exception as e:
                print(f"Error inserting evidence: {str(e)}")
                raise
        
        # 保存更新后的证明材料到JSON文件
        self.save_to_json()
    
    # EvidenceManager新增方法
    def get_evidence(self, index: int) -> Optional[Dict]:
        """根据索引获取单个证明材料
        Args:
            index: 证明材料索引
        Returns:
            证明材料数据字典，如果索引无效返回None
        """
        if 0 <= index < len(self.evidences):
            return self.evidences[index].to_dict(embeddings=False)
        return None

    def get_evidences(self, start: int = 0, end: int = 10) -> Dict:
        """获取分页证明材料列表
        Args:
            start: 起始索引（包含）
            end: 结束索引（不包含）
        Returns:
            包含证明材料列表和分页信息的字典
        """
        # 检查索引合法性
        start = max(0, start)
        end = min(len(self.evidences), end)
        
        evidences = self.evidences[start:end]
        
        return {
            "evidences": [evidence.to_dict(embeddings=False) for evidence in evidences],
            "total": len(evidences)
        }
    
if __name__ == "__main__":
    # 测试代码
    from datetime import datetime
    
    # 创建测试数据
    test_evidence = EvidenceItem(
        filename="test_evidence.pdf",
        file_format="PDF",
        collection_time=datetime.now(),
        collector="张三",
        project="项目A",
        evidence_type="财务报告",
        content="2023年Q4财务报告，显示收入增长20%，利润增长15%"
    )
    
    # 创建管理器实例
    manager = EvidenceManager()
    manager.evidences.append(test_evidence)
    # 测试摘要生成
    print("生成摘要前：", test_evidence.summary, test_evidence.keywords)
    manager.generate_index()
    print("生成摘要后：", test_evidence.summary, test_evidence.keywords)
    # 类型断言消除Pylint误报
    test_evidence: EvidenceItem
    summary_embedding: List[float] = test_evidence.summary_embedding or []
    keywords_embedding: List[float] = test_evidence.keywords_embedding or []
    
if __name__ == "__main__":
    # 测试代码
    from datetime import datetime
    
    # 创建测试数据
    test_evidence = EvidenceItem(
        filename="test_evidence.pdf",
        file_format="PDF",
        collection_time=datetime.now(),
        collector="张三",
        project="项目A",
        evidence_type="财务报告",
        content="2023年Q4财务报告，显示收入增长20%，利润增长15%"
    )
    
    # 创建管理器实例
    manager = EvidenceManager()
    manager.evidences.append(test_evidence)
    # 测试摘要生成
    print("生成摘要前：", test_evidence.summary, test_evidence.keywords)
    manager.generate_index()
    print("生成摘要后：", test_evidence.summary, test_evidence.keywords)
    # 类型断言消除Pylint误报
    test_evidence: EvidenceItem
    summary_embedding: List[float] = test_evidence.summary_embedding or []
