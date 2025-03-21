DEFAULT_REPORT_PROMPT = """请根据以下报告规范和证明材料生成报告结论：
报告规范：
{spec_summary}

证明材料：
{evidence_summaries}

请生成：
1. 是否合格的判断（是/否）
2. 详细的报告结论

请以JSON格式返回结果，包含以下字段：
- is_qualified: 是否合格
- conclusion: 报告结论
"""
