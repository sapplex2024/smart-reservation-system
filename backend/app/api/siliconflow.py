from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import httpx
import json

from ..models.database import get_db
from ..api.auth import get_current_user

router = APIRouter()

# 硅基流动配置模型
class SiliconFlowConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.siliconflow.cn/v1"
    default_model: str = "Qwen/Qwen2.5-72B-Instruct"
    max_tokens: int = 4096
    temperature: float = 0.7
    stream: bool = True

# 模型信息
class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    provider: str
    type: str  # chat, completion, embedding, etc.
    max_tokens: int
    pricing: Optional[Dict[str, float]] = None

# API测试请求
class APITestRequest(BaseModel):
    api_key: str
    base_url: str
    model: str
    message: str = "你好，请介绍一下你自己。"
    max_tokens: int = 100
    temperature: float = 0.7

# API测试响应
class APITestResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    latency: Optional[float] = None
    tokens_used: Optional[int] = None

# 硅基流动支持的模型列表 <mcreference link="https://docs.siliconflow.cn/cn/userguide/quickstart" index="1">1</mcreference> <mcreference link="https://zhuanlan.zhihu.com/p/18966056589" index="2">2</mcreference>
SILICONFLOW_MODELS = [
    {
        "id": "Qwen/Qwen2.5-72B-Instruct",
        "name": "Qwen2.5-72B-Instruct",
        "description": "通义千问2.5-72B指令模型，适合对话和文本生成",
        "provider": "Alibaba",
        "type": "chat",
        "max_tokens": 32768,
        "pricing": {"input": 0.0005, "output": 0.002}
    },
    {
        "id": "deepseek-ai/DeepSeek-R1",
        "name": "DeepSeek-R1",
        "description": "DeepSeek推理模型，具备强大的推理能力",
        "provider": "DeepSeek",
        "type": "chat",
        "max_tokens": 4096,
        "pricing": {"input": 0.0014, "output": 0.0028}
    },
    {
        "id": "Pro/deepseek-ai/DeepSeek-R1",
        "name": "DeepSeek-R1 Pro",
        "description": "DeepSeek推理模型专业版",
        "provider": "DeepSeek",
        "type": "chat",
        "max_tokens": 4096,
        "pricing": {"input": 0.002, "output": 0.004}
    },
    {
        "id": "Qwen/QwQ-32B",
        "name": "QwQ-32B",
        "description": "通义千问QwQ-32B模型",
        "provider": "Alibaba",
        "type": "chat",
        "max_tokens": 32768,
        "pricing": {"input": 0.0003, "output": 0.0012}
    },
    {
        "id": "meta-llama/Llama-3.1-405B-Instruct",
        "name": "Llama-3.1-405B-Instruct",
        "description": "Meta Llama 3.1 405B指令模型",
        "provider": "Meta",
        "type": "chat",
        "max_tokens": 4096,
        "pricing": {"input": 0.003, "output": 0.006}
    },
    {
        "id": "meta-llama/Llama-3.1-70B-Instruct",
        "name": "Llama-3.1-70B-Instruct",
        "description": "Meta Llama 3.1 70B指令模型",
        "provider": "Meta",
        "type": "chat",
        "max_tokens": 4096,
        "pricing": {"input": 0.0005, "output": 0.001}
    },
    {
        "id": "microsoft/DialoGPT-medium",
        "name": "DialoGPT-medium",
        "description": "微软对话生成模型",
        "provider": "Microsoft",
        "type": "chat",
        "max_tokens": 1024,
        "pricing": {"input": 0.0002, "output": 0.0008}
    },
    {
        "id": "THUDM/glm-4-9b-chat",
        "name": "GLM-4-9B-Chat",
        "description": "智谱AI GLM-4 9B对话模型",
        "provider": "THUDM",
        "type": "chat",
        "max_tokens": 8192,
        "pricing": {"input": 0.0001, "output": 0.0005}
    },
    # 语音合成模型
    {
        "id": "FunAudioLLM/CosyVoice2-0.5B",
        "name": "CosyVoice2-0.5B",
        "description": "CosyVoice2语音合成模型，支持多种音色和情感表达",
        "provider": "FunAudioLLM",
        "type": "tts",
        "max_tokens": 4096,
        "pricing": {"input": 0.0001, "output": 0.0002},
        "voices": ["alex", "anna", "bella", "chris", "diana", "eric"]
    },
    {
        "id": "fishaudio/fish-speech-1.4",
        "name": "Fish Speech 1.4",
        "description": "Fish Audio语音合成模型，高质量自然语音生成",
        "provider": "FishAudio",
        "type": "tts",
        "max_tokens": 4096,
        "pricing": {"input": 0.0001, "output": 0.0002},
        "voices": ["alex", "bella", "chris", "diana"]
    }
]

