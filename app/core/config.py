import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Union
from dotenv import load_dotenv

class Settings(BaseSettings):
    # env vars → .env file or container secrets
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = Field("postgresql://postgres:password@localhost:5432/toeic_vocabulary", env="DATABASE_URL")
    
    # Redis settings
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")

    # Firebase settings
    URL_STORAGEBUCKET: Optional[str] = None
    TYPE: Optional[str] = None
    PROJECT_ID: Optional[str] = None
    PRIVATE_KEY_ID: Optional[str] = None
    PRIVATE_KEY: Optional[str] = None
    CLIENT_EMAIL: Optional[str] = None
    CLIENT_ID: Optional[str] = None
    AUTH_URI: Optional[str] = None
    TOKEN_URI: Optional[str] = None
    AUTH_PROVIDER_X509_CERT_URL: Optional[str] = None
    CLIENT_X509_CERT_URL: Optional[str] = None
    UNIVERSE_DOMAIN: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

@lru_cache
def get_settings() -> Settings:
    return Settings()
