import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API settings
    PROJECT_NAME: str = "Komornicka 100"
    API_V1_STR: str = "/api"
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    
    # Database settings
    DATABASE_URL: str
    
    # CORS settings for frontend
    FRONTEND_URL: str
    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Strava API settings
    STRAVA_CLIENT_ID: str
    STRAVA_CLIENT_SECRET: str
    
    # Email settings
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    
    # Token settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    EMAIL_TOKEN_EXPIRE_HOURS: int = 48     # 48 hours
    
    # GPX file path
    SOURCE_GPX_PATH: str = "data"
    
    # GPX verification settings
    ROUTE_SIMILARITY_THRESHOLD: float = 0.8  # 80% similarity required for verification
    GPS_MAX_DEVIATION_METERS: float = 20.0   # 20 meters max deviation
    MIN_ACTIVITY_DISTANCE_KM: float = 100.0  # 100 kilometers minimum required

    # Model config
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


# Create global settings object
settings = Settings()