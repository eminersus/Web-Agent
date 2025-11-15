from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import os
import uuid
import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime
import logging

from .llm_service import get_ollama_service, cleanup_ollama_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Web Agent Backend API",
    description="FastAPI backend for chat-based web agent",
    version="1.0.0"
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Web Agent Backend...")
    ollama = get_ollama_service()
    is_healthy = await ollama.health_check()
    if is_healthy:
        logger.info("✓ Ollama service is healthy")
        models = await ollama.list_models()
        if models:
            logger.info(f"✓ Available models: {[m.get('name') for m in models]}")
        else:
            logger.warning("⚠ No models found. Please pull a model.")
    else:
        logger.warning("⚠ Ollama service is not responding")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Web Agent Backend...")
    await cleanup_ollama_service()

# CORS: read allowed origins from env (comma-separated)
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

# When using wildcard "*", we cannot use credentials
# This is a CORS security requirement
if allowed_origins and allowed_origins != ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # For development/local network access with wildcard
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
        "message": "Web Agent Backend API",
        "version": "1.0.0",
        "status": "running"
    })

@app.get("/api/health")
def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    })

@app.get("/api/llm/health")
async def llm_health():
    """Check LLM service health"""
    ollama = get_ollama_service()
    is_healthy = await ollama.health_check()
    
    if is_healthy:
        models = await ollama.list_models()
        return JSONResponse({
            "status": "healthy",
            "service": "ollama",
            "base_url": ollama.base_url,
            "model": ollama.model,
            "available_models": [m.get("name") for m in models]
        })
    else:
        return JSONResponse({
            "status": "unhealthy",
            "service": "ollama",
            "base_url": ollama.base_url
        }, status_code=503)

# =============================================================================
# In-Memory Storage
# =============================================================================

# Store message data: { message_id: { "text": str, "status": str, "events": list, "done": bool } }
messages_store: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# Pydantic Models
# =============================================================================

class ChatMessageRequest(BaseModel):
    text: str

# =============================================================================
# Chat Endpoints
# =============================================================================

@app.post("/api/chat/messages")
async def create_message(request: ChatMessageRequest):
    """
    Accept a user message, generate a message_id, and return it.
    This starts the backend processing in the background.
    """
    message_id = str(uuid.uuid4())
    
    # Initialize message in store
    messages_store[message_id] = {
        "text": request.text,
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
    Sends status updates, results, and a done event.
    """
    if message_id not in messages_store:
        raise HTTPException(status_code=404, detail="Message not found")
    
    async def event_generator():
        """Generate SSE events for this message"""
        logger.info(f"[{message_id}] SSE client connected")
        
        # Track which events we've already sent
        sent_count = 0
        
        while True:
            message_data = messages_store.get(message_id)
            if not message_data:
                break
            
            # Send any new events that haven't been sent yet
            events = message_data["events"]
            while sent_count < len(events):
                event = events[sent_count]
                event_type = event["type"]
                event_data = event["data"]
                
                yield {
                    "event": event_type,
                    "data": json.dumps(event_data)
                }
                
                # Only log non-token events to avoid spam
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
            
            # Wait a bit before checking for new events
            await asyncio.sleep(0.05)  # Check more frequently for smoother streaming
    
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
# Background Processing
# =============================================================================

async def process_message(message_id: str):
    """
    Process a user message by querying the LLM and streaming the response.
    """
    message_data = messages_store[message_id]
    user_message = message_data["text"]
    
    try:
        # Stage 1: Preparing to query LLM
        message_data["status"] = "preparing"
        message_data["events"].append({
            "type": "status",
            "data": {"stage": "preparing", "message": "Preparing your request..."}
        })
        logger.info(f"[{message_id}] Stage: preparing")
        
        # Stage 2: Querying LLM
        message_data["status"] = "querying_llm"
        message_data["events"].append({
            "type": "status",
            "data": {"stage": "querying_llm", "message": "Thinking..."}
        })
        logger.info(f"[{message_id}] Stage: querying LLM")
        
        # Get LLM service
        ollama = get_ollama_service()
        
        # Build system prompt for eBay search agent
        system_prompt = """You are a helpful assistant for daily chatting."""
        
        # Build messages for chat
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Stream the response
        full_response = ""
        token_count = 0
        
        async for chunk in ollama.generate_chat_stream(messages, temperature=0.7):
            if chunk.get("error"):
                # Handle error
                logger.error(f"[{message_id}] LLM error: {chunk['error']}")
                message_data["events"].append({
                    "type": "error",
                    "data": {"message": f"Error: {chunk['error']}"}
                })
                message_data["status"] = "error"
                break
            
            if chunk.get("done"):
                # Streaming complete
                logger.info(f"[{message_id}] LLM response complete. Tokens: {token_count}")
                
                # Add final response event
                message_data["events"].append({
                    "type": "response_complete",
                    "data": {
                        "full_text": full_response,
                        "token_count": chunk.get("eval_count", token_count)
                    }
                })
                message_data["status"] = "completed"
                message_data["result"] = {
                    "response": full_response,
                    "token_count": token_count
                }
                break
            
            # Handle token
            token = chunk.get("token", "")
            if token:
                full_response += token
                token_count += 1
                
                # Send token to frontend
                message_data["events"].append({
                    "type": "token",
                    "data": {"token": token}
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
