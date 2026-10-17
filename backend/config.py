import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "*"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_USE_SSL: bool = False
    REDIS_URL: Optional[str] = None

    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND_URL: Optional[str] = None

    TASK_SIMULATION_SECONDS: int = 2

    ENABLE_REAL_EMAIL: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    BREVO_API_KEY: Optional[str] = None

    model_config = {
        "env_file": [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
            os.path.join(os.path.dirname(__file__), ".env"),
            ".env",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.example"),
            os.path.join(os.path.dirname(__file__), ".env.example"),
            ".env.example",
        ],
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
        if self.REDIS_URL:
            return self.REDIS_URL
        return self._build_redis_url()

    @property
    def celery_result_backend_url(self) -> str:
        if self.CELERY_RESULT_BACKEND_URL:
            return self.CELERY_RESULT_BACKEND_URL
        if self.REDIS_URL:
            return self.REDIS_URL
        return self._build_redis_url()

    def safe_dict(self) -> dict:
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
