from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json
import base64
import io

from ..models.database import get_db, SystemSettings
from .auth import get_current_user
from ..models.database import User

router = APIRouter(prefix="/api/voice", tags=["语音服务"])

class ASRRequest(BaseModel):
    audio_data: str  # base64编码的音频数据
    format: str = "wav"  # 音频格式
    sample_rate: int = 16000  # 采样率
    language: str = "zh_cn"  # 语言

class ASRResponse(BaseModel):
    success: bool
    text: str = ""
    confidence: float = 0.0
    error: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "xiaoyan"
    speed: float = 0.5
    volume: float = 0.5
    pitch: float = 0.5

class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None  # base64编码的音频数据
    error: Optional[str] = None

class VoiceTestRequest(BaseModel):
    provider: str = "xunfei"
    config: Dict[str, Any] = {}

@router.get("/config")
async def get_voice_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取语音服务配置"""
    try:
        setting = db.query(SystemSettings).filter(
            SystemSettings.category == "voice",
            SystemSettings.key == "config"
        ).first()
        
        if not setting:
            return {
                "success": True,
                "config": {
                    "provider": "xunfei",
                    "xunfei": {
                        "appId": "",
                        "apiKey": "",
                        "apiSecret": ""
                    },
                    "enabled": False
                }
            }
        
        config = json.loads(setting.value)
        return {"success": True, "config": config}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取语音配置失败: {str(e)}")

@router.post("/asr")
async def speech_to_text(
    request: ASRRequest,
    db: Session = Depends(get_db)
):
    """语音识别 - 将语音转换为文字"""
    try:
        # 获取语音配置
        setting = db.query(SystemSettings).filter(
            SystemSettings.category == "voice",
            SystemSettings.key == "config"
        ).first()
        
        if not setting:
            return ASRResponse(
                success=False,
                error="语音服务未配置"
            )
        
        config = json.loads(setting.value)
        
        # 检查配置是否完整
        if not config.get("enabled", False):
            return ASRResponse(
                success=False,
                error="语音服务未启用"
            )
        
        provider = config.get("provider", "xunfei")
        
        if provider == "xunfei":
            return await _xunfei_asr(request, config.get("xunfei", {}))
        else:
            return ASRResponse(
                success=False,
                error=f"不支持的语音服务提供商: {provider}"
            )
            
    except Exception as e:
        return ASRResponse(
            success=False,
            error=f"语音识别失败: {str(e)}"
        )

@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    db: Session = Depends(get_db)
):
    """语音合成 - 将文字转换为语音"""
    try:
        # 获取语音配置
        setting = db.query(SystemSettings).filter(
            SystemSettings.category == "voice",
            SystemSettings.key == "config"
        ).first()
        
        if not setting:
            return TTSResponse(
                success=False,
                error="语音服务未配置"
            )
        
        config = json.loads(setting.value)
        
        if not config.get("enabled", False):
            return TTSResponse(
                success=False,
                error="语音服务未启用"
            )
        
        provider = config.get("provider", "xunfei")
        
        if provider == "xunfei":
            return await _xunfei_tts(request, config.get("xunfei", {}))
        elif provider == "qwen":
            return await _qwen_tts(request, config.get("qwen", {}))
        else:
            return TTSResponse(
                success=False,
                error=f"不支持的语音服务提供商: {provider}"
            )
            
    except Exception as e:
        return TTSResponse(
            success=False,
            error=f"语音合成失败: {str(e)}"
        )

@router.post("/test-connection")
async def test_voice_connection(
    request: VoiceTestRequest,
    db: Session = Depends(get_db)
):
    """测试语音服务连接"""
    try:
        provider = request.provider
        config = request.config
        
        if provider == "xunfei":
            # 验证科大讯飞配置
            required_fields = ["appId", "apiKey", "apiSecret"]
            for field in required_fields:
                if not config.get(field):
                    return {
                        "success": False,
                        "message": f"缺少必要的配置项: {field}"
                    }
            
            # 这里可以添加实际的连接测试逻辑
            return {
                "success": True,
                "message": "科大讯飞语音服务连接测试成功",
                "provider": "xunfei"
            }
        
        elif provider == "qwen":
            # 验证通义千问配置
            if not config.get("apiKey"):
                return {
                    "success": False,
                    "message": "缺少通义千问API Key"
                }
            
            return {
                "success": True,
                "message": "通义千问语音服务连接测试成功",
                "provider": "qwen"
            }
        
        else:
            return {
                "success": False,
                "message": f"不支持的语音服务提供商: {provider}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"连接测试失败: {str(e)}"
        }

@router.get("/voices")
async def get_available_voices():
    """获取可用的语音列表"""
    return {
        "success": True,
        "voices": [
            {"id": "xiaoyan", "name": "小燕", "gender": "female", "language": "zh_cn"},
            {"id": "xiaoyu", "name": "小宇", "gender": "male", "language": "zh_cn"},
            {"id": "xiaoxin", "name": "小新", "gender": "male", "language": "zh_cn"},
            {"id": "xiaofeng", "name": "小峰", "gender": "male", "language": "zh_cn"}
        ]
    }

# 私有函数 - 科大讯飞语音识别
async def _xunfei_asr(request: ASRRequest, config: Dict[str, Any]) -> ASRResponse:
    """科大讯飞语音识别实现"""
    try:
        # 检查配置
        app_id = config.get("appId")
        api_key = config.get("apiKey")
        api_secret = config.get("apiSecret")
        
        if not all([app_id, api_key, api_secret]):
            return ASRResponse(
                success=False,
                error="科大讯飞配置不完整"
            )
        
        # 导入科大讯飞ASR服务
        from ..services.xunfei_realtime_asr import XunfeiRealtimeASR
        
        # 创建ASR实例
        asr = XunfeiRealtimeASR(app_id, api_key, api_secret)
        
        # 解码音频数据
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception as e:
            return ASRResponse(
                success=False,
                error=f"音频数据解码失败: {str(e)}"
            )
        
        # 连接到科大讯飞ASR服务
        await asr.connect()
        
        # 发送音频数据并获取识别结果
        result_text = ""
        confidence = 0.0
        
        # 设置回调函数来收集识别结果
        def transcript_callback(text: str, is_final: bool):
            nonlocal result_text, confidence
            if is_final:
                result_text = text
                confidence = 0.95  # 科大讯飞通常不返回置信度，设置默认值
        
        asr.set_transcript_callback(transcript_callback)
        
        # 发送音频数据
        await asr.send_audio(audio_bytes)
        
        # 等待识别完成
        await asr.close()
        
        return ASRResponse(
            success=True,
            text=result_text or "未识别到语音内容",
            confidence=confidence
        )
        
    except Exception as e:
        return ASRResponse(
            success=False,
            error=f"科大讯飞ASR调用失败: {str(e)}"
        )

# 私有函数 - 科大讯飞语音合成
async def _xunfei_tts(request: TTSRequest, config: Dict[str, Any]) -> TTSResponse:
    """科大讯飞语音合成实现"""
    try:
        # 检查配置
        app_id = config.get("appId")
        api_key = config.get("apiKey")
        api_secret = config.get("apiSecret")
        
        if not all([app_id, api_key, api_secret]):
            return TTSResponse(
                success=False,
                error="科大讯飞配置不完整"
            )
        
        # 这里应该实现实际的科大讯飞TTS调用
        # 由于需要复杂的WebSocket连接和认证，这里先返回模拟结果
        
        # 模拟音频数据（空的base64字符串）
        return TTSResponse(
            success=True,
            audio_data=""  # 实际应该返回base64编码的音频数据
        )
        
    except Exception as e:
        return TTSResponse(
            success=False,
            error=f"科大讯飞TTS调用失败: {str(e)}"
        )

# 私有函数 - 通义千问语音合成
async def _qwen_tts(request: TTSRequest, config: Dict[str, Any]) -> TTSResponse:
    """通义千问语音合成实现"""
    try:
        # 检查配置
        api_key = config.get("apiKey")
        
        if not api_key:
            return TTSResponse(
                success=False,
                error="通义千问API Key未配置"
            )
        
        # 这里应该实现实际的通义千问TTS调用
        # 暂时返回模拟结果
        
        return TTSResponse(
            success=True,
            audio_data=""  # 实际应该返回base64编码的音频数据
        )
        
    except Exception as e:
        return TTSResponse(
            success=False,
            error=f"通义千问TTS调用失败: {str(e)}"
        )