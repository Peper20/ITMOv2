"""
Weather service for PythonNotify application.

This module handles integration with OpenWeatherMap API using async patterns.
It demonstrates proper error handling, caching, and async/await patterns.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, status

from app.models import WeatherData, ErrorResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service class for weather data integration with OpenWeatherMap API.
    
    This service demonstrates:
    - Async/await patterns with httpx
    - Comprehensive error handling
    - Response caching
    - Data transformation
    - Rate limiting considerations
    """
    
    def __init__(self):
        """Initialize weather service with cache and client settings."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(seconds=settings.cache_ttl_seconds)
        logger.info("Weather service initialized")
    
    async def get_weather(self, city: str) -> WeatherData:
        """
        Get current weather data for a city.
        
        Args:
            city: City name to fetch weather for
            
        Returns:
            WeatherData: Transformed weather data
            
        Raises:
            HTTPException: For various error conditions (404, 503, 504, etc.)
        """
        # Check cache first
        cached_data = self._get_cached_weather(city)
        if cached_data:
            logger.debug(f"Serving cached weather data for {city}")
            return cached_data
        
        try:
            # Fetch from API
            raw_data = await self._fetch_weather_from_api(city)
            
            # Transform and cache
            weather_data = self._transform_weather_data(raw_data, city)
            self._cache_weather(city, weather_data)
            
            return weather_data
            
        except httpx.TimeoutException:
            logger.error(f"Weather API timeout for city: {city}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Weather service timeout"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"City not found: {city}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"City '{city}' not found"
                )
            else:
                logger.error(f"Weather API error for {city}: {e.response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Weather service unavailable"
                )
        except Exception as e:
            logger.error(f"Unexpected error fetching weather for {city}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _fetch_weather_from_api(self, city: str) -> Dict[str, Any]:
        """
        Fetch raw weather data from OpenWeatherMap API.
        
        Args:
            city: City name to fetch weather for
            
        Returns:
            Dict: Raw API response data
            
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If API returns error status
        """
        url = f"{settings.openweather_base_url}/weather"
        params = {
            "q": city,
            "appid": settings.openweather_api_key,
            "units": "metric"  # Get temperature in Celsius
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=settings.weather_request_timeout
            )
            response.raise_for_status()
            return response.json()
    
    def _transform_weather_data(self, raw_data: Dict[str, Any], city: str) -> WeatherData:
        """
        Transform raw API response to standardized WeatherData model.
        
        Args:
            raw_data: Raw response from OpenWeatherMap API
            city: City name for the data
            
        Returns:
            WeatherData: Standardized weather data
        """
        main_data = raw_data.get("main", {})
        weather_info = raw_data.get("weather", [{}])[0]
        wind_data = raw_data.get("wind", {})
        
        return WeatherData(
            city=city,
            temperature=main_data.get("temp", 0),
            feels_like=main_data.get("feels_like", 0),
            humidity=main_data.get("humidity", 0),
            pressure=main_data.get("pressure", 0),
            condition=weather_info.get("main", "Unknown"),
            description=weather_info.get("description", "No description"),
            wind_speed=wind_data.get("speed", 0),
            visibility=raw_data.get("visibility", 0)
        )
    
    def _get_cached_weather(self, city: str) -> Optional[WeatherData]:
        """
        Get weather data from cache if available and not expired.
        
        Args:
            city: City name to check in cache
            
        Returns:
            Optional[WeatherData]: Cached data if available and valid, else None
        """
        if city not in self._cache:
            return None
        
        cache_entry = self._cache[city]
        cache_time = cache_entry.get("timestamp")
        
        if not cache_time or datetime.now() - cache_time > self._cache_ttl:
            # Cache expired
            del self._cache[city]
            return None
        
        return cache_entry["data"]
    
    def _cache_weather(self, city: str, weather_data: WeatherData) -> None:
        """
        Cache weather data with timestamp.
        
        Args:
            city: City name for cache key
            weather_data: Weather data to cache
        """
        self._cache[city] = {
            "data": weather_data,
            "timestamp": datetime.now()
        }
        logger.debug(f"Weather data cached for {city}")
    
    def clear_cache(self) -> None:
        """Clear the weather cache (for testing purposes)."""
        self._cache.clear()
        logger.info("Weather cache cleared")
    
    async def get_weather_for_multiple_cities(self, cities: list[str]) -> Dict[str, WeatherData]:
        """
        Get weather for multiple cities concurrently.
        
        Args:
            cities: List of city names
            
        Returns:
            Dict mapping city names to WeatherData (or None for errors)
        """
        tasks = [self.get_weather(city) for city in cities]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        weather_data = {}
        for city, result in zip(cities, results):
            if isinstance(result, WeatherData):
                weather_data[city] = result
            else:
                logger.warning(f"Failed to get weather for {city}: {result}")
                weather_data[city] = None
        
        return weather_data


# Global service instance for dependency injection
weather_service = WeatherService()