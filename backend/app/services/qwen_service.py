import requests
import json
from typing import Dict, Any, Optional
from app.core.config import settings

class QwenService:
    """
    阿里云通义千问API服务
    """
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.tts_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-to-speech/synthesis"
        self.asr_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/speech-recognition/recognition"
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """
        测试API连接是否有效
        """
        if not self.api_key or self.api_key == "your_qwen_api_key_here":
            return {
                "success": False,
                "error": "API密钥未配置或使用默认值",
                "details": "请在.env文件中配置有效的QWEN_API_KEY"
            }
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 发送一个简单的测试请求
            data = {
                "model": "qwen-turbo",
                "input": {
                    "messages": [
                        {"role": "user", "content": "测试连接"}
                    ]
                },
                "parameters": {
                    "max_tokens": 10,
                    "temperature": 0.1
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'output' in result:
                    return {
                        "success": True,
                        "message": "API连接测试成功",
                        "model": "qwen-turbo"
                    }
                else:
                    return {
                        "success": False,
                        "error": "API响应格式异常",
                        "details": str(result)
                    }
            else:
                return {
                    "success": False,
                    "error": f"API请求失败 (HTTP {response.status_code})",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "连接测试异常",
                "details": str(e)
            }
    
    async def generate_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        使用通义千问生成回复
        """
        if not self.api_key or self.api_key == "your_qwen_api_key_here":
            raise Exception("API密钥未配置或无效")
        
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt(context)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "qwen-turbo",  # 使用免费的qwen-turbo模型
                "input": {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ]
                },
                "parameters": {
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'output' in result and 'text' in result['output']:
                    return result['output']['text'].strip()
                else:
                    raise Exception(f"API响应格式异常: {result}")
            else:
                raise Exception(f"API请求失败: {response.status_code}, {response.text}")
                
        except Exception as e:
            print(f"通义千问服务错误: {e}")
            raise e
    
    async def text_to_speech(self, text: str, voice: str = "zhixiaoxia") -> Optional[bytes]:
        """
        文本转语音 (TTS)
        """
        if not self.api_key:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "cosyvoice-v1",  # 使用免费的语音合成模型
                "input": {
                    "text": text
                },
                "parameters": {
                    "voice": voice,  # 音色选择
                    "format": "mp3",
                    "sample_rate": 22050
                }
            }
            
            response = requests.post(self.tts_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'output' in result and 'audio_url' in result['output']:
                    # 下载音频文件
                    audio_response = requests.get(result['output']['audio_url'])
                    if audio_response.status_code == 200:
                        return audio_response.content
                    
            print(f"TTS请求失败: {response.status_code}, {response.text}")
            return None
            
        except Exception as e:
            print(f"TTS服务错误: {e}")
            return None
    
    async def speech_to_text(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """
        语音转文本 (ASR)
        """
        if not self.api_key:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 将音频数据转换为base64
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            data = {
                "model": "paraformer-realtime-v1",  # 使用免费的语音识别模型
                "input": {
                    "audio": audio_base64,
                    "format": format
                },
                "parameters": {
                    "language": "zh",  # 中文识别
                    "sample_rate": 16000
                }
            }
            
            response = requests.post(self.asr_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'output' in result and 'text' in result['output']:
                    return result['output']['text'].strip()
                    
            print(f"ASR请求失败: {response.status_code}, {response.text}")
            return None
            
        except Exception as e:
            print(f"ASR服务错误: {e}")
            return None
    
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

# 创建全局实例
qwen_service = QwenService()