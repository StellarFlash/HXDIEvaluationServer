from typing import List, Dict, Optional
from tqdm import tqdm
import json
from datetime import datetime
import uuid
from app.models.evidence.item import EvidenceItem
from app.utils.maas_client import MaaSClient
from app.models.evidence.prompt import DEFAULT_SUMMARY_PROMPT

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
                evidence = EvidenceItem(
                    id=str(uuid.uuid4()),  # 使用UUID作为ID
                    created_at=datetime.now().isoformat(),  # 设置当前时间为创建时间
                    filename=item["filename"],
                    file_format=item["file_format"],
                    collection_time=datetime.strptime(item["collection_time"], "%Y-%m-%dT%H:%M:%S"),  # 将 ISO 格式字符串转换为 datetime
                    collector=item["collector"],
                    project=item["project"],
                    evidence_type=item["evidence_type"],
                    content=item["content"],
                    summary=item["summary"],
                    keywords=item["keywords"]
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
                
                evidence.keywords = response['keywords'].split(',')
            
            print(evidence.summary)
            print(evidence.keywords)
            
            # 获取摘要和关键词的向量
            evidence.summary_embedding = client.get_embeddings(evidence.summary)
            evidence.keywords_embedding = client.get_embeddings(' '.join(evidence.keywords))
            
            # 将证明材料插入Elasticsearch
            try:
                from app.db.database import database
                database.insert_evidence(evidence.to_dict(embeddings=True))
            except Exception as e:
                print(f"Error inserting evidence: {str(e)}")
                raise
    
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
    
    print("摘要向量：", summary_embedding[:5], "...")
    print("关键词向量：", keywords_embedding[:5], "...")
