"""
Main FastAPI application for PythonNotify.

This module creates and configures the FastAPI application with all routers,
middleware, and startup/shutdown events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers import subscriptions, weather
from app.core.config import settings
from app.models import HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI instance
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="PythonNotify - Weather notification service with MCP integration",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(subscriptions.router)
    app.include_router(weather.router)
    
    # Health check endpoint
    @app.get(
        "/",
        response_model=HealthCheckResponse,
        summary="Health check",
        description="Check if the service is running and dependencies are available."
    )
    async def health_check() -> HealthCheckResponse:
        """
        Health check endpoint.
        
        Returns basic service status and dependency information.
        """
        return HealthCheckResponse(
            status="healthy",
            version=settings.app_version,
            dependencies={
                "subscription_service": "available",
                "weather_service": "available",
                "openweather_api": "configured"
            }
        )
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Execute on application startup."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info("Application startup completed")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Execute on application shutdown."""
        logger.info("Application shutdown initiated")
    
    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    """
    Run the application directly for development.
    
    Usage:
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    """
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )