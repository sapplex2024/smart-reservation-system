from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import base64
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.database import get_db, SystemSettings
from ..services.ai_service import AIService
from ..services.xunfei_realtime_asr import XunfeiRealtimeASR
from ..services.xunfei_streaming_tts import XunfeiStreamingTTS
from ..utils.audio_converter import AudioConverter

router = APIRouter(prefix="/api/voice", tags=["语音聊天"])
logger = logging.getLogger(__name__)

class VoiceChatManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.asr_sessions: Dict[str, XunfeiRealtimeASR] = {}
        self.tts_sessions: Dict[str, XunfeiStreamingTTS] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"语音聊天客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.asr_sessions:
            asyncio.create_task(self.asr_sessions[client_id].disconnect())
            del self.asr_sessions[client_id]
        if client_id in self.tts_sessions:
            asyncio.create_task(self.tts_sessions[client_id].disconnect())
            del self.tts_sessions[client_id]
        logger.info(f"语音聊天客户端 {client_id} 已断开连接")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                self.disconnect(client_id)

manager = VoiceChatManager()

@router.websocket("/chat")
async def voice_chat_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    client_id = f"client_{datetime.now().timestamp()}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_voice_message(client_id, message, db)
                
            except WebSocketDisconnect:
                logger.info(f"客户端 {client_id} 主动断开连接")
                break
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "消息格式错误"
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息时出错: {e}")
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": f"处理消息时出错: {str(e)}"
                })
                
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
    finally:
        manager.disconnect(client_id)

async def handle_voice_message(client_id: str, message: dict, db: Session):
    """处理语音消息"""
    message_type = message.get("type")
    
    try:
        if message_type == "start_recording":
            await start_voice_recording(client_id, message, db)
        elif message_type == "audio_chunk":
            await process_audio_chunk(client_id, message, db)
        elif message_type == "audio_complete":
            await process_complete_audio(client_id, message, db)
        elif message_type == "stop_recording":
            await stop_voice_recording(client_id, message, db)
        elif message_type == "text_message":
            await process_text_message(client_id, message, db)
        else:
            await manager.send_message(client_id, {
                "type": "error",
                "message": f"未知消息类型: {message_type}"
            })
    except Exception as e:
        logger.error(f"处理语音消息失败: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"处理失败: {str(e)}"
        })

async def start_voice_recording(client_id: str, message: dict, db: Session):
    """开始语音录制"""
    try:
        # 获取语音配置
        config = await get_voice_config(db)
        if not config or not config.get("enabled"):
            await manager.send_message(client_id, {
                "type": "error",
                "message": "语音服务未启用"
            })
            return
        
        # 创建ASR会话
        provider = config.get("provider", "xunfei")
        if provider == "xunfei":
            xunfei_config = config.get("xunfei", {})
            asr = XunfeiRealtimeASR(
                app_id=xunfei_config.get("appId", ""),
                api_key=xunfei_config.get("apiKey", ""),
                api_secret=xunfei_config.get("apiSecret", "")
            )
            
            # 设置回调函数
            async def on_transcript(text: str, is_final: bool):
                await manager.send_message(client_id, {
                    "type": "final_transcript" if is_final else "transcript",
                    "text": text
                })
            
            asr.set_transcript_callback(on_transcript)
            
            # 连接ASR服务
            await asr.connect()
            manager.asr_sessions[client_id] = asr
            
            await manager.send_message(client_id, {
                "type": "recording_started",
                "message": "开始录音"
            })
        else:
            await manager.send_message(client_id, {
                "type": "error",
                "message": f"不支持的语音提供商: {provider}"
            })
            
    except Exception as e:
        logger.error(f"开始录音失败: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"开始录音失败: {str(e)}"
        })

async def process_complete_audio(client_id: str, message: dict, db: Session):
    """处理完整的音频数据"""
    try:
        if client_id not in manager.asr_sessions:
            await manager.send_message(client_id, {
                "type": "error",
                "message": "ASR会话未初始化"
            })
            return
        
        # 获取音频数据和格式
        audio_data = message.get("audio_data")
        audio_format = message.get("format", "webm")
        
        if not audio_data:
            return
        
        # 解码base64音频数据
        try:
            audio_bytes = base64.b64decode(audio_data)
            logger.info(f"接收到完整音频数据: {len(audio_bytes)}字节, 格式: {audio_format}")
        except Exception as e:
            logger.error(f"音频数据解码失败: {e}")
            return
        
        # 根据格式转换为PCM
        pcm_data = None
        if audio_format == "wav":
            pcm_data = AudioConverter.wav_to_pcm(audio_bytes, sample_rate=16000, channels=1)
        else:  # webm
            pcm_data = AudioConverter.webm_to_pcm(audio_bytes, sample_rate=16000, channels=1)
        
        if pcm_data is None:
            logger.error(f"音频格式转换失败，数据长度: {len(audio_bytes)}字节，格式: {audio_format}")
            await manager.send_message(client_id, {
                "type": "error",
                "message": "音频格式转换失败"
            })
            return
        
        # 发送PCM音频数据到ASR服务
        asr = manager.asr_sessions[client_id]
        await asr.send_audio(pcm_data)
        
        # 通知ASR服务音频结束
        await asr.stop_recording()
        
    except Exception as e:
        logger.error(f"处理完整音频数据失败: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"处理音频数据失败: {str(e)}"
        })

