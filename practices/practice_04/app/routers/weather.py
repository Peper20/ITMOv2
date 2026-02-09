"""
Weather router for PythonNotify application.

This module contains API endpoints for retrieving weather data.
It demonstrates async endpoint patterns and integration with external APIs.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Optional

from app.models import WeatherAPIResponse, ErrorResponse
from app.services.weather import WeatherService
from app.services.subscription import SubscriptionService
from app.core.dependencies import get_weather_service, get_subscription_service

# Create router with prefix and tags
router = APIRouter(
    prefix="/weather",
    tags=["weather"],
    responses={
        404: {"description": "City not found"},
        503: {"description": "Service unavailable"},
        504: {"description": "Gateway timeout"}
    }
)


@router.get(
    "/{city}",
    response_model=WeatherAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current weather for a city",
    description="Retrieve current weather data for a specific city from OpenWeatherMap API."
)
async def get_weather(
    city: str,
    weather_service: WeatherService = Depends(get_weather_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> WeatherAPIResponse:
    """
    Get current weather data for a city.
    
    This endpoint fetches real-time weather data from OpenWeatherMap API.
    The data includes temperature, humidity, conditions, and more.
    
    Args:
        city: City name to fetch weather for (URL path parameter)
        
    Returns:
        WeatherAPIResponse: Weather data with metadata
        
    Raises:
        HTTPException 404: City not found in weather API
        HTTPException 503: Weather service unavailable
        HTTPException 504: Request timeout
        
    Example:
        GET /weather/Moscow
        
        Response:
        ```json
        {
            "data": {
                "city": "Moscow",
                "temperature": 15.5,
                "feels_like": 12.3,
                "humidity": 65,
                "pressure": 1013,
                "condition": "Clouds",
                "description": "scattered clouds",
                "wind_speed": 3.2,
                "visibility": 10000
            },
            "timestamp": "2023-10-25T14:30:00Z",
            "source": "OpenWeatherMap",
            "cached": false
        }
        ```
    """
    # Check if city is subscribed (for potential future features)
    is_subscribed = subscription_service.is_subscribed(city)
    
    # Fetch weather data
    weather_data = await weather_service.get_weather(city)
    
    return WeatherAPIResponse(
        data=weather_data,
        source="OpenWeatherMap",
        cached=False  # Currently not implementing cache flag in response
    )


@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get weather for all subscribed cities",
    description="Retrieve weather data for all currently subscribed cities.",
    include_in_schema=False  # Optional: hide from docs if not fully implemented
)
async def get_weather_for_subscriptions(
    weather_service: WeatherService = Depends(get_weather_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> dict:
    """
    Get weather data for all subscribed cities.
    
    This endpoint demonstrates fetching data for multiple cities concurrently.
    It's a bonus feature that shows async gathering patterns.
    
    Returns:
        dict: Weather data for all subscribed cities
        
    Example:
        Response:
        ```json
        {
            "weather_data": {
                "Moscow": { ... },
                "London": { ... }
            },
            "timestamp": "2023-10-25T14:30:00Z"
        }
        ```
    """
    subscriptions = subscription_service.get_all_subscriptions()
    cities = subscriptions.subscriptions
    
    if not cities:
        return {
            "message": "No subscriptions found",
            "weather_data": {}
        }
    
    # Fetch weather for all cities concurrently
    weather_data = await weather_service.get_weather_for_multiple_cities(cities)
    
    return {
        "weather_data": {city: data.dict() if data else None for city, data in weather_data.items()},
        "timestamp": subscriptions.timestamp
    }


@router.delete(
    "/cache",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Clear weather cache (admin)",
    description="Clear the weather data cache (for testing and admin purposes).",
    include_in_schema=False  # Hide from public API docs
)
async def clear_weather_cache(
    weather_service: WeatherService = Depends(get_weather_service)
) -> dict:
    """
    Clear the weather data cache.
    
    This endpoint is for testing and administrative purposes only.
    It clears all cached weather data.
    
    Returns:
        dict: Confirmation message
        
    Example:
        Response:
        ```json
        {
            "status": "cleared",
            "message": "Weather cache cleared"
        }
        ```
    """
    weather_service.clear_cache()
    return {
        "status": "cleared",
        "message": "Weather cache cleared"
    }