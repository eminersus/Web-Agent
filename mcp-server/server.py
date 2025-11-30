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
from api.ebay import EbayBrowseAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure server host and port
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))

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
- eBay category suggestions
- eBay item aspects for categories

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


def get_mcp_app():
    """
    Get the FastAPI app from FastMCP and add REST endpoints.
    This allows the backend to call tools directly via HTTP.
    """
    from fastapi import HTTPException, Body, FastAPI
    from typing import Dict, Any
    import inspect
    
    # Get the FastAPI app that FastMCP will create
    app = FastAPI(title="Web-Agent-MCP", description="MCP Server with REST endpoints")
    
    # Store tool registry
    tool_registry = {}
    
    # Register tools from MCP instance
    for tool_name in dir(tools_api):
        attr = getattr(tools_api, tool_name)
        if callable(attr) and not tool_name.startswith('_'):
            tool_registry[tool_name] = attr

    for tool_name in dir(ebay_api):
        attr = getattr(ebay_api, tool_name)
        if callable(attr) and not tool_name.startswith('_'):
            tool_registry[tool_name] = attr
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "server": "Web-Agent-MCP",
            "transport": "SSE",
            "sse_endpoint": "/sse"
        }
    
    @app.get("/tools")
    async def list_tools():
        """List all available tools"""
        # Get tools directly from the MCP instance
        tools = []
        
        # Access FastMCP's internal tool registry
        if hasattr(mcp, '_tools') and mcp._tools:
            for tool_name, tool_info in mcp._tools.items():
                tool_def = {
                    "name": tool_name,
                    "description": tool_info.get("description", ""),
                    "inputSchema": tool_info.get("input_schema", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
                tools.append(tool_def)
        else:
            # Fallback: introspect from API classes
            for api_class in [tools_api, ebay_api]:
                for method_name in dir(api_class):
                    method = getattr(api_class, method_name)
                    if callable(method) and not method_name.startswith('_') and method_name != 'mcp':
                        try:
                            sig = inspect.signature(method)
                            doc = inspect.getdoc(method) or ""
                            
                            # Build input schema from signature with proper type introspection
                            properties = {}
                            required = []
                            for param_name, param in sig.parameters.items():
                                if param_name == 'self':
                                    continue
                                
                                # Get type annotation
                                param_type = "string"  # default
                                description = f"Parameter {param_name}"
                                
                                if param.annotation != inspect.Parameter.empty:
                                    # Check if it's Annotated
                                    if hasattr(param.annotation, '__origin__'):
                                        # It's likely Annotated[type, description]
                                        args = getattr(param.annotation, '__args__', ())
                                        if args:
                                            # Get the actual type
                                            actual_type = args[0]
                                            if actual_type == str:
                                                param_type = "string"
                                            elif actual_type == int:
                                                param_type = "integer"
                                            elif actual_type == float:
                                                param_type = "number"
                                            elif actual_type == bool:
                                                param_type = "boolean"
                                            
                                            # Get description if available
                                            if len(args) > 1 and isinstance(args[1], str):
                                                description = args[1]
                                
                                properties[param_name] = {
                                    "type": param_type,
                                    "description": description
                                }
                                
                                if param.default == inspect.Parameter.empty:
                                    required.append(param_name)
                            
                            tool_def = {
                                "name": method_name,
                                "description": doc.split('\n')[0] if doc else method_name,
                                "inputSchema": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required
                                }
                            }
                            tools.append(tool_def)
                        except Exception as e:
                            logger.warning(f"Could not introspect {method_name}: {e}")
                            continue
        
        return tools
    
    @app.post("/tools/{tool_name}")
    async def call_tool(tool_name: str, arguments: Dict[str, Any] = Body(...)):
        """Execute a tool with given arguments"""
        # Find the tool in our API classes
        tool_func = None
        for api_class in [tools_api, ebay_api]:
            if hasattr(api_class, tool_name):
                tool_func = getattr(api_class, tool_name)
                break
        
        if not tool_func:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        try:
            # Call the tool function
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)
            
            return {"result": result}
        except TypeError as e:
            logger.error(f"Invalid arguments for tool {tool_name}: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Invalid arguments: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


# Run the server
if __name__ == "__main__":
    logger.info(f"Starting Web Agent MCP Server on {HOST}:{PORT}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sse":
        # Run with REST endpoints for backend integration
        logger.info("Running with REST endpoints for backend integration")
        
        # Create FastAPI app with REST endpoints
        app = get_mcp_app()
        logger.info("Added REST endpoints: GET /health, GET /tools, POST /tools/{tool_name}")
        
        try:
            logger.info(f"REST endpoints available at http://{HOST}:{PORT}/")
            logger.info(f"Tools endpoint: http://{HOST}:{PORT}/tools")
            logger.info(f"Starting server (uvicorn will bind to {HOST}:{PORT})...")
            
            # Run uvicorn directly with our FastAPI app
            import uvicorn
            uvicorn.run(app, host=HOST, port=PORT, log_level="info")
        except Exception as e:
            logger.error(f"Failed to start server: {e}", exc_info=True)
            raise
    else:
        # Run as stdio server for local development/testing
        logger.info("Running in STDIO mode for local development")
        mcp.run(transport="stdio")
