"""
BreastHealth Monitor - Backend Configuration
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./breast_monitor.db"
    )
    
    # API
    API_PREFIX: str = "/api"
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    # Files
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Analysis thresholds
    ASYMMETRY_NORMAL: float = 0.5  # °C
    ASYMMETRY_ELEVATED: float = 1.0  # °C
    TEMP_NORMAL_MAX: float = 37.5  # °C
    TEMP_ELEVATED_MAX: float = 38.0  # °C
    
    # LLM 
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
