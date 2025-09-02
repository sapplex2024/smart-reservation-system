from openai import OpenAI
from typing import Dict, Any, Optional
import json
from app.core.config import settings
from app.services.qwen_service import QwenService
from app.services.siliconflow_service import siliconflow_service

class AIService:
    def __init__(self):
        # 优先使用通义千问服务
        self.qwen_service = QwenService()
        
        # 硅基流动服务
        self.siliconflow_service = siliconflow_service
        
        # OpenAI作为备用
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成AI回复 - 优先使用通义千问，然后硅基流动，最后回退到OpenAI
        """
        # 首先尝试通义千问
        if settings.QWEN_API_KEY:
            try:
                response = await self.qwen_service.generate_response(message, context)
                if response and not response.startswith("感谢您的咨询"):  # 不是fallback回复
                    return response
            except Exception as e:
                print(f"通义千问服务错误，尝试硅基流动服务: {e}")
        
        # 尝试硅基流动
        if self.siliconflow_service.api_key:
            try:
                # 构建系统提示
                system_prompt = self._build_system_prompt(context)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                
                response = await self.siliconflow_service.chat_completion(
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                if response and response.get("choices"):
                    content = response["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
                        
            except Exception as e:
                print(f"硅基流动服务错误，尝试OpenAI备用服务: {e}")
        
        # 回退到OpenAI
        if self.openai_client:
            try:
                # 构建系统提示
                system_prompt = self._build_system_prompt(context)
                
                # 调用OpenAI API
                response = self.openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"OpenAI服务错误: {e}")
        
        # 所有AI服务都失败，抛出异常让调用方处理
        raise Exception("所有AI服务都不可用")
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        构建系统提示
        """
        base_prompt = """
你是一个智能预约系统的助手，专门帮助用户处理会议室预约、访客预约和车位预约等事务。

你的主要职责：
1. 理解用户的预约需求
2. 提供友好、专业的服务
3. 引导用户完成预约流程
4. 回答关于预约系统的问题

请用中文回复，保持友好和专业的语调。
        """
        
        if context:
            base_prompt += f"\n\n当前对话上下文：{json.dumps(context, ensure_ascii=False)}"
        
        return base_prompt.strip()
    
    def _get_fallback_response(self, message: str) -> str:
        """
        当AI服务不可用时的备用回复
        """
        fallback_responses = {
            "greeting": "您好！我是智能预约助手，很高兴为您服务。我可以帮您预约会议室、安排访客来访或预约车位。请告诉我您需要什么帮助？",
            "reservation": "我理解您想要进行预约。请提供更多详细信息，比如预约类型（会议室/访客/车位）、时间和其他要求，我会尽力帮助您。",
            "query": "我可以帮您查询预约信息。请告诉我您想查询什么内容？",
            "help": "我可以帮助您：\n1. 预约会议室\n2. 安排访客来访\n3. 预约车位\n4. 查询现有预约\n5. 取消或修改预约\n\n请告诉我您需要哪种服务？",
            "default": "感谢您的咨询。我是智能预约助手，专门处理预约相关事务。如果您需要预约服务或有相关问题，请随时告诉我！"
        }
        
        # 简单的关键词匹配
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["你好", "hello", "hi", "您好"]):
            return fallback_responses["greeting"]
        elif any(word in message_lower for word in ["预约", "预定", "booking", "reserve"]):
            return fallback_responses["reservation"]
        elif any(word in message_lower for word in ["查询", "查看", "query", "check"]):
            return fallback_responses["query"]
        elif any(word in message_lower for word in ["帮助", "help", "怎么", "如何"]):
            return fallback_responses["help"]
        else:
            return fallback_responses["default"]
    
    async def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """
        分析消息情感
        """
        if not self.client:
            return {"sentiment": "neutral", "confidence": 0.5}
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "分析以下消息的情感倾向，返回JSON格式：{\"sentiment\": \"positive/negative/neutral\", \"confidence\": 0.0-1.0}"
                    },
                    {"role": "user", "content": message}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"情感分析错误: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}
    
    async def generate_suggestions(self, context: Dict[str, Any]) -> list:
        """
        基于上下文生成建议
        """
        default_suggestions = [
            "我想预约会议室",
            "查看我的预约",
            "预约访客来访",
            "预约车位",
            "取消预约"
        ]
        
        if not self.client:
            return default_suggestions
        
        try:
            response = await self.client.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"基于对话上下文生成3-5个相关的用户可能想要的操作建议，返回JSON数组格式。上下文：{json.dumps(context, ensure_ascii=False)}"
                    }
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            suggestions = json.loads(response.choices[0].message.content)
            return suggestions if isinstance(suggestions, list) else default_suggestions
            
        except Exception as e:
            print(f"建议生成错误: {e}")
            return default_suggestions