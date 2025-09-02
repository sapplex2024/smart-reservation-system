from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from typing import Dict, Any, Optional
from app.services.qwen_service import QwenService
from app.services.siliconflow_service import siliconflow_service
import io

router = APIRouter()
qwen_service = QwenService()

@router.post("/tts")
async def text_to_speech(request: Dict[str, Any]):
    """
    文本转语音API
    支持多个语音提供商：qwen（通义千问）、siliconflow（硅基流动）
    """
    try:
        text = request.get("text", "")
        voice = request.get("voice", "zhixiaoxia")
        provider = request.get("provider", "qwen")  # 默认使用通义千问
        model = request.get("model", None)  # 硅基流动模型选择
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        audio_data = None
        
        if provider == "siliconflow":
            # 使用硅基流动TTS服务
            if not siliconflow_service.api_key:
                raise HTTPException(
                    status_code=503, 
                    detail="硅基流动语音合成服务暂时不可用，请配置SILICONFLOW_API_KEY环境变量"
                )
            
            # 硅基流动的音色格式处理
            sf_model = model or "FunAudioLLM/CosyVoice2-0.5B"
            sf_voice = voice if ":" in voice else f"{sf_model}:{voice}"
            
            audio_data = await siliconflow_service.text_to_speech(
                text=text, 
                model=sf_model,
                voice=sf_voice
            )
        else:
            # 使用通义千问TTS服务（默认）
            if not qwen_service.api_key or qwen_service.api_key == "your_qwen_api_key_here":
                raise HTTPException(
                    status_code=503, 
                    detail="通义千问语音合成服务暂时不可用，请配置QWEN_API_KEY环境变量"
                )
            
            audio_data = await qwen_service.text_to_speech(text, voice)
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=speech.mp3"}
            )
        else:
            raise HTTPException(
                status_code=503, 
                detail=f"{provider}语音合成服务暂时不可用，请检查API配置或网络连接"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS服务错误: {str(e)}")

@router.post("/asr")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    语音转文本API
    """
    try:
        # 检查文件类型
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="请上传音频文件")
        
        # 检查API密钥是否配置
        if not qwen_service.api_key or qwen_service.api_key == "your_qwen_api_key_here":
            return {
                "success": False,
                "text": "",
                "error": "语音识别服务暂时不可用，请配置QWEN_API_KEY环境变量"
            }
        
        # 读取音频数据
        audio_data = await audio.read()
        
        # 获取文件格式
        file_format = "wav"
        if audio.content_type == "audio/mpeg":
            file_format = "mp3"
        elif audio.content_type == "audio/wav":
            file_format = "wav"
        elif audio.content_type == "audio/webm":
            file_format = "webm"
        
        # 调用通义千问ASR服务
        text = await qwen_service.speech_to_text(audio_data, file_format)
        
        if text:
            return {
                "success": True,
                "text": text
            }
        else:
            return {
                "success": False,
                "text": "",
                "error": "语音识别服务暂时不可用，请检查API配置或网络连接"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"ASR服务错误: {str(e)}"
        }

@router.get("/voices")
async def get_available_voices(provider: Optional[str] = None):
    """
    获取可用的语音列表
    支持按提供商筛选：qwen（通义千问）、siliconflow（硅基流动）
    """
    # 通义千问语音列表
    qwen_voices = [
        {"id": "zhixiaoxia", "name": "知小夏", "gender": "female", "language": "zh-CN", "provider": "qwen"},
        {"id": "zhichu", "name": "知楚", "gender": "male", "language": "zh-CN", "provider": "qwen"},
        {"id": "zhimiao", "name": "知妙", "gender": "female", "language": "zh-CN", "provider": "qwen"},
        {"id": "zhixiaobai", "name": "知小白", "gender": "male", "language": "zh-CN", "provider": "qwen"},
        {"id": "zhiyan", "name": "知燕", "gender": "female", "language": "zh-CN", "provider": "qwen"}
    ]
    
    # 硅基流动语音列表
    siliconflow_voices = await siliconflow_service.get_available_voices()
    for voice in siliconflow_voices:
        voice["provider"] = "siliconflow"
    
    # 根据提供商筛选
    if provider == "qwen":
        return {"voices": qwen_voices}
    elif provider == "siliconflow":
        return {"voices": siliconflow_voices}
    else:
        # 返回所有语音
        all_voices = qwen_voices + siliconflow_voices
        return {"voices": all_voices}

@router.post("/test-connection")
async def test_api_connection(request: Dict[str, Any] = None):
    """
    测试API连接
    支持测试不同的语音提供商
    """
    provider = "qwen"  # 默认测试通义千问
    if request:
        provider = request.get("provider", "qwen")
    
    try:
        if provider == "siliconflow":
            # 测试硅基流动连接
            result = await siliconflow_service.test_connection()
            return result
        else:
            # 测试通义千问连接（默认）
            if not hasattr(qwen_service, 'api_key') or not qwen_service.api_key or qwen_service.api_key == "your_qwen_api_key_here":
                return {
                    "success": False,
                    "message": "请先配置QWEN_API_KEY环境变量",
                    "suggestion": "您可以在环境变量中设置QWEN_API_KEY，或考虑使用硅基流动语音服务"
                }
            
            # 测试一个简单的文本生成
            response = await qwen_service.generate_response("你好")
            
            return {
                "success": True,
                "message": "通义千问API连接正常",
                "test_response": response
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"{provider} API连接失败: {str(e)}",
            "suggestion": "请检查网络连接和API密钥配置"
        }

@router.get("/providers")
async def get_voice_providers():
    """
    获取可用的语音提供商列表
    """
    providers = [
        {
            "id": "qwen",
            "name": "通义千问",
            "description": "阿里云通义千问语音合成服务",
            "available": bool(qwen_service.api_key and qwen_service.api_key != "your_qwen_api_key_here")
        },
        {
            "id": "siliconflow",
            "name": "硅基流动",
            "description": "硅基流动语音合成服务，支持多种高质量语音模型",
            "available": bool(siliconflow_service.api_key)
        }
    ]
    
    return {"providers": providers}