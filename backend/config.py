"""
Centralized Configuration Module
Provides strongly-typed, validated configuration with environment variable support,
safe defaults for development, and secret masking for safe logging.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")
    BACKEND_HOST: str = Field(default="0.0.0.0", description="Backend host bind address")
    BACKEND_PORT: int = Field(default=8000, description="Backend port")
    CORS_ORIGINS: str = Field(default="*", description="Comma-separated CORS origins or '*'")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis hostname or endpoint")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password for AUTH")
    REDIS_DB: int = Field(default=0, description="Redis DB index")
    REDIS_USE_SSL: bool = Field(default=False, description="Enable TLS/SSL for ElastiCache in-transit encryption")

    # Celery Override URLs (optional, derived if not set)
    CELERY_BROKER_URL: Optional[str] = Field(default=None, description="Explicit Celery broker URL override")
    CELERY_RESULT_BACKEND_URL: Optional[str] = Field(default=None, description="Explicit Celery result backend URL override")

    # Task Settings
    TASK_SIMULATION_SECONDS: int = Field(default=2, description="Simulated duration for background work in seconds")

    # Real Email Delivery Settings (SMTP)
    ENABLE_REAL_EMAIL: bool = Field(default=False, description="Enable real outbound email delivery")
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP server hostname")
    SMTP_PORT: int = Field(default=587, description="SMTP server port (587 for TLS)")
    SMTP_USER: Optional[str] = Field(default=None, description="Sender Gmail/SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="Gmail 16-character App Password")
    SMTP_FROM: Optional[str] = Field(default=None, description="From header email address")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def _build_redis_url(self) -> str:
        protocol = "rediss" if self.REDIS_USE_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def celery_broker_url(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return self._build_redis_url()

    @property
    def celery_result_backend_url(self) -> str:
        if self.CELERY_RESULT_BACKEND_URL:
            return self.CELERY_RESULT_BACKEND_URL
        return self._build_redis_url()

    def safe_dict(self) -> dict:
        """Returns configuration dictionary with secrets masked for safe logging/inspection."""
        return {
            "ENVIRONMENT": self.ENVIRONMENT,
            "LOG_LEVEL": self.LOG_LEVEL,
            "BACKEND_HOST": self.BACKEND_HOST,
            "BACKEND_PORT": self.BACKEND_PORT,
            "CORS_ORIGINS": self.CORS_ORIGINS,
            "REDIS_HOST": self.REDIS_HOST,
            "REDIS_PORT": self.REDIS_PORT,
            "REDIS_PASSWORD_CONFIGURED": bool(self.REDIS_PASSWORD),
            "REDIS_DB": self.REDIS_DB,
            "REDIS_USE_SSL": self.REDIS_USE_SSL,
            "CELERY_BROKER_MASKED": self._mask_url(self.celery_broker_url),
            "CELERY_BACKEND_MASKED": self._mask_url(self.celery_result_backend_url),
            "ENABLE_REAL_EMAIL": self.ENABLE_REAL_EMAIL,
            "SMTP_HOST": self.SMTP_HOST,
            "SMTP_PORT": self.SMTP_PORT,
            "SMTP_USER": self.SMTP_USER,
            "SMTP_PASSWORD_CONFIGURED": bool(self.SMTP_PASSWORD),
        }

    @staticmethod
    def _mask_url(url: str) -> str:
        if not url:
            return ""
        if "@" in url:
            scheme_and_auth, rest = url.split("@", 1)
            scheme = scheme_and_auth.split("://")[0]
            return f"{scheme}://***:***@{rest}"
        return url


settings = Settings()
