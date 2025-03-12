from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    """Базовые настройки фреймворка."""
    
    # Database settings
    DATABASE_URL: str = "sqlite:///AgentForge.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings() 