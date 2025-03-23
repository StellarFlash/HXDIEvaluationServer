from app.models.document.manager import  DocumentManager
from app.models.evidence.manager import EvidenceManager
from app.models.evaluation_spec.manager import EvaluationSpecManager
from app.models.report.manager import ReportManager
# 全局管理器实例
document_manager = DocumentManager()
evidence_manager = EvidenceManager()
evaluation_spec_manager = EvaluationSpecManager()

report_manager = ReportManager()
