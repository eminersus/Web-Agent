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

app = FastAPI(
    title="Web Agent Backend API",
    description="FastAPI backend for chat-based web agent",
    version="1.0.0"
)

# CORS: read allowed origins from env (comma-separated)
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],   # loosen during early dev
    allow_credentials=True,
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
    
    print(f"[{message_id}] Created message: {request.text}")
    
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
        print(f"[{message_id}] SSE client connected")
        
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
                
                print(f"[{message_id}] SSE sent: {event_type} -> {event_data}")
                sent_count += 1
            
            # If done, send the done event and close
            if message_data["done"]:
                yield {
                    "event": "done",
                    "data": json.dumps({})
                }
                print(f"[{message_id}] SSE stream complete")
                break
            
            # Wait a bit before checking for new events
            await asyncio.sleep(0.1)
    
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
    Simulate background processing of a message.
    Sends status updates and mock results.
    """
    message_data = messages_store[message_id]
    
    # Stage 1: Parsing
    await asyncio.sleep(0.5)
    message_data["status"] = "parsing"
    message_data["events"].append({
        "type": "status",
        "data": {"stage": "parsing"}
    })
    print(f"[{message_id}] Stage: parsing")
    
    # Stage 2: Searching eBay
    await asyncio.sleep(1)
    message_data["status"] = "searching_ebay"
    message_data["events"].append({
        "type": "status",
        "data": {"stage": "searching_ebay"}
    })
    print(f"[{message_id}] Stage: searching_ebay")
    
    # Stage 3: Return mock result
    await asyncio.sleep(1)
    result = {
        "title": "Purple Umbrella",
        "price": 17.99,
        "url": "https://ebay.com/item/example",
        "condition": "New"
    }
    message_data["status"] = "completed"
    message_data["result"] = result
    message_data["events"].append({
        "type": "result",
        "data": result
    })
    print(f"[{message_id}] Result: {result}")
    
    # Mark as done
    await asyncio.sleep(0.2)
    message_data["done"] = True
    print(f"[{message_id}] Processing complete")
