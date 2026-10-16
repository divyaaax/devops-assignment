"""
Unit tests for the centralized configuration module.
Verifies environment variable resolution, defaults, URL construction, and secret masking.
"""

import os
import pytest
from config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.ENVIRONMENT == "development"
    assert settings.BACKEND_PORT == 8000
    assert settings.REDIS_HOST == "localhost" or settings.REDIS_HOST == "redis"
    assert settings.cors_origins_list == ["*"]
    assert "redis://" in settings.celery_broker_url


def test_cors_origins_parsing():
    settings = Settings(CORS_ORIGINS="http://localhost:3000, https://myapp.example.com")
    assert settings.cors_origins_list == ["http://localhost:3000", "https://myapp.example.com"]


def test_ssl_redis_url_generation():
    settings = Settings(
        REDIS_HOST="elasticache.amazonaws.com",
        REDIS_PORT=6379,
        REDIS_USE_SSL=True,
        REDIS_PASSWORD="secret-auth-token",
        REDIS_DB=1,
    )
    assert settings.celery_broker_url == "rediss://:secret-auth-token@elasticache.amazonaws.com:6379/1"
    assert settings.celery_result_backend_url == "rediss://:secret-auth-token@elasticache.amazonaws.com:6379/1"


def test_safe_dict_masks_secrets():
    settings = Settings(
        REDIS_HOST="elasticache.amazonaws.com",
        REDIS_PASSWORD="super-secret-password",
        REDIS_USE_SSL=True,
    )
    safe = settings.safe_dict()
    assert safe["REDIS_PASSWORD_CONFIGURED"] is True
    assert "super-secret-password" not in str(safe)
    assert "super-secret-password" not in safe["CELERY_BROKER_MASKED"]
    assert "***:***" in safe["CELERY_BROKER_MASKED"]
