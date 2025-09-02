from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json
from datetime import datetime

from ..models.database import get_db, SystemSettings
from ..api.auth import get_current_user
from ..models.database import User

router = APIRouter()

class AIConfigRequest(BaseModel):
    provider: str
    model: str
    baseUrl: str
    apiKey: str
    xunfei: Optional[Dict[str, str]] = None
    qwen: Optional[Dict[str, str]] = None
    siliconflow: Optional[Dict[str, str]] = None
    openai: Optional[Dict[str, str]] = None

@router.get("/config")
async def get_ai_config(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # 手动获取查询参数
        show_keys = request.query_params.get('show_keys', 'false').lower() == 'true'
        setting = db.query(SystemSettings).filter(
            SystemSettings.category == "ai",
            SystemSettings.key == "config"
        ).first()
        
        if setting and setting.value:
            config = json.loads(setting.value)
            # 根据show_keys参数决定是否遮蔽API密钥
            if not show_keys:
                for key in ['apiKey']:
                    if config.get(key):
                        config[key] = "***"
                for provider in ['xunfei', 'qwen', 'siliconflow', 'openai']:
                    if provider in config and isinstance(config[provider], dict):
                        for key in ['apiKey', 'apiSecret']:
                            if config[provider].get(key):
                                config[provider][key] = "***"
            return {"success": True, "config": config}
        else:
            return {"success": True, "config": {
                "provider": "siliconflow",
                "model": "Qwen/Qwen2.5-72B-Instruct",
                "baseUrl": "https://api.siliconflow.cn/v1",
                "apiKey": "",
                "xunfei": {"appId": "", "apiSecret": "", "apiKey": ""},
                "qwen": {"apiKey": ""},
                "siliconflow": {"apiKey": "", "customModel": ""},
                "openai": {"apiKey": "", "organization": ""}
            }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def save_ai_config(
    config: AIConfigRequest,
    db: Session = Depends(get_db)
):
    try:
        config_data = config.dict()
        
        setting = db.query(SystemSettings).filter(
            SystemSettings.category == "ai",
            SystemSettings.key == "config"
        ).first()
        
        if setting:
            setting.value = json.dumps(config_data)
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSettings(
                category="ai",
                key="config",
                value=json.dumps(config_data),
                description="AI服务配置"
            )
            db.add(setting)
        
        db.commit()
        return {"success": True, "message": "配置保存成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))