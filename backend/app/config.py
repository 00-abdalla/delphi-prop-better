"""Application configuration using Pydantic Settings."""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://delphi:delphi@localhost:5432/delphi_ai"
    
    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Delphi"
    API_VERSION: str = "1.0.0"
    
    # Models
    MODEL_DIR: str = "./models"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Discord Bot
    DISCORD_BOT_TOKEN: Optional[str] = None
    API_BASE_URL: str = "http://localhost:8000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_model_dir_path(self) -> Path:
        """Get Path object for model directory."""
        path = Path(self.MODEL_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()
