"""
Pydantic models for PythonNotify application.

This module defines all data models for requests, responses, and internal data structures.
All models include comprehensive validation and documentation for educational purposes.
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List, Dict
from datetime import datetime
import re


class SubscriptionRequest(BaseModel):
    """
    Request model for subscribing to weather notifications.
    
    This model validates the city name before processing the subscription.
    """
    
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City name for weather subscription",
        example="Moscow"
    )
    
    @field_validator('city')
    @classmethod
    def validate_city(cls, v: str) -> str:
        """
        Validate city name is not empty and contains only letters, spaces, and hyphens.
        
        Args:
            v: City name to validate
            
        Returns:
            str: Trimmed and validated city name
            
        Raises:
            ValueError: If city name is empty or contains invalid characters
        """
        if not v or not v.strip():
            raise ValueError('City name cannot be empty')
        
        city = v.strip()
        
        # Allow letters, spaces, hyphens, and apostrophes for city names
        if not re.match(r'^[a-zA-Z\s\-\']+$', city):
            raise ValueError('City name can only contain letters, spaces, hyphens, and apostrophes')
        
        return city


class SubscriptionResponse(BaseModel):
    """
    Response model for subscription operations.
    
    Returns status and city information after subscription actions.
    """
    
    status: str = Field(
        ...,
        description="Operation status",
        example="subscribed"
    )
    
    city: str = Field(
        ...,
        description="City name",
        example="Moscow"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Operation timestamp"
    )


class UnsubscriptionRequest(BaseModel):
    """
    Request model for unsubscribing from weather notifications.
    """
    
    city: str = Field(
        ...,
        description="City name to unsubscribe from",
        example="Moscow"
    )
    
    @field_validator('city')
    @classmethod
    def validate_city(cls, v: str) -> str:
        """Validate city name is not empty."""
        if not v or not v.strip():
            raise ValueError('City name cannot be empty')
        return v.strip()


class UnsubscriptionResponse(BaseModel):
    """
    Response model for unsubscription operations.
    """
    
    status: str = Field(
        ...,
        description="Operation status",
        example="unsubscribed"
    )
    
    city: str = Field(
        ...,
        description="City name",
        example="Moscow"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Operation timestamp"
    )


class SubscriptionsListResponse(BaseModel):
    """
    Response model for listing all subscriptions.
    """
    
    subscriptions: List[str] = Field(
        ...,
        description="List of subscribed cities",
        example=["Moscow", "London", "Paris"]
    )
    
    count: int = Field(
        ...,
        description="Number of subscriptions",
        example=3
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )


class WeatherData(BaseModel):
    """
    Weather data model from OpenWeatherMap API.
    
    This model represents the transformed weather data after API response processing.
    """
    
    city: str = Field(
        ...,
        description="City name",
        example="Moscow"
    )
    
    temperature: float = Field(
        ...,
        description="Temperature in Celsius",
        example=15.5
    )
    
    feels_like: float = Field(
        ...,
        description="Feels like temperature in Celsius",
        example=12.3
    )
    
    humidity: int = Field(
        ...,
        ge=0,
        le=100,
        description="Humidity percentage",
        example=65
    )
    
    pressure: int = Field(
        ...,
        ge=800,
        le=1100,
        description="Atmospheric pressure in hPa",
        example=1013
    )
    
    condition: str = Field(
        ...,
        description="Weather condition",
        example="Clouds"
    )
    
    description: str = Field(
        ...,
        description="Weather description",
        example="scattered clouds"
    )
    
    wind_speed: float = Field(
        ...,
        ge=0,
        description="Wind speed in meters per second",
        example=3.2
    )
    
    visibility: int = Field(
        ...,
        ge=0,
        description="Visibility in meters",
        example=10000
    )
    
    @field_validator('temperature', 'feels_like')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within reasonable range."""
        if v < -100 or v > 60:
            raise ValueError('Temperature must be between -100°C and 60°C')
        return round(v, 1)


class WeatherAPIResponse(BaseModel):
    """
    Standard response model for weather API endpoints.
    
    Includes metadata about the response source and caching.
    """
    
    data: WeatherData = Field(
        ...,
        description="Weather data"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
    
    source: str = Field(
        "OpenWeatherMap",
        description="Data source",
        example="OpenWeatherMap"
    )
    
    cached: bool = Field(
        False,
        description="Whether data was served from cache",
        example=False
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model for API errors.
    """
    
    error_type: str = Field(
        ...,
        description="Type of error",
        example="CITY_NOT_FOUND"
    )
    
    message: str = Field(
        ...,
        description="Error message",
        example="City 'InvalidCity' not found"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Error timestamp"
    )
    
    details: Optional[Dict] = Field(
        None,
        description="Additional error details"
    )


class HealthCheckResponse(BaseModel):
    """
    Health check response model.
    """
    
    status: str = Field(
        "healthy",
        description="Service status",
        example="healthy"
    )
    
    version: str = Field(
        ...,
        description="Application version",
        example="1.0.0"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Check timestamp"
    )
    
    dependencies: Dict[str, str] = Field(
        ...,
        description="Dependency status",
        example={"database": "connected", "weather_api": "available"}
    )