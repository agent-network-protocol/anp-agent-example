"""
Main application entry point for ANP Agent Example.

This module creates and configures the FastAPI application with all routers,
middleware, and dependencies required for the ANP-compliant agent service.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from ad_router import router as agent_description_router
from api_router import router as api_router

# Import authentication middleware
from auth_middleware import auth_middleware
from yaml_router import router as yaml_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="ANP智能体示例服务",
    description="基于FastAPI实现的ANP协议智能体示例，提供符合ANP规范的智能体描述和API接口服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.middleware("http")(auth_middleware)

# Include routers
app.include_router(agent_description_router, tags=["Agent Description"])
app.include_router(api_router, tags=["API Resources"])
app.include_router(yaml_router, tags=["YAML Resources"])


@app.get("/", response_class=JSONResponse)
async def root():
    """
    Root endpoint providing basic service information.
    
    Returns:
        Service information and available endpoints
    """
    return {
        "service": "ANP智能体示例服务",
        "version": "1.0.0",
        "protocol": "ANP",
        "protocol_version": "1.0.0",
        "description": "基于FastAPI实现的ANP协议智能体示例服务",
        "endpoints": {
            "agent_description": "/agents/travel/test/ad.json",
            "api_resources": "/agents/travel/test/api/{json_file}",
            "yaml_resources": "/agents/travel/test/api_files/{yaml_file}",
            "documentation": "/docs",
            "openapi_spec": "/openapi.json"
        },
        "authentication": "DID-WBA",
        "status": "online"
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint for service monitoring.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "anp-agent-example",
        "version": "1.0.0"
    }


@app.get("/v1/status", response_class=JSONResponse)
async def status_check():
    """
    Status endpoint for compatibility.
    
    Returns:
        Service status information
    """
    return {
        "status": "ok",
        "message": "ANP Agent Example Service is running"
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Custom 404 handler.
    
    Args:
        request: The FastAPI request object
        exc: The exception that was raised
        
    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource '{request.url.path}' was not found",
            "status_code": 404
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """
    Custom 500 handler.
    
    Args:
        request: The FastAPI request object
        exc: The exception that was raised
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
