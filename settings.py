from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CALENDAR_TOKEN: str
    GOOGLE_CALENDAR_ID: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создание экземпляра настроек
settings = Settings()
