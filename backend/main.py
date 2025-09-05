from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from app.api import chat, reservations, auth, ai_config, smart_reservation, resources, notifications, reports, logs, siliconflow
from app.api import settings as settings_api
from app.core.config import settings
from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Create FastAPI app
app = FastAPI(
    title="Smart Reservation System",
    description="基于大模型的智能预约系统",
    version="1.0.0"
)

# Add error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(reservations.router, prefix="/api/v1/reservations", tags=["reservations"])
app.include_router(resources.router, prefix="/api/resources", tags=["resources"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ai_config.router, prefix="/api/v1/ai", tags=["ai-config"])
app.include_router(smart_reservation.router, prefix="/api/smart-reservation", tags=["smart-reservation"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(siliconflow.router, prefix="/api/siliconflow", tags=["siliconflow"])

@app.get("/")
async def root():
    return {"message": "Smart Reservation System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)