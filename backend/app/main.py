from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import os
import uuid
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .openrouter_service import get_openrouter_service, cleanup_openrouter_service
from .mcp_client import get_mcp_client, cleanup_mcp_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Web Agent Backend API",
    description="FastAPI backend middleware for LibreChat -> Backend -> MCP Server",
    version="2.0.0"
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Web Agent Backend (Middleware)...")
    
    # Check OpenRouter
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
        logger.info("✓ MCP Server is healthy")
        tools = await mcp.list_tools()
        if tools:
            logger.info(f"✓ Available MCP tools: {[t.get('name') for t in tools]}")
    else:
        logger.warning("⚠ MCP Server is not responding")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Web Agent Backend...")
    await cleanup_openrouter_service()
    await cleanup_mcp_client()

# CORS: read allowed origins from env (comma-separated)
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

# When using wildcard "*", we cannot use credentials
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

@app.get("/")
def root():
    """Root endpoint"""
    return JSONResponse({
        "message": "Web Agent Backend API (Middleware)",
        "version": "2.0.0",
        "status": "running",
        "architecture": "LibreChat -> Backend -> MCP Server"
    })

@app.get("/api/health")
def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    })

@app.get("/api/services/health")
async def services_health():
    """Check all services health"""
    openrouter = get_openrouter_service()
    mcp = get_mcp_client()
    
    openrouter_healthy = await openrouter.health_check()
    mcp_healthy = await mcp.health_check()
    
    return JSONResponse({
        "backend": {"status": "healthy"},
        "openrouter": {"status": "healthy" if openrouter_healthy else "unhealthy"},
        "mcp_server": {"status": "healthy" if mcp_healthy else "unhealthy"}
    })

