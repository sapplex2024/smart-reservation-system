import httpx
import asyncio
from typing import Optional, Dict, Any, List
from ..core.config import settings
from ..core.logger import logger

class SiliconFlowService:
    """硅基流动服务类"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SILICONFLOW_API_KEY', None)
        self.base_url = getattr(settings, 'SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')
        self.chat_url = f"{self.base_url}/chat/completions"
        self.tts_url = f"{self.base_url}/audio/speech"
        self.default_chat_model = "Qwen/Qwen2.5-72B-Instruct"
        self.default_tts_model = "FunAudioLLM/CosyVoice2-0.5B"
        self.default_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
    
    async def text_to_speech(
        self, 
        text: str, 
        model: str = None,
        voice: str = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        sample_rate: int = 24000
    ) -> Optional[bytes]:
        """文本转语音
        
        Args:
            text: 要转换的文本
            model: 使用的模型，默认为 FunAudioLLM/CosyVoice2-0.5B
            voice: 音色选择，默认为 alex
            response_format: 音频格式，支持 mp3, wav, pcm, opus
            speed: 语音速度，默认 1.0
            sample_rate: 采样率，默认 24000
            
        Returns:
            音频数据的字节流，失败时返回 None
        """
        if not self.api_key:
            logger.error("SiliconFlow API key not configured")
            return None
            
        if not text or not text.strip():
            logger.error("Text is empty")
            return None
        
        # 使用默认值或传入的参数
        model = model or self.default_tts_model
        if voice:
            # 如果传入的voice不包含模型前缀，则添加
            if ":" not in voice:
                voice = f"{model}:{voice}"
        else:
            voice = self.default_voice
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "sample_rate": sample_rate
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Calling SiliconFlow TTS API with model: {model}, voice: {voice}")
                response = await client.post(
                    self.tts_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info("SiliconFlow TTS request successful")
                    return response.content
                else:
                    logger.error(f"SiliconFlow TTS API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling SiliconFlow TTS API: {str(e)}")
            return None
    
    async def get_available_voices(self, model: str = None) -> List[Dict[str, Any]]:
        """获取可用的音色列表
        
        Args:
            model: 模型名称，如果不指定则返回所有模型的音色
            
        Returns:
            音色列表
        """
        # 硅基流动支持的音色列表（基于文档）
        voices_data = {
            "FunAudioLLM/CosyVoice2-0.5B": [
                {"id": "alex", "name": "Alex", "gender": "male", "language": "zh-CN"},
                {"id": "anna", "name": "Anna", "gender": "female", "language": "zh-CN"},
                {"id": "bella", "name": "Bella", "gender": "female", "language": "zh-CN"},
                {"id": "chris", "name": "Chris", "gender": "male", "language": "zh-CN"},
                {"id": "diana", "name": "Diana", "gender": "female", "language": "zh-CN"},
                {"id": "eric", "name": "Eric", "gender": "male", "language": "zh-CN"}
            ],
            "fishaudio/fish-speech-1.4": [
                {"id": "alex", "name": "Alex", "gender": "male", "language": "zh-CN"},
                {"id": "bella", "name": "Bella", "gender": "female", "language": "zh-CN"},
                {"id": "chris", "name": "Chris", "gender": "male", "language": "zh-CN"},
                {"id": "diana", "name": "Diana", "gender": "female", "language": "zh-CN"}
            ]
        }
        
        if model:
            return voices_data.get(model, [])
        else:
            # 返回所有音色，添加模型信息
            all_voices = []
            for model_name, voices in voices_data.items():
                for voice in voices:
                    voice_copy = voice.copy()
                    voice_copy["model"] = model_name
                    voice_copy["full_id"] = f"{model_name}:{voice['id']}"
                    all_voices.append(voice_copy)
            return all_voices
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """对话完成API
        
        Args:
            messages: 对话消息列表
            model: 使用的模型，默认为 Qwen/Qwen2.5-72B-Instruct
            max_tokens: 最大token数
            temperature: 温度参数
            stream: 是否流式输出
            
        Returns:
            API响应结果，失败时返回 None
        """
        if not self.api_key:
            logger.error("SiliconFlow API key not configured")
            return None
            
        if not messages:
            logger.error("Messages list is empty")
            return None
        
        # 使用默认值或传入的参数
        model = model or self.default_chat_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Calling SiliconFlow Chat API with model: {model}")
                response = await client.post(
                    self.chat_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info("SiliconFlow Chat request successful")
                    return response.json()
                else:
                    logger.error(f"SiliconFlow Chat API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling SiliconFlow Chat API: {str(e)}")
            return None
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """测试API连接有效性
        
        Returns:
            测试结果
        """
        if not self.api_key or self.api_key == "your_siliconflow_api_key_here":
            return {
                "success": False,
                "error": "API密钥未配置或使用默认值",
                "details": "请在.env文件中配置有效的SILICONFLOW_API_KEY"
            }
        
        try:
            # 使用聊天API进行真实连接测试
            test_messages = [
                {"role": "user", "content": "你好"}
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.default_chat_model,
                "messages": test_messages,
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.chat_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "硅基流动API连接成功",
                        "model": self.default_chat_model,
                        "response_id": result.get("id", "unknown")
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "API密钥无效",
                        "details": f"HTTP 401: {response.text}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API请求失败",
                        "details": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "连接超时",
                "details": "请检查网络连接"
            }
        except Exception as e:
            return {
                "success": False,
                "error": "连接测试异常",
                "details": str(e)
            }

# 全局实例
siliconflow_service = SiliconFlowService()