"""
Web Agent MCP Server using FastMCP
Architecture similar to sagemind's sagebot-mcp
"""

from fastmcp import FastMCP
import os
import sys
import asyncio
import logging
from threading import Thread
from fastapi import FastAPI
import uvicorn
from api.tools import ToolsAPI
from api.web import WebAPI
from api.tasks import TasksAPI
from api.ebay import EbayBrowseAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure server host and port
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8001"))

INSTRUCTIONS = """
MCP Server for Web Agent providing various tools and capabilities.
This server provides tools for:
- Time and date information
- Mathematical calculations
- Web search capabilities
- Weather information
- Task management
- Text analysis
- eBay item search and discovery

Use these tools to help users accomplish their goals.
"""

# Instantiate MCP server
# FastMCP takes only the name parameter; instructions are set via dependencies or prompts
mcp = FastMCP("Web-Agent-MCP")

# Add a greeting resource (example)
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}! Welcome to Web Agent."

# Initialize API modules - they will register their tools with mcp
logger.info("Initializing API modules...")
tools_api = ToolsAPI(mcp)
logger.info("Tools API initialized")
web_api = WebAPI(mcp)
logger.info("Web API initialized")
tasks_api = TasksAPI(mcp)
logger.info("Tasks API initialized")
ebay_api = EbayBrowseAPI(mcp)
logger.info("eBay Browse API initialized")


def create_health_server():
    """Create a simple health check server on a different port"""
    health_app = FastAPI()
    
    @health_app.get("/health")
    async def health_check():
        """Health check endpoint for Docker and monitoring"""
        return {
            "status": "healthy",
            "server": "Web-Agent-MCP",
            "transport": "SSE",
            "sse_endpoint": "/sse"
        }
    
    return health_app


# Run the server
if __name__ == "__main__":
    logger.info(f"Starting Web Agent MCP Server on {HOST}:{PORT}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sse":
        # Run as SSE server for LibreChat integration
        logger.info("Running in SSE mode for LibreChat integration")
        
        # FastMCP uses environment variables for uvicorn configuration
        # Set them before running
        os.environ["UVICORN_HOST"] = HOST
        os.environ["UVICORN_PORT"] = str(PORT)
        
        try:
            logger.info(f"MCP SSE endpoint will be available at http://{HOST}:{PORT}/sse")
            logger.info(f"Starting FastMCP server (uvicorn will bind to {HOST}:{PORT})...")
            
            # FastMCP.run() in SSE mode will read UVICORN_HOST and UVICORN_PORT from environment
            mcp.run(transport="sse")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}", exc_info=True)
            raise
    else:
        # Run as stdio server for local development/testing
        logger.info("Running in STDIO mode for local development")
        mcp.run(transport="stdio")
