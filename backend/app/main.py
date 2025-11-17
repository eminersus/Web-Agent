from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .openrouter_service import get_openrouter_service, cleanup_openrouter_service
from .mcp_client import get_mcp_client, cleanup_mcp_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Web Agent Backend Middleware",
    description="Backend middleware for flow control, monitoring, and future interruption capabilities",
    version="2.0.0"
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Web Agent Backend Middleware...")
    logger.info("Architecture: LibreChat -> MCP Server (SSE)")
    logger.info("Backend Role: Monitoring, Logging, Future Flow Control")
    
    # Check OpenRouter service
    openrouter = get_openrouter_service()
    is_healthy = await openrouter.health_check()
    if is_healthy:
        logger.info("✓ OpenRouter service is healthy")
        models = await openrouter.list_models()
        if models:
            logger.info(f"✓ Available models: {len(models)}")
    else:
        logger.warning("⚠ OpenRouter service is not responding")
    
    # Check MCP Server
    mcp = get_mcp_client()
    is_mcp_healthy = await mcp.health_check()
    if is_mcp_healthy:
        logger.info("✓ MCP Server is healthy and reachable")
    else:
        logger.warning("⚠ MCP Server is not responding")
    
    logger.info("✅ Backend Middleware ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Web Agent Backend...")
    await cleanup_openrouter_service()
    await cleanup_mcp_client()

# CORS Configuration
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

if allowed_origins and allowed_origins != ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # For development with wildcard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# =============================================================================
# Root Endpoints
# =============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return JSONResponse({
        "message": "Web Agent Backend Middleware API",
        "version": "2.0.0",
        "status": "running",
        "architecture": {
            "frontend": "LibreChat",
            "mcp_connection": "Direct SSE to MCP Server",
            "backend_role": "Monitoring, Logging, Future Flow Control"
        },
        "note": "LibreChat connects directly to MCP Server via SSE. This backend provides monitoring and optional flow control."
    })

@app.get("/api/health")
def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.get("/api/services/health")
async def services_health():
    """Check all services health"""
    openrouter = get_openrouter_service()
    mcp = get_mcp_client()
    
    openrouter_healthy = await openrouter.health_check()
    mcp_healthy = await mcp.health_check()
    
    return JSONResponse({
        "backend": {
            "status": "healthy",
            "role": "middleware"
        },
        "openrouter": {
            "status": "healthy" if openrouter_healthy else "unhealthy",
            "endpoint": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        },
        "mcp_server": {
            "status": "healthy" if mcp_healthy else "unhealthy",
            "endpoint": os.getenv("MCP_SERVER_URL", "http://mcp-server:8001"),
            "transport": "SSE"
        }
    })

# =============================================================================
# MCP Monitoring Endpoints
# =============================================================================

@app.get("/api/mcp/info")
async def mcp_info():
    """Get MCP server information and available tools"""
    mcp = get_mcp_client()
    
    try:
        # Get MCP server health
        is_healthy = await mcp.health_check()
        
        return JSONResponse({
            "mcp_server": {
                "url": os.getenv("MCP_SERVER_URL", "http://mcp-server:8001"),
                "transport": "SSE",
                "healthy": is_healthy,
                "connection": "Direct from LibreChat via SSE"
            },
            "note": "Tools are accessed directly by LibreChat through SSE connection"
        })
    except Exception as e:
        logger.error(f"Error getting MCP info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# OpenRouter Monitoring Endpoints
# =============================================================================

@app.get("/api/openrouter/models")
async def list_openrouter_models():
    """List available models from OpenRouter"""
    openrouter = get_openrouter_service()
    
    try:
        models = await openrouter.list_models()
        return JSONResponse({
            "models": models,
            "count": len(models) if models else 0
        })
    except Exception as e:
        logger.error(f"Error listing OpenRouter models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Future Flow Control Endpoints (Placeholders)
# =============================================================================

class InterruptionRequest(BaseModel):
    """Request to interrupt an ongoing conversation"""
    conversation_id: str
    reason: Optional[str] = None

@app.post("/api/flow/interrupt")
async def interrupt_conversation(request: InterruptionRequest):
    """
    Interrupt an ongoing conversation (Future feature).
    
    This is a placeholder for future functionality where the backend
    can interrupt and redirect LLM flows.
    """
    logger.info(f"Interruption requested for conversation: {request.conversation_id}")
    
    return JSONResponse({
        "success": True,
        "conversation_id": request.conversation_id,
        "message": "Interruption feature not yet implemented",
        "note": "This endpoint is a placeholder for future flow control capabilities"
    })

class FlowRedirectRequest(BaseModel):
    """Request to redirect conversation flow"""
    conversation_id: str
    new_instructions: str
    context: Optional[Dict[str, Any]] = None

@app.post("/api/flow/redirect")
async def redirect_flow(request: FlowRedirectRequest):
    """
    Redirect conversation flow (Future feature).
    
    This is a placeholder for future functionality where the backend
    can redirect conversations to different flows or instructions.
    """
    logger.info(f"Flow redirect requested for conversation: {request.conversation_id}")
    
    return JSONResponse({
        "success": True,
        "conversation_id": request.conversation_id,
        "new_instructions": request.new_instructions,
        "message": "Flow redirect feature not yet implemented",
        "note": "This endpoint is a placeholder for future flow control capabilities"
    })

# =============================================================================
# Logging and Monitoring Endpoints
# =============================================================================

@app.get("/api/logs/stats")
async def get_log_stats():
    """
    Get statistics about system usage (Future feature).
    
    This is a placeholder for monitoring conversation patterns,
    tool usage, and system performance.
    """
    return JSONResponse({
        "message": "Log statistics not yet implemented",
        "note": "This endpoint will provide insights into system usage, popular tools, and performance metrics"
    })

# =============================================================================
# Development/Debug Endpoints
# =============================================================================

@app.get("/api/debug/config")
async def debug_config():
    """Debug endpoint to view current configuration (development only)"""
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=403, detail="Debug endpoints only available in development")
    
    return JSONResponse({
        "environment": os.getenv("ENVIRONMENT"),
        "debug": os.getenv("DEBUG"),
        "mcp_server_url": os.getenv("MCP_SERVER_URL"),
        "openrouter_base_url": os.getenv("OPENROUTER_BASE_URL"),
        "cors_origins": os.getenv("CORS_ALLOW_ORIGINS"),
    })
