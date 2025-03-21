DEFAULT_SUMMARY_PROMPT = """请根据以下评估规范生成摘要和关键词：
一级标题：{primary_title}
二级标题：{secondary_title}
三级标题：{tertiary_title}

内容：
{content}

评估指南：
{guidelines}

请生成：
1. 简洁、专业的摘要，突出关键评估要点
2. 3-5个关键词，用逗号分隔

请以JSON格式返回结果，包含以下字段：
- summary: 摘要内容
- keywords: 关键词列表"""
