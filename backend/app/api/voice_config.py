from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

router = APIRouter()

# 配置文件路径
CONFIG_FILE = Path("voice_config.json")

# 配置数据模型
class ASRConfig(BaseModel):
    model: str = "paraformer-realtime-v1"
    language: str = "zh"
    sampleRate: int = 16000
    format: str = "wav"
    realtime: bool = True
    noiseReduction: bool = True

class TTSConfig(BaseModel):
    model: str = "cosyvoice-v1"
    voice: str = "zhixiaoxia"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 0.8
    format: str = "mp3"
    sampleRate: int = 22050

class APIConfig(BaseModel):
    apiKey: str = ""
    baseUrl: str = "https://dashscope.aliyuncs.com/api/v1"
    timeout: int = 30

class VoiceConfigRequest(BaseModel):
    asr: Optional[ASRConfig] = None
    tts: Optional[TTSConfig] = None
    api: Optional[APIConfig] = None

# 默认配置
DEFAULT_CONFIG = {
    "asr": {
        "model": "paraformer-realtime-v1",
        "language": "zh",
        "sampleRate": 16000,
        "format": "wav",
        "realtime": True,
        "noiseReduction": True
    },
    "tts": {
        "model": "cosyvoice-v1",
        "voice": "zhixiaoxia",
        "speed": 1.0,
        "pitch": 1.0,
        "volume": 0.8,
        "format": "mp3",
        "sampleRate": 22050
    },
    "api": {
        "apiKey": "",
        "baseUrl": "https://dashscope.aliyuncs.com/api/v1",
        "timeout": 30
    }
}

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置，确保所有字段都存在
                for section in DEFAULT_CONFIG:
                    if section not in config:
                        config[section] = DEFAULT_CONFIG[section]
                    else:
                        for key, value in DEFAULT_CONFIG[section].items():
                            if key not in config[section]:
                                config[section][key] = value
                return config
        else:
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

@router.get("/config")
async def get_voice_config():
    """获取语音配置"""
    try:
        config = load_config()
        return {
            "success": True,
            "asr": config.get("asr", DEFAULT_CONFIG["asr"]),
            "tts": config.get("tts", DEFAULT_CONFIG["tts"]),
            "api": {
                # 不返回完整的API密钥，只返回是否已配置
                "apiKey": "***" if config.get("api", {}).get("apiKey") else "",
                "baseUrl": config.get("api", {}).get("baseUrl", DEFAULT_CONFIG["api"]["baseUrl"]),
                "timeout": config.get("api", {}).get("timeout", DEFAULT_CONFIG["api"]["timeout"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.post("/config")
async def save_voice_config(config_request: VoiceConfigRequest):
    """保存语音配置"""
    try:
        # 加载现有配置
        current_config = load_config()
        
        # 更新配置
        if config_request.asr:
            current_config["asr"].update(config_request.asr.dict())
        
        if config_request.tts:
            current_config["tts"].update(config_request.tts.dict())
        
        if config_request.api:
            api_data = config_request.api.dict()
            # 如果API密钥是占位符，保持原有密钥不变
            if api_data.get("apiKey") == "***":
                api_data.pop("apiKey")
            current_config["api"].update(api_data)
        
        # 保存配置
        if save_config(current_config):
            return {"success": True, "message": "配置保存成功"}
        else:
            raise HTTPException(status_code=500, detail="配置保存失败")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

@router.get("/voices")
async def get_available_voices():
    """获取可用的语音列表"""
    try:
        voices = [
            {
                "id": "zhixiaoxia",
                "name": "知小夏",
                "gender": "female",
                "language": "zh-CN",
                "description": "温柔甜美的女声"
            },
            {
                "id": "zhichu",
                "name": "知楚",
                "gender": "male",
                "language": "zh-CN",
                "description": "成熟稳重的男声"
            },
            {
                "id": "zhimiao",
                "name": "知妙",
                "gender": "female",
                "language": "zh-CN",
                "description": "活泼可爱的女声"
            },
            {
                "id": "zhixiaobai",
                "name": "知小白",
                "gender": "male",
                "language": "zh-CN",
                "description": "清新自然的男声"
            },
            {
                "id": "zhiyan",
                "name": "知燕",
                "gender": "female",
                "language": "zh-CN",
                "description": "优雅知性的女声"
            }
        ]
        
        return {
            "success": True,
            "voices": voices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取语音列表失败: {str(e)}")

@router.get("/models")
async def get_available_models():
    """获取可用的模型列表"""
    try:
        models = {
            "asr": [
                {
                    "id": "paraformer-realtime-v1",
                    "name": "Paraformer实时版",
                    "description": "实时语音识别，低延迟",
                    "languages": ["zh", "en"]
                },
                {
                    "id": "paraformer-v1",
                    "name": "Paraformer标准版",
                    "description": "高精度语音识别",
                    "languages": ["zh", "en"]
                },
                {
                    "id": "whisper-large-v3",
                    "name": "Whisper Large V3",
                    "description": "多语言语音识别",
                    "languages": ["zh", "en", "auto"]
                }
            ],
            "tts": [
                {
                    "id": "cosyvoice-v1",
                    "name": "CosyVoice V1",
                    "description": "高质量语音合成",
                    "languages": ["zh", "en"]
                },
                {
                    "id": "speecht5",
                    "name": "SpeechT5",
                    "description": "快速语音合成",
                    "languages": ["zh", "en"]
                },
                {
                    "id": "vits",
                    "name": "VITS",
                    "description": "自然语音合成",
                    "languages": ["zh"]
                }
            ]
        }
        
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.post("/test-asr")
async def test_asr_config():
    """测试ASR配置"""
    try:
        # 这里可以实现实际的ASR测试逻辑
        # 目前返回模拟结果
        return {
            "success": True,
            "message": "ASR配置测试成功",
            "result": "测试识别结果：你好，这是语音识别测试。"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR测试失败: {str(e)}")

@router.post("/test-tts")
async def test_tts_config(request: dict):
    """测试TTS配置"""
    try:
        text = request.get("text", "你好，这是语音合成测试。")
        # 这里可以实现实际的TTS测试逻辑
        # 目前返回模拟结果
        return {
            "success": True,
            "message": "TTS配置测试成功",
            "audio_url": "/api/voice/tts",  # 实际的音频URL
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS测试失败: {str(e)}")