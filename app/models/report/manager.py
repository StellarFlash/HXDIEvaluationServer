from typing import List, Dict, Optional
from tqdm import tqdm
from datetime import datetime
from app.models.report.item import ReportItem
from app.models.report.prompt import DEFAULT_REPORT_PROMPT
from app.models.evidence.item import EvidenceItem
from app.models.evaluation_spec.item import EvaluationSpecItem
from app.utils.maas_client import MaaSClient
from app.db.database import database


class ReportManager:
    def __init__(self, evaluation_spec_index: str = None, evidence_index:str = None):
        self.reports: List[ReportItem] = []
        self.client = MaaSClient()
        self.evaluation_spec_index = database._get_index_name("evaluation_specifications") if evaluation_spec_index is None else evaluation_spec_index
        self.evidence_index = database._get_index_name("evidence_metadata") if evidence_index is None else evidence_index
        
    def get_report(self, index: int = 0) -> Optional[Dict]:
        """根据索引获取单条报告
        Args:
            index: 报告索引
        Returns:
            报告数据字典，如果索引无效返回None
        """
        if 0 <= index < len(self.reports):
            report = self.reports[index]
            return {
                "id": str(index),
                "evaluation_spec": report.spec.to_dict(embeddings=False),  # 保持字典格式
                "evidences": [e.to_dict(embeddings=False) for e in report.evidences],  # 保持字典格式
                "is_qualified": report.is_qualified,
                "conclusion": report.conclusion,
                "created_at": datetime.now().isoformat()
            }
        return None
        
    def get_reports(self, start: int = 0, end: int = 10) -> Dict:
        """获取报告列表
        Args:
            start: 起始索引（包含）
            end: 结束索引（不包含）
        Returns:
            包含报告列表和信息的字典
        """
        # 检查索引合法性
        start = max(0, start)
        end = min(len(self.reports), end)
        
        reports = self.reports[start:end]
        
        return {
            "reports": [self.get_report(i) for i in range(start, end)],
            "total": len(reports)
        }
        
    def export_reports_markdown(self) -> str:
        """导出所有报告为markdown表格格式
        Returns:
            markdown格式的表格字符串
        """
        if not self.reports:
            return ""
            
        # 表头
        markdown = "| 报告索引 | 评估项内容 | 证明材料 | 是否合格 | 结论 |\n"
        markdown += "| --- | --- | --- | --- | --- |\n"
        
        # 表格内容
        for i, report in enumerate(self.reports, 1):
            eval_content = report.spec.content[:50] + "..." if len(report.spec.content) > 50 else report.spec.content
            evidence_files = ", ".join([e.filename for e in report.evidences])
            markdown += f"| {i} | {eval_content} | {evidence_files} | {report.is_qualified} | {report.conclusion[:50]}... |\n"
            
        return markdown

    def generate_report(self) -> Dict:
        """生成完整报告
        Returns:
            返回包含运行状态和错误信息的字典
        """
        try:
            for report in tqdm(self.reports, desc="Processing Reports", unit="report"):
                self.generate_report_item_conclusion(report)
            return {
                "success": True,
                "message": "报告生成成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"报告生成失败: {str(e)}"
            }

    def generate_report_item_conclusion(self, report: ReportItem) -> None:
        """生成单个报告项的结论
        1. 召回证明材料
        2. 调用大模型生成评估结论
        3. 更新报告项
        """
        # 如果证明材料为空，先进行召回
        if not report.evidences:
            try:
                # 获取评估规范的向量
                spec = database.es.get(
                    index=self.evaluation_spec_index,
                    id=report.spec.id
                )['_source']

                # 使用向量相似度查询召回证明材料
                query = {
                    "size": 10,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": """
                                    cosineSimilarity(params.spec_summary, 'summary_embedding') +
                                    cosineSimilarity(params.spec_keywords, 'keywords_embedding')
                                """,
                                "params": {
                                    "spec_summary": spec['summary_embedding'],
                                    "spec_keywords": spec['keywords_embedding']
                                }
                            }
                        }
                    }
                }

                result = database.es.search(
                    index=self.evidence_index,
                    body=query
                )

                if result['hits']['total']['value'] > 0:
                    report.evidences = [EvidenceItem(**e['_source']) for e in result['hits']['hits']]
                else:
                    print("警告: 未找到相关证明材料")
            except Exception as e:
                print(f"警告: 召回证明材料失败: {str(e)}")
                return
        
        # 获取评估规范的摘要
        spec_summary = report.spec.summary
        
        # 获取证明材料的摘要
        evidence_summaries = "\n".join([e.summary for e in report.evidences])
        
        # 构建提示词
        prompt = DEFAULT_REPORT_PROMPT.format(
            spec_summary=spec_summary,
            evidence_summaries=evidence_summaries
        )
        
        # 调用大模型生成结论
        response = self.client.chat_completion(prompt, output_format='json')
        
        # 更新报告项
        report.is_qualified = response['is_qualified']
        report.conclusion = response['conclusion']

    def add_report_item(self, spec_id: str) -> ReportItem:
        """添加报告项
        1. 获取评估规范
        2. 召回相关证明材料
        3. 创建报告项
        """
        # 从数据库获取评估规范
        spec_data = database.es.get(
            index=self.evaluation_spec_index,
            id=spec_id
        )['_source']
        spec = EvaluationSpecItem(**spec_data)
        
        # 召回证明材料
        evidences = database.retrieve_evidence_by_spec(spec_id)['hits']['hits']
        
        # 创建报告项
        report_item = ReportItem(
            spec=spec,
            evidences=[EvidenceItem(**e['_source']) for e in evidences]
        )
        
        self.reports.append(report_item)
        return report_item
    
    def init_test_data(self) -> None:
        """使用测试数据初始化报告管理器
        
        1. 从测试索引中获取所有评估规范ID
        2. 为每个评估规范创建报告项
        3. 生成完整的测试报告
        """
        try:
            # 获取所有spec_id
            print(f"正在查询索引 {self.evaluation_spec_index}...")
            # 先尝试简单的count查询
            try:
                count = database.es.count(index=self.evaluation_spec_index)
                print(f"索引 {self.evaluation_spec_index} 中的文档数量: {count['count']}")
            except Exception as e:
                print(f"Count查询失败: {str(e)}")
            
            # 执行搜索查询
            response = database.es.search(
                index=self.evaluation_spec_index,
                body={"query": {"match_all": {}}},
                size=10  # 限制返回结果数量
            )
            print(f"查询结果: {response}")
            
            if not response['hits']['hits']:
                print(f"警告: 索引 {self.evaluation_spec_index} 中没有找到任何评估规范")
                # 尝试列出所有索引
                try:
                    indices = database.es.cat.indices(format="json")
                    print(f"当前所有索引: {indices}")
                except Exception as e:
                    print(f"获取索引列表失败: {str(e)}")
                return
                
            spec_ids = [hit['_id'] for hit in response['hits']['hits']]
            print(f"找到 {len(spec_ids)} 个评估规范ID: {spec_ids}")
            
            # 为每个spec_id添加报告项
            for spec_id in spec_ids:
                try:
                    print(f"正在为评估规范 {spec_id} 创建报告项...")
                    report_item = self.add_report_item(spec_id)
                    print(f"成功为评估规范 {spec_id} 创建报告项")
                    print(f"报告项详情: spec={report_item.spec.id}, evidences={len(report_item.evidences)}")
                except Exception as e:
                    print(f"为评估规范 {spec_id} 创建报告项失败: {str(e)}")
                    
            print(f"初始化完成，当前报告总数: {len(self.reports)}")
        except Exception as e:
            print(f"初始化测试数据失败: {str(e)}")

if __name__ == "__main__":
    # 初始化ReportManager
    manager = ReportManager()
    
    # 获取所有spec_id
    response = database.es.search(
        index= "test_evaluation_specifications",
        body={"query": {"match_all": {}}}
    )
    spec_ids = [hit['_id'] for hit in response['hits']['hits']]
    
    # 为每个spec_id添加报告项
    for i, spec_id in enumerate(spec_ids, 1):
        print(f"正在处理第{i}个报告项...")
        report_item = manager.add_report_item(spec_id)
        print(f"报告项{i}创建成功，包含{len(report_item.evidences)}条证明材料")
    
    # 生成报告
    print("开始生成报告...")
    manager.generate_report()
    
    # 打印结果
    print("\n报告生成结果：")
    for i, report in enumerate(manager.reports, 1):
        print(f"\n报告项{i}:")
        print(f"评估结论: {report.conclusion}")
        print(f"是否合格: {report.is_qualified}")
