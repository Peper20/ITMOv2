"""
Dependency injection for PythonNotify application.

This module provides dependency injection functions for services and other components.
It follows FastAPI's dependency injection pattern for testability and modularity.
"""

from app.services.subscription import subscription_service
from app.services.weather import weather_service


def get_subscription_service() -> type(subscription_service):
    """
    Dependency function for subscription service.
    
    Returns:
        SubscriptionService: Instance of subscription service
        
    This allows for easy mocking in tests and follows dependency injection principles.
    """
    return subscription_service


def get_weather_service() -> type(weather_service):
    """
    Dependency function for weather service.
    
    Returns:
        WeatherService: Instance of weather service
        
    This allows for easy mocking in tests and follows dependency injection principles.
    """
    return weather_service