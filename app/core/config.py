from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///D:/Projects/PortfolioAI/portfolio-backend/test.db"  # updated absolute path
    SECRET_KEY: str = "your_secret_key"
    ALLOWED_HOSTS: list = ["*"]
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()