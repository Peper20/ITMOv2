"""
Subscription service for PythonNotify application.

This module handles the business logic for managing weather subscriptions.
It uses in-memory storage for simplicity in this educational project.
"""

from typing import Set, List
from datetime import datetime
import logging
from fastapi import HTTPException, status

from app.models import (
    SubscriptionRequest,
    SubscriptionResponse,
    UnsubscriptionRequest,
    UnsubscriptionResponse,
    SubscriptionsListResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service class for managing weather subscriptions.
    
    This service demonstrates:
    - Business logic encapsulation
    - In-memory data storage
    - Error handling patterns
    - Integration with other services
    """
    
    def __init__(self):
        """Initialize subscription service with empty storage."""
        self.subscriptions: Set[str] = set()
        logger.info("Subscription service initialized")
    
    def subscribe(self, request: SubscriptionRequest) -> SubscriptionResponse:
        """
        Subscribe to weather notifications for a city.
        
        Args:
            request: Subscription request with validated city name
            
        Returns:
            SubscriptionResponse: Confirmation of subscription
            
        Raises:
            HTTPException: If already subscribed or maximum subscriptions reached
        """
        city = request.city
        
        # Check if already subscribed
        if city in self.subscriptions:
            logger.warning(f"Attempt to subscribe to already subscribed city: {city}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Already subscribed to {city}"
            )
        
        # Check subscription limit
        if len(self.subscriptions) >= settings.max_subscriptions:
            logger.warning(f"Subscription limit reached: {settings.max_subscriptions}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum subscription limit ({settings.max_subscriptions}) reached"
            )
        
        # Add subscription
        self.subscriptions.add(city)
        logger.info(f"Subscribed to city: {city}")
        
        return SubscriptionResponse(
            status="subscribed",
            city=city
        )
    
    def unsubscribe(self, request: UnsubscriptionRequest) -> UnsubscriptionResponse:
        """
        Unsubscribe from weather notifications for a city.
        
        Args:
            request: Unsubscription request with city name
            
        Returns:
            UnsubscriptionResponse: Confirmation of unsubscription
            
        Raises:
            HTTPException: If not subscribed to the city
        """
        city = request.city
        
        # Check if subscribed
        if city not in self.subscriptions:
            logger.warning(f"Attempt to unsubscribe from non-subscribed city: {city}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Not subscribed to {city}"
            )
        
        # Remove subscription
        self.subscriptions.remove(city)
        logger.info(f"Unsubscribed from city: {city}")
        
        return UnsubscriptionResponse(
            status="unsubscribed",
            city=city
        )
    
    def get_all_subscriptions(self) -> SubscriptionsListResponse:
        """
        Get all active subscriptions.
        
        Returns:
            SubscriptionsListResponse: List of subscribed cities and count
        """
        subscriptions_list = sorted(list(self.subscriptions))
        logger.debug(f"Retrieved {len(subscriptions_list)} subscriptions")
        
        return SubscriptionsListResponse(
            subscriptions=subscriptions_list,
            count=len(subscriptions_list)
        )
    
    def is_subscribed(self, city: str) -> bool:
        """
        Check if a city is currently subscribed.
        
        Args:
            city: City name to check
            
        Returns:
            bool: True if subscribed, False otherwise
        """
        return city in self.subscriptions
    
    def clear_subscriptions(self) -> None:
        """
        Clear all subscriptions (for testing purposes).
        """
        self.subscriptions.clear()
        logger.info("All subscriptions cleared")


# Global service instance for dependency injection
subscription_service = SubscriptionService()