from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Any
import os
from datetime import timedelta

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///test.db"
    
    # SMTP Settings
    #Set values from .env file
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = os.getenv("SMTP_PORT")
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_TLS: bool = os.getenv("SMTP_TLS")
    SMTP_SSL: bool = os.getenv("SMTP_SSL")
    
    # Security settings
    SECRET_KEY: str = "your_secret_key_here_replace_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    ALLOWED_HOSTS: list[str] = ["*"]
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()