@app.get("/api/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    mcp = get_mcp_client()
    tools = await mcp.list_tools()
    return JSONResponse({"tools": tools})

# =============================================================================
# In-Memory Storage
# =============================================================================

messages_store: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# Pydantic Models
# =============================================================================

class ChatMessageRequest(BaseModel):
    text: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    use_mcp_tools: Optional[bool] = True

class MCPToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

# =============================================================================
# Chat Endpoints
# =============================================================================

@app.post("/api/chat/messages")
async def create_message(request: ChatMessageRequest):
    """
    Accept a user message from LibreChat, generate a message_id, and return it.
    This starts the backend processing in the background.
    """
    message_id = str(uuid.uuid4())
    
    # Initialize message in store
    messages_store[message_id] = {
        "text": request.text,
        "model": request.model,
        "temperature": request.temperature,
        "use_mcp_tools": request.use_mcp_tools,
        "status": "initialized",
        "events": [],
        "done": False,
        "result": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Start background processing
    asyncio.create_task(process_message(message_id))
    
    logger.info(f"[{message_id}] Created message: {request.text}")
    
    return JSONResponse({
        "message_id": message_id
    })

@app.get("/api/chat/messages/{message_id}/events")
async def stream_message_events(message_id: str):
    """
    Stream SSE events for a given message_id.
    Sends status updates, tokens, tool calls, and completion events.
    """
    if message_id not in messages_store:
        raise HTTPException(status_code=404, detail="Message not found")
    
    async def event_generator():
        """Generate SSE events for this message"""
        logger.info(f"[{message_id}] SSE client connected")
        
        sent_count = 0
        
        while True:
            message_data = messages_store.get(message_id)
            if not message_data:
                break
            
            # Send any new events
            events = message_data["events"]
            while sent_count < len(events):
                event = events[sent_count]
                event_type = event["type"]
                event_data = event["data"]
                
                yield {
                    "event": event_type,
                    "data": json.dumps(event_data)
                }
                
                if event_type != "token":
                    logger.info(f"[{message_id}] SSE sent: {event_type}")
                sent_count += 1
            
            # If done, send the done event and close
            if message_data["done"]:
                yield {
                    "event": "done",
                    "data": json.dumps({})
                }
                logger.info(f"[{message_id}] SSE stream complete")
                break
            
            await asyncio.sleep(0.05)
    
    return EventSourceResponse(event_generator())

@app.get("/api/chat/messages/{message_id}/status")
async def get_message_status(message_id: str):
    """
    Polling fallback endpoint. Returns current status and all events.
    """
    if message_id not in messages_store:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message_data = messages_store[message_id]
    
    return JSONResponse({
        "message_id": message_id,
        "status": message_data["status"],
        "events": message_data["events"],
        "done": message_data["done"],
        "result": message_data["result"]
    })

# =============================================================================
# MCP Tool Call Endpoint
# =============================================================================

@app.post("/api/mcp/tools/call")
async def call_mcp_tool(request: MCPToolCallRequest):
    """
    Call an MCP tool directly
    """
    mcp = get_mcp_client()
    result = await mcp.call_tool(request.tool_name, request.arguments)
    
    if result.get("success"):
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Tool call failed"))

# =============================================================================
# Background Processing
# =============================================================================

async def process_message(message_id: str):
    """
    Process a user message by:
    1. Querying OpenRouter LLM
    2. Handling any tool calls via MCP
    3. Streaming the response back
    """
    message_data = messages_store[message_id]
    user_message = message_data["text"]
    model = message_data.get("model")
    temperature = message_data.get("temperature", 0.7)
    use_mcp_tools = message_data.get("use_mcp_tools", True)
    
    try:
        # Stage 1: Preparing
        message_data["status"] = "preparing"
        message_data["events"].append({
            "type": "status",
            "data": {"stage": "preparing", "message": "Preparing your request..."}
        })
        logger.info(f"[{message_id}] Stage: preparing")
        
        # Stage 2: Get MCP tools if enabled
        tools_schema = None
        if use_mcp_tools:
            mcp = get_mcp_client()
            tools_list = await mcp.list_tools()
            if tools_list:
                # Convert MCP tools to OpenAI function calling format
                tools_schema = []
                for tool in tools_list:
                    tools_schema.append({
                        "type": "function",
                        "function": {
                            "name": tool.get("name"),
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {})
                        }
                    })
                logger.info(f"[{message_id}] Loaded {len(tools_schema)} MCP tools")
        
        # Stage 3: Querying LLM
        message_data["status"] = "querying_llm"
        message_data["events"].append({
            "type": "status",
            "data": {"stage": "querying_llm", "message": "Thinking..."}
        })
        logger.info(f"[{message_id}] Stage: querying LLM")
        
        # Get OpenRouter service
        openrouter = get_openrouter_service()
        
        # Build system prompt
        system_prompt = """You are a helpful AI assistant. You have access to various tools that can help you answer questions and perform tasks.
When you need to use a tool, make a function call and wait for the result."""
        
        # Build messages for chat
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Stream the response
        full_response = ""
        token_count = 0
        tool_calls_made = []
        
        async for chunk in openrouter.generate_chat_stream(
            messages,
            model=model,
            temperature=temperature,
            tools=tools_schema
        ):
            if chunk.get("error"):
                logger.error(f"[{message_id}] LLM error: {chunk['error']}")
                message_data["events"].append({
                    "type": "error",
                    "data": {"message": f"Error: {chunk['error']}"}
                })
                message_data["status"] = "error"
                break
            
            if chunk.get("done"):
                logger.info(f"[{message_id}] LLM response complete. Tokens: {token_count}")
                
                # Add final response event
                message_data["events"].append({
                    "type": "response_complete",
                    "data": {
                        "full_text": full_response,
                        "token_count": token_count,
                        "tool_calls": tool_calls_made
                    }
                })
                message_data["status"] = "completed"
                message_data["result"] = {
                    "response": full_response,
                    "token_count": token_count,
                    "tool_calls": tool_calls_made
                }
                break
            
            # Handle token
            token = chunk.get("token")
            if token:
                full_response += token
                token_count += 1
                
                message_data["events"].append({
                    "type": "token",
                    "data": {"token": token}
                })
            
            # Handle tool calls
            tool_calls = chunk.get("tool_calls")
            if tool_calls:
                logger.info(f"[{message_id}] Tool calls requested: {tool_calls}")
                
                # Execute tool calls via MCP
                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    tool_args = tool_call.get("function", {}).get("arguments", {})
                    
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)
                    
                    # Call MCP tool
                    mcp = get_mcp_client()
                    tool_result = await mcp.call_tool(tool_name, tool_args)
                    
                    tool_calls_made.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })
                    
                    # Send tool call event
                    message_data["events"].append({
                        "type": "tool_call",
                        "data": {
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        }
                    })
        
        # Mark as done
        message_data["done"] = True
        logger.info(f"[{message_id}] Processing complete")
    
    except Exception as e:
        logger.error(f"[{message_id}] Error processing message: {e}", exc_info=True)
        message_data["status"] = "error"
        message_data["events"].append({
            "type": "error",
            "data": {"message": f"An error occurred: {str(e)}"}
        })
        message_data["done"] = True
