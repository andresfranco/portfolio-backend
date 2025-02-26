from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Any

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///D:/Projects/PortfolioAI/portfolio-backend/test.db"
    
    # SMTP Settings
    SMTP_HOST: str = "mail.privateemail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "admin@amfapps.com"
    SMTP_PASSWORD: str = "test"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = True

    SECRET_KEY: str = "your_secret_key"
    ALLOWED_HOSTS: list[str] = ["*"]
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()