async def process_audio_chunk(client_id: str, message: dict, db: Session):
    """处理音频数据块"""
    try:
        if client_id not in manager.asr_sessions:
            await manager.send_message(client_id, {
                "type": "error",
                "message": "ASR会话未初始化"
            })
            return
        
        # 获取音频数据
        audio_data = message.get("audio_data")
        if not audio_data:
            return
        
        # 解码base64音频数据
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            logger.error(f"音频数据解码失败: {e}")
            return
        
        # 智能检测音频格式并转换为PCM
        pcm_data = None
        
        # 检测音频格式（简单的魔数检测）
        if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:12]:
            # WAV格式
            pcm_data = AudioConverter.wav_to_pcm(audio_bytes, sample_rate=16000, channels=1)
            logger.debug("检测到WAV格式音频")
        elif audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):  # EBML header for WebM
            # WebM格式
            pcm_data = AudioConverter.webm_to_pcm(audio_bytes, sample_rate=16000, channels=1)
            logger.debug("检测到WebM格式音频")
        else:
            # 默认尝试WebM格式
            pcm_data = AudioConverter.webm_to_pcm(audio_bytes, sample_rate=16000, channels=1)
            logger.debug("未知格式，尝试WebM解析")
        
        if pcm_data is None:
            logger.error(f"音频格式转换失败，数据长度: {len(audio_bytes)}字节")
            await manager.send_message(client_id, {
                "type": "error",
                "message": "音频格式转换失败"
            })
            return
        
        # 发送PCM音频数据到ASR服务
        asr = manager.asr_sessions[client_id]
        await asr.send_audio(pcm_data)
        
    except Exception as e:
        logger.error(f"处理音频数据失败: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"处理音频数据失败: {str(e)}"
        })

async def stop_voice_recording(client_id: str, message: dict, db: Session):
    """停止语音录制"""
    try:
        if client_id in manager.asr_sessions:
            asr = manager.asr_sessions[client_id]
            await asr.stop_recording()
            
            await manager.send_message(client_id, {
                "type": "recording_stopped",
                "message": "录音结束"
            })
        
    except Exception as e:
        logger.error(f"停止录音失败: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"停止录音失败: {str(e)}"
        })

async def process_text_message(client_id: str, message: dict, db: Session):
    """处理文本消息"""
    try:
        text = message.get("text", "").strip()
        if not text:
            return
        
        # 使用AI服务生成回复
        ai_service = AIService()
        response = await ai_service.chat(text)
        
        # 发送AI回复
        await manager.send_message(client_id, {
            "type": "ai_response",
            "text": response
        })
        
        # 生成语音回复
        await generate_voice_response(client_id, response, db)
        
    except Exception as e:
        logger.error(f"处理文本消息失败: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"处理文本消息失败: {str(e)}"
        })

async def generate_voice_response(client_id: str, text: str, db: Session):
    """生成语音回复"""
    try:
        # 获取语音配置
        config = await get_voice_config(db)
        if not config or not config.get("enabled"):
            return
        
        provider = config.get("provider", "xunfei")
        if provider == "xunfei":
            xunfei_config = config.get("xunfei", {})
            tts = XunfeiStreamingTTS(
                app_id=xunfei_config.get("appId", ""),
                api_key=xunfei_config.get("apiKey", ""),
                api_secret=xunfei_config.get("apiSecret", "")
            )
            
            # 生成语音
            audio_data = await tts.synthesize(text)
            if audio_data:
                # 发送音频数据
                await manager.send_message(client_id, {
                    "type": "audio_response",
                    "audio_data": base64.b64encode(audio_data).decode('utf-8')
                })
        
    except Exception as e:
        logger.error(f"生成语音回复失败: {e}")

async def get_voice_config(db: Session) -> Optional[Dict[str, Any]]:
    """获取语音配置"""
    try:
        setting = db.query(SystemSettings).filter(
            SystemSettings.category == "voice",
            SystemSettings.key == "config"
        ).first()
        
        if setting:
            return json.loads(setting.value)
        return None
        
    except Exception as e:
        logger.error(f"获取语音配置失败: {e}")
        return None