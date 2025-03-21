from app.models.report.manager import ReportManager
from app.models.evidence.manager import EvidenceManager
from app.models.evaluation_spec.manager import EvaluationSpecManager

# 全局管理器实例

evidence_manager = EvidenceManager()
evaluation_spec_manager = EvaluationSpecManager()

report_manager = ReportManager()
