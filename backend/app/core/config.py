from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Smart Reservation System"
    
    # Database
    DATABASE_URL: str = "sqlite:///./reservations.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI API (备用)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 阿里云通义千问API
    QWEN_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-turbo"
    
    # 硅基流动API配置
    SILICONFLOW_API_KEY: Optional[str] = None
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_CHAT_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    SILICONFLOW_TTS_MODEL: str = "FishAudio/fish-speech-1.4"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    """获取配置实例"""
    return settings