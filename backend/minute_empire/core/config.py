import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Minute Empire"
    
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/minute_empire")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "minute_empire")
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:8080",  # Vue.js frontend
        "http://localhost:3000",
    ]
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 