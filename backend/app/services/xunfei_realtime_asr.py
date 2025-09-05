import asyncio
import websockets
import json
import base64
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlencode
import logging
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

class XunfeiRealtimeASR:
    """科大讯飞实时语音识别服务"""
    
    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = "rtasr.xfyun.cn"
        self.uri = "/v1/ws"
        self.websocket = None
        self.is_connected = False
        self.transcript_callback = None
        
    def _generate_signature(self, ts: str) -> str:
        """生成签名"""
        # 1. 获取baseString
        base_string = self.app_id + ts
        
        # 2. 对baseString进行MD5
        md5_hash = hashlib.md5(base_string.encode('utf-8')).hexdigest()
        
        # 3. 以apiKey为key对MD5之后的baseString进行HmacSHA1加密，然后base64编码
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            md5_hash.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _build_auth_url(self) -> str:
        """构建认证URL"""
        ts = str(int(datetime.now().timestamp()))
        signature = self._generate_signature(ts)
        
        params = {
            'appid': self.app_id,
            'ts': ts,
            'signa': signature,
            'lang': 'cn',  # 中文
            'punc': '1',   # 返回标点
            'pd': 'tech'   # 科技领域
        }
        
        return f"wss://{self.host}{self.uri}?{urlencode(params)}"
    
    def set_transcript_callback(self, callback: Callable[[str, bool], None]):
        """设置转录回调函数"""
        self.transcript_callback = callback
    
    async def connect(self, on_result: Optional[Callable[[Dict[str, Any]], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None) -> bool:
        """连接到科大讯飞实时语音识别服务"""
        try:
            auth_url = self._build_auth_url()
            logger.info(f"连接到科大讯飞实时ASR: {auth_url}")
            
            self.websocket = await websockets.connect(auth_url)
            self.is_connected = True
            
            # 启动消息接收任务
            asyncio.create_task(self._handle_messages(on_result, on_error))
            
            logger.info("科大讯飞实时ASR连接成功")
            return True
            
        except Exception as e:
            logger.error(f"连接科大讯飞实时ASR失败: {e}")
            if on_error:
                on_error(f"连接失败: {e}")
            return False
    
    async def _handle_messages(self, on_result: Optional[Callable[[Dict[str, Any]], None]],
                              on_error: Optional[Callable[[str], None]]):
        """处理WebSocket消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('action') == 'started':
                        logger.info("科大讯飞实时ASR握手成功")
                        continue
                    
                    if data.get('action') == 'result':
                        # 提取识别结果
                        text = self.extract_text_from_result(data)
                        is_final = self.is_final_result(data)
                        
                        # 调用回调函数
                        if self.transcript_callback and text:
                            self.transcript_callback(text, is_final)
                        
                        if on_result:
                            on_result(data)
                    
                    elif data.get('action') == 'error':
                        error_msg = f"ASR错误: {data.get('desc', '未知错误')}"
                        logger.error(error_msg)
                        if on_error:
                            on_error(error_msg)
                            
                except json.JSONDecodeError as e:
                    logger.error(f"解析ASR响应失败: {e}")
                    if on_error:
                        on_error(f"解析响应失败: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("科大讯飞实时ASR连接已关闭")
            self.is_connected = False
        except Exception as e:
            logger.error(f"处理ASR消息时出错: {e}")
            if on_error:
                on_error(f"处理消息出错: {e}")
            self.is_connected = False
    
    async def send_audio(self, audio_data: bytes) -> bool:
        """发送音频数据"""
        if not self.is_connected or not self.websocket:
            logger.error("ASR连接未建立")
            return False
        
        try:
            # 科大讯飞实时ASR直接发送PCM音频数据
            await self.websocket.send(audio_data)
            return True
            
        except Exception as e:
            logger.error(f"发送音频数据失败: {e}")
            return False
    
    async def send_end_signal(self) -> bool:
        """发送结束信号"""
        if not self.is_connected or not self.websocket:
            return False
        
        try:
            # 发送空数据表示结束
            await self.websocket.send(b'')
            return True
        except Exception as e:
            logger.error(f"发送结束信号失败: {e}")
            return False
    
    async def close(self):
        """关闭连接并发送结束信号"""
        if self.is_connected:
            # 发送结束信号
            await self.send_end_signal()
            # 断开连接
            await self.disconnect()
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"关闭ASR连接时出错: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
                logger.info("科大讯飞实时ASR连接已断开")
    
    def extract_text_from_result(self, result_data: Dict[str, Any]) -> Optional[str]:
        """从识别结果中提取文本"""
        try:
            data = result_data.get('data')
            if not data:
                return None
            
            result = data.get('result')
            if not result:
                return None
            
            # 提取识别文本
            words = []
            for item in result.get('ws', []):
                for word_info in item.get('cw', []):
                    words.append(word_info.get('w', ''))
            
            text = ''.join(words)
            return text if text.strip() else None
            
        except Exception as e:
            logger.error(f"提取识别文本失败: {e}")
            return None
    
    def is_final_result(self, result_data: Dict[str, Any]) -> bool:
        """判断是否为最终结果"""
        try:
            data = result_data.get('data', {})
            result = data.get('result', {})
            return result.get('ls', False)  # ls=true表示最终结果
        except:
            return False