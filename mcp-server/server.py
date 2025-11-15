"""
MCP Server implementing Model Context Protocol for LibreChat
Uses HTTP POST transport as required by streamable-http type
"""

import os
import logging
import json
from datetime import datetime
from typing import Any, Dict, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server")

# =============================================================================
# Tool Implementations
# =============================================================================

def get_current_time() -> str:
    """Get the current date and time"""
    now = datetime.now()
    return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"


def calculate(expression: str) -> str:
    """Calculate a mathematical expression safely"""
    try:
        allowed_chars = set('0123456789+-*/()%. ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Expression contains invalid characters"
        
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating expression: {str(e)}"


def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Search the web for information (placeholder)"""
    logger.info(f"Web search requested: {query}")
    return {
        "query": query,
        "num_results": num_results,
        "results": [{
            "title": f"Sample result for: {query}",
            "url": "https://example.com",
            "snippet": "Placeholder search result"
        }],
        "message": "Note: This is a placeholder. Connect to a real search API."
    }


def get_weather(location: str) -> Dict[str, Any]:
    """Get weather information (placeholder)"""
    logger.info(f"Weather request for: {location}")
    return {
        "location": location,
        "temperature": "72°F",
        "condition": "Partly Cloudy",
        "humidity": "45%",
        "message": "Note: This is a placeholder. Connect to a real weather API."
    }


def create_task(title: str, description: str = "", priority: str = "medium") -> Dict[str, Any]:
    """Create a new task or reminder"""
    task_id = f"task_{datetime.now().timestamp()}"
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    logger.info(f"Task created: {task_id}")
    return task


def analyze_text(text: str, analysis_type: str = "sentiment") -> Dict[str, Any]:
    """Analyze text for sentiment, keywords, or summary"""
    logger.info(f"Text analysis requested: {analysis_type}")
    result = {
        "text_length": len(text),
        "word_count": len(text.split()),
        "analysis_type": analysis_type,
    }
    
    if analysis_type == "sentiment":
        result["sentiment"] = "neutral"
        result["confidence"] = 0.75
    elif analysis_type == "keywords":
        result["keywords"] = text.split()[:5]
    elif analysis_type == "summary":
        result["summary"] = text[:100] + "..." if len(text) > 100 else text
    
    return result


# =============================================================================
# MCP Protocol Implementation
# =============================================================================

# Tool definitions following MCP protocol schema
TOOLS = [
    {
        "name": "get_current_time",
        "description": "Get the current date and time",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "calculate",
        "description": "Calculate a mathematical expression safely",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "create_task",
        "description": "Create a new task or reminder",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Task description",
                    "default": ""
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority",
                    "default": "medium"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "analyze_text",
        "description": "Analyze text for sentiment, keywords, or summary",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["sentiment", "keywords", "summary"],
                    "description": "Type of analysis",
                    "default": "sentiment"
                }
            },
            "required": ["text"]
        }
    }
]


@app.get("/health")
def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "server": "Web-Agent-MCP-Server"})


@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """
    Handle MCP protocol messages
    Implements the Model Context Protocol over HTTP POST
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        logger.info(f"MCP Request: {method}")
        
        # Handle notifications (no response needed, no id field)
        if request_id is None and method and method.startswith("notifications/"):
            logger.info(f"Received notification: {method}")
            return JSONResponse({"ok": True})
        
        # Handle initialize
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "Web-Agent-MCP-Server",
                        "version": "1.0.0"
                    }
                }
            }
            return JSONResponse(response)
        
        # Handle tools/list
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": TOOLS
                }
            }
            return JSONResponse(response)
        
        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Execute the tool
            try:
                if tool_name == "get_current_time":
                    result = get_current_time()
                elif tool_name == "calculate":
                    result = calculate(arguments.get("expression", ""))
                elif tool_name == "search_web":
                    result = search_web(
                        arguments.get("query", ""),
                        arguments.get("num_results", 5)
                    )
                elif tool_name == "get_weather":
                    result = get_weather(arguments.get("location", ""))
                elif tool_name == "create_task":
                    result = create_task(
                        arguments.get("title", ""),
                        arguments.get("description", ""),
                        arguments.get("priority", "medium")
                    )
                elif tool_name == "analyze_text":
                    result = analyze_text(
                        arguments.get("text", ""),
                        arguments.get("analysis_type", "sentiment")
                    )
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result) if isinstance(result, dict) else str(result)
                            }
                        ]
                    }
                }
                return JSONResponse(response)
            
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                return JSONResponse(response, status_code=500)
        
        # Handle resources/list
        elif method == "resources/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []
                }
            }
            return JSONResponse(response)
        
        # Unknown method
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            return JSONResponse(response, status_code=404)
    
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }, status_code=400)


if __name__ == "__main__":
    logger.info("Starting MCP Server with HTTP POST transport...")
    logger.info("Listening on port 8001 at /mcp endpoint")
    logger.info("LibreChat will connect to: http://mcp-server:8001/mcp")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
