from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from app.models.database import get_db, User
from app.core.config import settings

# 导入路由
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.reservations import router as reservations_router
from app.api.resources import router as resources_router
from app.api.voice import router as voice_router
from app.api.voice_config import router as voice_config_router
from .api.notifications import router as notifications_router
from .api.reports import router as reports_router
from .api.settings import router as settings_router
from .api.logs import router as logs_router
from .api.siliconflow import router as siliconflow_router
from .api.smart_reservation import router as smart_reservation_router
from .api.ai_config import router as ai_config_router
from app.services.qwen_service import qwen_service

# 创建FastAPI应用实例
app = FastAPI(
    title="智能预约系统 API",
    description="基于大模型的智能预约管理系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 导入中间件和异常处理器
from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加错误处理中间件
app.add_middleware(ErrorHandlerMiddleware)

# 注册异常处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(chat_router, prefix="/api/chat", tags=["智能对话"])
app.include_router(reservations_router, prefix="/api/reservations", tags=["预约管理"])
app.include_router(resources_router, prefix="/api/resources", tags=["资源管理"])
app.include_router(voice_router, prefix="/api/voice", tags=["语音服务"])
app.include_router(voice_config_router, prefix="/api/voice", tags=["语音配置"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["通知管理"])
app.include_router(reports_router, prefix="/api/reports", tags=["报表管理"])
app.include_router(settings_router, prefix="/api/settings", tags=["系统设置"])
app.include_router(logs_router, prefix="/api/logs", tags=["日志管理"])
app.include_router(siliconflow_router, prefix="/api/siliconflow", tags=["硅基流动模型管理"])
app.include_router(smart_reservation_router, prefix="/api/smart-reservation", tags=["智能预约"])
app.include_router(ai_config_router, prefix="/api/v1/ai", tags=["AI配置管理"])

# 根路径
@app.get("/")
async def root():
    return {
        "message": "智能预约系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 启动事件
@app.on_event("startup")
async def startup_event():
    print("智能预约系统 API 启动成功")
    print(f"API文档地址: http://localhost:8000/docs")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    print("智能预约系统 API 关闭")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )