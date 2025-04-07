from typing import List, Dict, Optional
from openai import embeddings
from tqdm import tqdm
from datetime import datetime
import uuid
from app.models.report.item import ReportItem
from app.models.report.prompt import DEFAULT_REPORT_PROMPT
from app.models.evidence.item import EvidenceItem
from app.models.evaluation_spec.item import EvaluationSpecItem
from app.utils.maas_client import MaaSClient
from app.database import get_database, search_evaluation_spec, retrieve_evidence_by_spec, dump_evaluation_spec
import app.config as config


database = get_database()  # 获取数据库实例

class ReportManager:
    def __init__(self, evaluation_spec_index: str = None, evidence_index:str = None):
        self.reports: List[ReportItem] = []
        self.client = MaaSClient()
        
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
                "id": str(uuid.uuid4()),
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
                # 使用向量相似度查询召回证明材料
                evidences = retrieve_evidence_by_spec(
                    database = database,
                    spec=report.spec.to_dict(embeddings=True)
                )
                
                if evidences:
                    report.evidences = [EvidenceItem(**e) for e in evidences]
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

    def add_report_item(self, spec: str) -> ReportItem:
        """添加报告项
        2. 召回相关证明材料
        3. 创建报告项
        """
        print(spec.keys())
        # 召回证明材料
        spec=EvaluationSpecItem(
            id=spec['id'],
            primary_title = spec['metadata']['primary_title'],
            secondary_title = spec['metadata']['secondary_title'],
            tertiary_title = spec['metadata']['tertiary_title'],
            content = spec['metadata']['content'],
            evaluation_guidelines = spec['metadata']['evaluation_guidelines'],
            keywords = spec['metadata'].get('keywords', []),
            keywords_embedding = spec['keywords_embedding'],
            summary = spec['metadata'].get('summary', ""),
            summary_embedding = spec['summary_embedding']
        )
        
        
        evidences_dict_list = retrieve_evidence_by_spec(database = database, spec = spec.to_dict(embeddings = True))
        
        evidence_item_list = []
        for evidece_dict in evidences_dict_list:
            evidence_item = EvidenceItem(
                id = evidece_dict['metadata']['id'],
                filename = evidece_dict['metadata']['filename'],
                file_format = evidece_dict['metadata']['file_format'],
                collection_time = evidece_dict['metadata']['collection_time'],
                collector = evidece_dict['metadata']['collector'],
                project = evidece_dict['metadata']['project'],
                evidence_type = evidece_dict['metadata']['evidence_type'],
                content = evidece_dict['metadata']['content'],
                keywords = evidece_dict['metadata'].get('keywords', []),
                keywords_embedding = evidece_dict['metadata']['keywords_embedding'],
                summary = evidece_dict['metadata'].get('summary', ""),
                summary_embedding = evidece_dict['metadata']['summary_embedding']
            )
            evidence_item_list.append(evidence_item)
            
        print(evidence_item_list[0].to_dict(embeddings = False))
        # 创建报告项
        report_item = ReportItem(spec = spec, evidences=evidence_item_list)
        
        self.reports.append(report_item)
        return report_item
    
    def load_data(self) -> Dict:
        """使用测试数据初始化报告管理器
        
        1. 从测试索引中获取所有评估规范ID
        2. 为每个评估规范创建报告项
        3. 生成完整的测试报告
        
        Returns:
            包含操作结果的字典，包含success和message键
        """
        
        self.reports = []  # 清空现有报告
        
        try:
            # 使用新的dump_evaluation_spec接口获取所有评估规范
            specs = dump_evaluation_spec(database = database)
            
            if not specs:
                error_msg = "数据库中没有任何评估规范"
                print(f"警告: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
                
            print(f"找到 {len(specs)} 个评估规范。")
            
            # 为每个spec_id添加报告项
            for spec in specs:
                try:
                    print(f"正在为评估规范 {spec['id']} 创建报告项...")
                    report_item = self.add_report_item(spec)
                    print(f"成功为评估规范 {spec['id']} 创建报告项")
                    print(f"报告项详情: spec={report_item.spec.id}, evidences={len(report_item.evidences)}")
                except Exception as e:
                    print(f"为评估规范 {spec['id']} 创建报告项失败: {str(e)}")
                    
            print(f"初始化完成，当前报告总数: {len(self.reports)}")
            return {
                "success": True,
                "message": "数据加载成功"
            }
        except Exception as e:
            error_msg = f"初始化测试数据失败: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
