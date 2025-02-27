from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создание экземпляра настроек
settings = Settings()
