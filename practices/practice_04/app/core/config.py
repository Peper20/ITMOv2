"""
Configuration settings for PythonNotify application.

This module handles environment variables and application settings using Pydantic BaseSettings.
All sensitive configuration should be loaded from environment variables.
"""

from pydantic import BaseSettings, Field, validator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic.BaseSettings for automatic environment variable loading.
    Required variables must be set in .env file or environment.
    """
    
    # OpenWeatherMap API configuration
    openweather_api_key: str = Field(
        ...,
        description="OpenWeatherMap API key (required)",
        env="OPENWEATHER_API_KEY"
    )
    
    openweather_base_url: str = Field(
        "https://api.openweathermap.org/data/2.5",
        description="OpenWeatherMap API base URL",
        env="OPENWEATHER_BASE_URL"
    )
    
    # Application settings
    app_name: str = Field(
        "PythonNotify",
        description="Application name",
        env="APP_NAME"
    )
    
    app_version: str = Field(
        "1.0.0",
        description="Application version",
        env="APP_VERSION"
    )
    
    debug: bool = Field(
        False,
        description="Debug mode flag",
        env="DEBUG"
    )
    
    # API request settings
    weather_request_timeout: int = Field(
        10,
        description="Timeout in seconds for weather API requests",
        env="WEATHER_REQUEST_TIMEOUT"
    )
    
    max_subscriptions: int = Field(
        100,
        description="Maximum number of subscriptions allowed",
        env="MAX_SUBSCRIPTIONS"
    )
    
    # Cache settings
    cache_ttl_seconds: int = Field(
        300,
        description="Time-to-live for weather cache in seconds",
        env="CACHE_TTL_SECONDS"
    )
    
    class Config:
        """Pydantic configuration for settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('openweather_api_key')
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is provided and not empty."""
        if not v or not v.strip():
            raise ValueError('OpenWeatherMap API key is required')
        return v.strip()
    
    @validator('weather_request_timeout')
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is within reasonable range."""
        if v < 1 or v > 30:
            raise ValueError('Timeout must be between 1 and 30 seconds')
        return v
    
    @validator('max_subscriptions')
    def validate_max_subscriptions(cls, v: int) -> int:
        """Validate maximum subscriptions is reasonable."""
        if v < 1 or v > 1000:
            raise ValueError('Max subscriptions must be between 1 and 1000')
        return v


# Global settings instance
settings = Settings()

# Log configuration loading
logger.info(f"Loaded configuration for {settings.app_name} v{settings.app_version}")
logger.info(f"OpenWeatherMap base URL: {settings.openweather_base_url}")
logger.info(f"Debug mode: {settings.debug}")