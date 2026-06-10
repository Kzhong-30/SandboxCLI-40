from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "public_opinion_db"
    APP_NAME: str = "舆情监控系统"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
