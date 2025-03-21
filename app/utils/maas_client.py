from openai import OpenAI
from app.config.config import Config

class MaaSClient:
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL
        )
        self.vlm_client = OpenAI(
            api_key=Config.VLM_API_KEY,
            base_url=Config.VLM_BASE_URL
        )
        self.embedding_client = OpenAI(
            api_key=Config.EMBEDDING_API_KEY,
            base_url=Config.EMBEDDING_BASE_URL
        )

    def chat_completion(self, messages, model=None, output_format=None):
        # 确保messages是列表格式
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # 如果指定了JSON格式输出，添加系统提示
        if output_format == 'json':
            messages.insert(0, {
                "role": "system",
                "content": "请始终以JSON格式返回结果"
            })
            
        response = self.llm_client.chat.completions.create(
            messages=messages,
            model=model or Config.LLM_MODEL,
            response_format={"type": "json_object"} if output_format == 'json' else None
        )
        
        # 解析响应
        content = response.choices[0].message.content
        content = content[content.find('{')-1:content.rfind('}')+1]
        # print(content)
        if output_format == 'json':
            import json
            return json.loads(content)
        return {
            'text': content
        }

    def vision_completion(self, messages, model=None):
        return self.vlm_client.chat.completions.create(
            messages=messages,
            model=model or Config.VLM_MODEL
        )

    def get_embeddings(self, input, model=None, dimensions=1024, encoding_format="float"):
        """获取文本的嵌入向量
        Args:
            input: 输入文本
            model: 模型名称，可选
            dimensions: 向量维度，默认1024
            encoding_format: 编码格式，默认"float"
        Returns:
            返回嵌入向量
        """
        return self.embedding_client.embeddings.create(
            input=input,
            model=model or Config.EMBEDDING_MODEL,
            dimensions=dimensions,
            encoding_format=encoding_format
        ).data[0].embedding

maas_client = MaaSClient()

def chat_completion(messages, model=None):
    return maas_client.chat_completion(messages, model)

def vision_completion(messages, model=None):
    return maas_client.vision_completion(messages, model)

def get_embeddings(input, model=None):
    return maas_client.get_embeddings(input, model)
