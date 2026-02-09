"""
Subscription router for PythonNotify application.

This module contains API endpoints for managing weather subscriptions.
It demonstrates FastAPI router patterns and dependency injection.
"""

from fastapi import APIRouter, Depends, status
from typing import List

from app.models import (
    SubscriptionRequest,
    SubscriptionResponse,
    UnsubscriptionRequest,
    UnsubscriptionResponse,
    SubscriptionsListResponse
)
from app.services.subscription import SubscriptionService
from app.core.dependencies import get_subscription_service

# Create router with prefix and tags
router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/",
    response_model=SubscriptionsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all active subscriptions",
    description="Retrieve a list of all cities with active weather subscriptions."
)
async def get_subscriptions(
    service: SubscriptionService = Depends(get_subscription_service)
) -> SubscriptionsListResponse:
    """
    Get all active weather subscriptions.
    
    Returns a list of all cities that are currently subscribed to weather notifications.
    
    Returns:
        SubscriptionsListResponse: List of subscribed cities and count
        
    Example:
        ```json
        {
            "subscriptions": ["Moscow", "London"],
            "count": 2,
            "timestamp": "2023-10-25T14:30:00Z"
        }
        ```
    """
    return service.get_all_subscriptions()


@router.post(
    "/",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to weather notifications",
    description="Subscribe to receive weather notifications for a specific city."
)
async def subscribe(
    request: SubscriptionRequest,
    service: SubscriptionService = Depends(get_subscription_service)
) -> SubscriptionResponse:
    """
    Subscribe to weather notifications for a city.
    
    This endpoint allows users to subscribe to weather updates for a specific city.
    The city name is validated and must not be empty or contain invalid characters.
    
    Args:
        request: Subscription request with city name
        
    Returns:
        SubscriptionResponse: Confirmation of subscription
        
    Raises:
        HTTPException 400: Invalid city name or maximum subscriptions reached
        HTTPException 409: Already subscribed to this city
        
    Example:
        Request:
        ```json
        {
            "city": "Moscow"
        }
        ```
        
        Response:
        ```json
        {
            "status": "subscribed",
            "city": "Moscow",
            "timestamp": "2023-10-25T14:30:00Z"
        }
        ```
    """
    return service.subscribe(request)


@router.delete(
    "/{city}",
    response_model=UnsubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Unsubscribe from weather notifications",
    description="Unsubscribe from weather notifications for a specific city."
)
async def unsubscribe(
    city: str,
    service: SubscriptionService = Depends(get_subscription_service)
) -> UnsubscriptionResponse:
    """
    Unsubscribe from weather notifications for a city.
    
    This endpoint allows users to unsubscribe from weather updates for a specific city.
    
    Args:
        city: City name to unsubscribe from (URL path parameter)
        
    Returns:
        UnsubscriptionResponse: Confirmation of unsubscription
        
    Raises:
        HTTPException 404: Not subscribed to this city
        
    Example:
        DELETE /subscriptions/Moscow
        
        Response:
        ```json
        {
            "status": "unsubscribed",
            "city": "Moscow",
            "timestamp": "2023-10-25T14:30:00Z"
        }
        ```
    """
    request = UnsubscriptionRequest(city=city)
    return service.unsubscribe(request)


@router.delete(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Clear all subscriptions (admin)",
    description="Clear all subscriptions (for testing and admin purposes).",
    include_in_schema=False  # Hide from public API docs
)
async def clear_subscriptions(
    service: SubscriptionService = Depends(get_subscription_service)
) -> dict:
    """
    Clear all subscriptions (admin endpoint).
    
    This endpoint is for testing and administrative purposes only.
    It clears all active subscriptions from the system.
    
    Returns:
        dict: Confirmation message
        
    Example:
        Response:
        ```json
        {
            "status": "cleared",
            "message": "All subscriptions cleared"
        }
        ```
    """
    service.clear_subscriptions()
    return {
        "status": "cleared",
        "message": "All subscriptions cleared"
    }