import asyncio
import websockets
import json
import base64
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlencode, quote
import logging
from typing import Optional, Callable, Dict, Any, AsyncGenerator
import io

logger = logging.getLogger(__name__)

class XunfeiStreamingTTS:
    """科大讯飞流式语音合成服务"""
    
    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = "tts-api.xfyun.cn"
        self.uri = "/v2/tts"
        
    def _generate_auth_header(self, date: str) -> str:
        """生成认证头"""
        # 构建签名原始字符串
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.uri} HTTP/1.1"
        
        # 使用HMAC-SHA256计算签名
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature = base64.b64encode(signature_sha).decode('utf-8')
        
        # 构建authorization原始字符串
        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        
        # Base64编码
        auth_str = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        return auth_str
    
    def _build_auth_url(self) -> tuple[str, str]:
        """构建认证URL"""
        # 获取当前时间 RFC1123格式
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        auth_str = self._generate_auth_header(date)
        
        params = {
            'authorization': auth_str,
            'date': date,
            'host': self.host
        }
        
        url = f"wss://{self.host}{self.uri}?{urlencode(params)}"
        return url, date
    
    async def synthesize_streaming(self, text: str, 
                                  voice: str = "xiaoyan",
                                  speed: int = 50,
                                  volume: int = 50,
                                  pitch: int = 50,
                                  audio_format: str = "mp3") -> AsyncGenerator[bytes, None]:
        """流式语音合成
        
        Args:
            text: 要合成的文本
            voice: 发音人 (xiaoyan, aisjiuxu, aisxping等)
            speed: 语速 (0-100)
            volume: 音量 (0-100) 
            pitch: 音调 (0-100)
            audio_format: 音频格式 (mp3, pcm)
        
        Yields:
            bytes: 音频数据块
        """
        websocket = None
        try:
            auth_url, date = self._build_auth_url()
            logger.info(f"连接到科大讯飞流式TTS: {auth_url[:100]}...")
            
            websocket = await websockets.connect(auth_url)
            logger.info("科大讯飞流式TTS连接成功")
            
            # 构建请求参数
            aue = "lame" if audio_format == "mp3" else "raw"
            sfl = 1 if audio_format == "mp3" else 0
            
            frame = {
                "common": {
                    "app_id": self.app_id
                },
                "business": {
                    "aue": aue,
                    "auf": "audio/L16;rate=16000",
                    "vcn": voice,
                    "tte": "UTF8",
                    "sfl": sfl,
                    "speed": speed,
                    "volume": volume,
                    "pitch": pitch
                },
                "data": {
                    "text": base64.b64encode(text.encode('utf-8')).decode('utf-8'),
                    "status": 2  # 一次性发送完整文本
                }
            }
            
            # 发送合成请求
            await websocket.send(json.dumps(frame))
            logger.info(f"发送TTS合成请求: {text[:50]}...")
            
            # 接收音频数据
            audio_buffer = io.BytesIO()
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('code') != 0:
                        error_msg = f"TTS合成错误: {data.get('message', '未知错误')}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    audio_data = data.get('data', {}).get('audio')
                    if audio_data:
                        # 解码音频数据
                        audio_bytes = base64.b64decode(audio_data)
                        audio_buffer.write(audio_bytes)
                        
                        # 流式返回音频数据
                        yield audio_bytes
                    
                    # 检查是否合成完成
                    status = data.get('data', {}).get('status')
                    if status == 2:
                        logger.info("TTS合成完成")
                        break
                        
                except json.JSONDecodeError as e:
                    logger.error(f"解析TTS响应失败: {e}")
                    break
                except Exception as e:
                    logger.error(f"处理TTS响应时出错: {e}")
                    raise
            
        except Exception as e:
            logger.error(f"流式TTS合成失败: {e}")
            raise
        finally:
            if websocket:
                try:
                    await websocket.close()
                    logger.info("科大讯飞流式TTS连接已关闭")
                except Exception as e:
                    logger.error(f"关闭TTS连接时出错: {e}")
    
    async def synthesize_complete(self, text: str,
                                 voice: str = "xiaoyan",
                                 speed: int = 50,
                                 volume: int = 50,
                                 pitch: int = 50,
                                 audio_format: str = "mp3") -> bytes:
        """完整语音合成（等待所有数据）
        
        Returns:
            bytes: 完整的音频数据
        """
        audio_buffer = io.BytesIO()
        
        async for audio_chunk in self.synthesize_streaming(
            text, voice, speed, volume, pitch, audio_format
        ):
            audio_buffer.write(audio_chunk)
        
        return audio_buffer.getvalue()
    
    def get_available_voices(self) -> Dict[str, str]:
        """获取可用的发音人列表"""
        return {
            "xiaoyan": "小燕(女声，温和)",
            "aisjiuxu": "许久(男声，磁性)",
            "aisxping": "小萍(女声，甜美)",
            "aisjinger": "小婧(女声，柔和)",
            "aisbabyxu": "许小宝(童声)",
            "x2_xiaofeng": "小峰(男声，成熟)",
            "x2_xiaoyuan": "小媛(女声，知性)",
            "x2_xiaoqian": "小倩(女声，可爱)",
            "x2_xiaoxue": "小雪(女声，清新)",
            "x2_xiaoyao": "小瑶(女声，活泼)"
        }
    
    def validate_parameters(self, voice: str, speed: int, volume: int, pitch: int) -> bool:
        """验证合成参数"""
        available_voices = self.get_available_voices()
        
        if voice not in available_voices:
            logger.error(f"不支持的发音人: {voice}")
            return False
        
        if not (0 <= speed <= 100):
            logger.error(f"语速参数超出范围: {speed}")
            return False
        
        if not (0 <= volume <= 100):
            logger.error(f"音量参数超出范围: {volume}")
            return False
        
        if not (0 <= pitch <= 100):
            logger.error(f"音调参数超出范围: {pitch}")
            return False
        
        return True