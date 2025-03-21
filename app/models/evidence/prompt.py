DEFAULT_SUMMARY_PROMPT = """请根据以下证明材料生成摘要和关键词：
文件名：{filename}
文件格式：{file_format}
采集时间：{collection_time}
采集人员：{collector}
所属项目：{project}
类型：{evidence_type}

内容：
{content}

请生成：
1. 简洁、专业的摘要，突出关键信息
2. 3-5个关键词，用逗号分隔

请以JSON格式返回结果，包含以下字段：
- summary: 摘要内容
- keywords: 关键词列表"""
