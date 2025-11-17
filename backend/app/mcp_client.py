"""
MCP Client for monitoring and communicating with the MCP Server

Note: In the FastMCP/SSE architecture, LibreChat connects directly to the MCP server.
This client is used by the backend middleware for monitoring and health checks.
"""

import os
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")
MCP_TIMEOUT = float(os.getenv("MCP_TIMEOUT", "60.0"))


class MCPClient:
    """Client for monitoring MCP Server health and status"""
    
    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=MCP_TIMEOUT)
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is available and healthy.
        
        Note: This checks the /health endpoint. The actual MCP protocol
        communication happens via SSE at /sse endpoint.
        """
        try:
            # Try to access the SSE endpoint (FastMCP health check)
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except httpx.ConnectError:
            logger.error(f"MCP health check failed: Cannot connect to {self.base_url}")
            return False
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return False
    
    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the MCP server.
        
        Returns basic server info for monitoring purposes.
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return {
                    "healthy": True,
                    "url": self.base_url,
                    "transport": "SSE",
                    "sse_endpoint": f"{self.base_url}/sse"
                }
            return {
                "healthy": False,
                "error": f"Unexpected status code: {response.status_code}"
            }
        except Exception as e:
            logger.error(f"Failed to get MCP server info: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


async def cleanup_mcp_client():
    """Cleanup the global MCP client instance"""
    global _mcp_client
    if _mcp_client is not None:
        await _mcp_client.close()
        _mcp_client = None