@router.get("/models", response_model=List[ModelInfo])
async def get_available_models(
    current_user: dict = Depends(get_current_user)
):
    """获取硅基流动支持的模型列表"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问模型管理"
        )
    
    return [ModelInfo(**model) for model in SILICONFLOW_MODELS]

@router.post("/test", response_model=APITestResponse)
async def test_api_connection(
    test_request: APITestRequest,
    current_user: dict = Depends(get_current_user)
):
    """测试硅基流动API连接 <mcreference link="https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions" index="2">2</mcreference>"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以测试API连接"
        )
    
    import time
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {test_request.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": test_request.model,
                "messages": [
                    {"role": "user", "content": test_request.message}
                ],
                "max_tokens": test_request.max_tokens,
                "temperature": test_request.temperature,
                "stream": False
            }
            
            response = await client.post(
                f"{test_request.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                return APITestResponse(
                    success=True,
                    response=content,
                    latency=latency,
                    tokens_used=tokens_used
                )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except:
                    pass
                
                return APITestResponse(
                    success=False,
                    error=f"API请求失败 (状态码: {response.status_code}): {error_detail}",
                    latency=latency
                )
                
    except httpx.TimeoutException:
        return APITestResponse(
            success=False,
            error="API请求超时，请检查网络连接或API地址",
            latency=time.time() - start_time
        )
    except Exception as e:
        return APITestResponse(
            success=False,
            error=f"连接失败: {str(e)}",
            latency=time.time() - start_time
        )

@router.get("/config")
async def get_siliconflow_config(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取硅基流动配置"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看配置"
        )
    
    # 从系统设置中获取配置
    from ..models.database import SystemSetting
    
    config = {}
    settings = db.query(SystemSetting).filter(
        SystemSetting.category == "siliconflow"
    ).all()
    
    for setting in settings:
        config[setting.key] = setting.value
    
    # 设置默认值
    default_config = {
        "api_key": "",
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Qwen/Qwen2.5-72B-Instruct",
        "max_tokens": "4096",
        "temperature": "0.7",
        "stream": "true"
    }
    
    for key, default_value in default_config.items():
        if key not in config:
            config[key] = default_value
    
    return config

@router.post("/config")
async def update_siliconflow_config(
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新硅基流动配置"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改配置"
        )
    
    from ..models.database import SystemSetting
    
    try:
        # 更新或创建配置项
        for key, value in config.items():
            setting = db.query(SystemSetting).filter(
                SystemSetting.category == "siliconflow",
                SystemSetting.key == key
            ).first()
            
            if setting:
                setting.value = str(value)
            else:
                setting = SystemSetting(
                    category="siliconflow",
                    key=key,
                    value=str(value),
                    description=f"硅基流动{key}配置"
                )
                db.add(setting)
        
        db.commit()
        return {"message": "配置更新成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置更新失败: {str(e)}"
        )

@router.get("/usage")
async def get_api_usage(
    current_user: dict = Depends(get_current_user)
):
    """获取API使用统计（模拟数据）"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看使用统计"
        )
    
    # 这里返回模拟数据，实际应该从数据库或日志中统计
    return {
        "total_requests": 1250,
        "total_tokens": 125000,
        "total_cost": 12.50,
        "today_requests": 45,
        "today_tokens": 4500,
        "today_cost": 0.45,
        "popular_models": [
            {"model": "Qwen/Qwen2.5-72B-Instruct", "requests": 800, "percentage": 64},
            {"model": "deepseek-ai/DeepSeek-R1", "requests": 300, "percentage": 24},
            {"model": "meta-llama/Llama-3.1-70B-Instruct", "requests": 150, "percentage": 12}
        ]
    }