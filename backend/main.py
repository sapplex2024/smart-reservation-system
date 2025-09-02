from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import chat, reservations, auth, ai_config, smart_reservation
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="Smart Reservation System",
    description="基于大模型的智能预约系统",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(reservations.router, prefix="/api/v1/reservations", tags=["reservations"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(ai_config.router, prefix="/api/v1/ai", tags=["ai-config"])
app.include_router(smart_reservation.router, prefix="/api/smart-reservation", tags=["smart-reservation"])

@app.get("/")
async def root():
    return {"message": "Smart Reservation System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)