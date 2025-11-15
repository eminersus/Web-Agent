"""
MCP Client for communicating with the MCP Server
"""

import os
import httpx
import json
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")
MCP_TIMEOUT = float(os.getenv("MCP_TIMEOUT", "60.0"))


class MCPClient:
    """Client for interacting with MCP Server"""
    
    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=MCP_TIMEOUT)
    
    async def health_check(self) -> bool:
        """Check if MCP server is available"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server"""
        try:
            response = await self.client.get(f"{self.base_url}/tools")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
        
        Returns:
            Dictionary containing the tool's response
        """
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            
            response = await self.client.post(
                f"{self.base_url}/tools/{tool_name}",
                json={"arguments": arguments}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"MCP tool {tool_name} succeeded")
                return {"success": True, "result": result}
            else:
                error_msg = f"MCP tool call failed with status {response.status_code}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        
        except httpx.TimeoutException:
            error_msg = f"MCP tool call timed out after {MCP_TIMEOUT}s"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error calling MCP tool: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Get a resource from the MCP server
        
        Args:
            resource_uri: URI of the resource (e.g., "config://server")
        
        Returns:
            Dictionary containing the resource data
        """
        try:
            logger.info(f"Getting MCP resource: {resource_uri}")
            
            response = await self.client.get(
                f"{self.base_url}/resources",
                params={"uri": resource_uri}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"MCP resource {resource_uri} retrieved")
                return {"success": True, "data": result}
            else:
                error_msg = f"MCP resource retrieval failed with status {response.status_code}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        
        except Exception as e:
            error_msg = f"Error getting MCP resource: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
    
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

