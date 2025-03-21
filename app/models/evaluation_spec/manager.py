from typing import List, Dict, Optional
from tqdm import tqdm
import json
from app.models.evaluation_spec.item import EvaluationSpecItem
from app.utils.maas_client import MaaSClient
from app.models.evaluation_spec.prompt import DEFAULT_SUMMARY_PROMPT

class EvaluationSpecManager:
    """评估规范管理类"""
    
    def __init__(self):
        self.specs: List[EvaluationSpecItem] = []
        self.load_from_json()
        self.generate_index()
        
    def load_from_directory(self, dir_path: str) -> None:
        """从目录加载所有评估规范"""
        # TODO: 实现目录加载逻辑
        pass
        
    def load_from_json(self, file_path: str = "data/evaluation_spec.json") -> None:
        """
        从json文件加载所有评估规范
        :param file_path: JSON 文件路径
        """
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        # 转换为 EvaluationSpecItem 对象
            for item in data:
                spec = EvaluationSpecItem(
                    primary_title=item["primary_title"],
                    secondary_title=item.get("secondary_title"),
                    tertiary_title=item.get("tertiary_title"),
                    content=item["content"],
                    evaluation_guidelines=item["evaluation_guidelines"],
                    keywords=item["keywords"],
                    summary=item["summary"]
                )
                self.specs.append(spec)
            
            print(f"Loaded {len(self.specs)} evaluation specs from {file_path}")
        except FileNotFoundError:
            print(f"Error: File not found at path {file_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in file {file_path}")
        except Exception as e:
            print(f"Error loading evaluation specs: {e}")
    
    def generate_index(self, summary_prompt: str = None) -> None:
        """生成评估规范索引
        Args:
            summary_prompt: 可选的自定义提示词模板，如果未提供则使用默认模板
        """
        
        if summary_prompt is None:
            summary_prompt = DEFAULT_SUMMARY_PROMPT
        
        client = MaaSClient()
        
        for spec in tqdm(self.specs, desc="Processing EvaluationSpec", unit="spec"):
            if spec.summary == "" or spec.keywords == []:
                # 构建提示词
                prompt = summary_prompt.format(
                    primary_title=spec.primary_title,
                    secondary_title=spec.secondary_title,
                    tertiary_title=spec.tertiary_title,
                    content=spec.content,
                    guidelines="\n".join(spec.evaluation_guidelines)
                )
                # print(prompt)
                # 调用大模型接口，指定JSON格式输出
                response = client.chat_completion(prompt, output_format='json')
                
                # 更新摘要和关键词
                spec.summary = response['summary']
                spec.keywords = response['keywords'].split(',')
            
            print(spec.summary)
            print(spec.keywords)
            
            # 获取摘要和关键词的向量
            spec.summary_embedding = client.get_embeddings(spec.summary)
            spec.keywords_embedding = client.get_embeddings(' '.join(spec.keywords))
            
            # 将评估规范插入Elasticsearch
            try:
                from app.db.database import database
                database.insert_evaluation_spec(spec.to_dict(embeddings=True))
            except Exception as e:
                print(f"Error inserting evaluation spec: {str(e)}")
                raise
            
    # EvaluationSpecManager新增方法
    def get_evaluation_spec(self, index: int) -> Optional[Dict]:
        """根据索引获取单个评估规范
        Args:
            index: 评估规范索引
        Returns:
            评估规范数据字典，如果索引无效返回None
        """
        if 0 <= index < len(self.specs):
            return self.specs[index].to_dict(embeddings=False)
        return None

    def get_evaluation_specs(self, start: int = 0, end: int = 10) -> Dict:
        """获取分页评估规范列表
        Args:
            start: 起始索引（包含）
            end: 结束索引（不包含）
        Returns:
            包含评估规范列表和分页信息的字典
        """
        # 检查索引合法性
        start = max(0, start)
        end = min(len(self.specs), end)
        
        specs = self.specs[start:end]
        
        return {
            "evaluation_specs": [spec.to_dict(embeddings=False) for spec in specs],
            "total": len(specs)
        }

if __name__ == "__main__":
    # 测试代码
    test_spec = EvaluationSpecItem(
        primary_title="项目评估",
        secondary_title="财务评估",
        tertiary_title="季度报告",
        content="2023年Q4财务报告，显示收入增长20%，利润增长15%",
        evaluation_guidelines=[
            "评估收入增长情况",
            "评估利润增长情况",
            "分析增长原因"
        ],
        keywords=[]
    )
    
    # 创建管理器实例
    manager = EvaluationSpecManager()
    manager.specs.append(test_spec)
    
    # 测试摘要和关键词生成
    print("生成前：")
    print(f"摘要: {test_spec.summary}")
    print(f"关键词: {test_spec.keywords}")
    
    manager.generate_index()
    
    print("\n生成后：")
    print(f"摘要: {test_spec.summary}")
    print(f"关键词: {test_spec.keywords}")
    # 类型断言消除Pylint误报
    test_spec: EvaluationSpecItem
    summary_embedding: List[float] = test_spec.summary_embedding or []
    keywords_embedding: List[float] = test_spec.keywords_embedding or []
    print(f"摘要向量: {test_spec.summary_embedding[:5]} ...")
    print(f"关键词向量: {test_spec.keywords_embedding[:5]} ...")
