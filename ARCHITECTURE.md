# Web Agent Architecture

This document describes the architecture and design of the Web Agent application.

## 🏗️ System Overview

The Web Agent is a three-tier architecture combining a modern chat interface (LibreChat), a middleware backend, and a tool server using the Model Context Protocol (MCP).

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ HTTP/WebSocket
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                     LibreChat Frontend                           │
│  - React-based UI                                               │
│  - Chat interface                                               │
│  - File uploads                                                 │
│  - Conversation management                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ REST API
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│  - Message coordination                                         │
│  - Stream management                                            │
│  - LLM request routing                                          │
│  - MCP tool orchestration                                       │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               │ HTTPS                       │ HTTP
               ↓                             ↓
┌────────────────────────┐     ┌──────────────────────────────────┐
│   OpenRouter API       │     │       MCP Server                 │
│                        │     │  (FastMCP - Python)              │
│  - Claude 3.5 Sonnet   │     │                                  │
│  - GPT-4 Turbo         │     │  Tools:                          │
│  - Llama 3.1           │     │  - get_current_time              │
│  - Gemini Pro          │     │  - calculate                     │
│  - And more...         │     │  - search_web                    │
└────────────────────────┘     │  - get_weather                   │
                               │  - create_task                   │
                               │  - analyze_text                  │
                               │                                  │
                               │  Resources:                      │
                               │  - config://server               │
                               │  - info://capabilities           │
                               └──────────────────────────────────┘

Supporting Services:
┌──────────────────┐
│    MongoDB       │
│  - User data     │
│  - Conversations │
└──────────────────┘
```

## 🔄 Data Flow

### 1. User Message Processing

```
User types message
    ↓
LibreChat sends to Backend
    ↓
Backend creates message_id and returns it
    ↓
User connects to SSE stream (/api/chat/messages/{id}/events)
    ↓
Backend processes in background:
    1. Checks if MCP tools should be available
    2. Lists available MCP tools
    3. Formats tools for LLM (OpenAI function calling format)
    4. Sends request to OpenRouter with tools
    ↓
OpenRouter streams response
    ↓
Backend forwards tokens to SSE stream
    ↓
If LLM requests tool call:
    Backend → MCP Server (HTTP POST)
    ↓
    MCP Server executes tool
    ↓
    Returns result to Backend
    ↓
    Backend includes result in conversation
    ↓
    Continues streaming to user
    ↓
Stream completes
```

### 2. Tool Call Flow

```
LLM decides to use a tool
    ↓
Sends tool_call in response stream
    ↓
Backend receives tool_call
    {
      "function": {
        "name": "calculate",
        "arguments": {"expression": "2+2"}
      }
    }
    ↓
Backend forwards to MCP Server
    POST /tools/calculate
    Body: {"arguments": {"expression": "2+2"}}
    ↓
MCP Server executes tool
    ↓
Returns result
    {"success": true, "result": "Result: 4"}
    ↓
Backend adds tool result to conversation
    ↓
Continues streaming to user
```

## 📦 Component Details

### LibreChat (Frontend)

**Technology:** React, Node.js  
**Purpose:** User interface for chat interactions  
**Port:** 3080

**Key Features:**
- Modern, responsive chat UI
- Multiple conversation support
- File upload capabilities
- Model selection
- User authentication

**Configuration:** `librechat.yaml`

### Backend (Middleware)

**Technology:** FastAPI (Python)  
**Purpose:** Coordinate between LibreChat, OpenRouter, and MCP Server  
**Port:** 8000

**Key Responsibilities:**
1. Message orchestration
2. Server-Sent Events (SSE) streaming
3. OpenRouter API integration
4. MCP tool discovery and execution
5. Error handling and logging
6. CORS management

**Key Files:**
- `backend/app/main.py` - Main application
- `backend/app/openrouter_service.py` - OpenRouter client
- `backend/app/mcp_client.py` - MCP server client

**API Endpoints:**
- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/services/health` - All services health
- `POST /api/chat/messages` - Create message
- `GET /api/chat/messages/{id}/events` - SSE stream
- `GET /api/chat/messages/{id}/status` - Polling fallback
- `GET /api/mcp/tools` - List MCP tools
- `POST /api/mcp/tools/call` - Call MCP tool directly

### MCP Server (Tools)

**Technology:** FastMCP (Python)  
**Purpose:** Provide tools and resources to the LLM  
**Port:** 8001

**Architecture:** Based on Model Context Protocol (MCP)

**Tools Provided:**
1. **get_current_time()** - Returns current date/time
2. **calculate(expression)** - Safe math evaluation
3. **search_web(query, num_results)** - Web search (placeholder)
4. **get_weather(location)** - Weather info (placeholder)
5. **create_task(title, description, priority)** - Task management
6. **analyze_text(text, analysis_type)** - Text analysis

**Resources Provided:**
1. **config://server** - Server configuration
2. **info://capabilities** - Capability information

**Tool Registration:**
```python
@mcp.tool()
def tool_name(param: str) -> ReturnType:
    """Tool description"""
    # Implementation
    return result
```

### OpenRouter (LLM Provider)

**Type:** External API  
**Purpose:** Access to multiple LLM models  
**URL:** https://openrouter.ai/api/v1

**Supported Models:**
- Anthropic Claude (3.5 Sonnet, 3 Opus, 3 Haiku)
- OpenAI GPT (4 Turbo, 4, 3.5)
- Meta Llama (3.1 - 8B, 70B, 405B)
- Google Gemini (Pro, Pro Vision)
- Mistral (Large, Medium)
- And 100+ more models

**Key Features:**
- Unified API for multiple providers
- Pay-as-you-go pricing
- Usage tracking and analytics
- Rate limiting and quotas

### MongoDB

**Type:** Database  
**Purpose:** Store user data and conversations  
**Port:** 27017

**Collections:**
- users
- conversations
- messages
- files

## 🔐 Security Architecture

### Authentication Flow

```
User registers/logs in
    ↓
LibreChat generates JWT token
    ↓
Token stored in browser (httpOnly cookie)
    ↓
Every request includes token
    ↓
LibreChat validates token
    ↓
If valid, processes request
```

### API Key Management

- OpenRouter API key stored in environment variable
- Never exposed to frontend
- Backend manages all external API calls
- Rate limiting at multiple levels

### CORS Configuration

Development:
```
CORS_ALLOW_ORIGINS=*
```

Production:
```
CORS_ALLOW_ORIGINS=https://yourdomain.com
```

## 🔄 Message State Management

The backend maintains in-memory state for active messages:

```python
messages_store = {
    "message_id": {
        "text": "user message",
        "status": "querying_llm",
        "events": [
            {"type": "status", "data": {...}},
            {"type": "token", "data": {"token": "Hello"}},
            {"type": "tool_call", "data": {...}}
        ],
        "done": False,
        "result": None
    }
}
```

**States:**
1. `initialized` - Message created
2. `preparing` - Preparing request
3. `querying_llm` - Waiting for LLM response
4. `completed` - Successfully completed
5. `error` - Error occurred

## 📊 Event Types (SSE)

The backend streams different event types:

1. **status** - Stage updates
   ```json
   {"stage": "preparing", "message": "Preparing your request..."}
   ```

2. **token** - Text chunks from LLM
   ```json
   {"token": "Hello"}
   ```

3. **tool_call** - Tool execution
   ```json
   {
     "tool": "calculate",
     "arguments": {"expression": "2+2"},
     "result": {"success": true, "result": "4"}
   }
   ```

4. **response_complete** - Final response
   ```json
   {
     "full_text": "complete response",
     "token_count": 42,
     "tool_calls": []
   }
   ```

5. **error** - Error occurred
   ```json
   {"message": "Error description"}
   ```

6. **done** - Stream complete
   ```json
   {}
   ```

## 🚀 Scaling Considerations

### Current Limitations

1. **In-memory state** - Messages stored in RAM
   - Not persistent across restarts
   - Limited by server memory
   
2. **Single instance** - No load balancing
   
3. **No queue system** - Direct processing

### Scaling Improvements

For production deployment:

1. **Use Redis for state**
   - Replace in-memory dict with Redis
   - Enable multiple backend instances
   - Persist state across restarts

2. **Add message queue**
   - Use RabbitMQ or Redis Queue
   - Decouple request handling from processing
   - Better load distribution

3. **Implement caching**
   - Cache MCP tool results
   - Cache OpenRouter responses
   - Reduce API calls and costs

4. **Add rate limiting**
   - Per-user rate limits
   - Per-IP rate limits
   - Circuit breakers for external APIs

## 🔧 Extension Points

### Adding New MCP Tools

1. Edit `mcp-server/server.py`
2. Add tool function with `@mcp.tool()` decorator
3. Restart MCP server
4. Tools automatically available to LLM

### Adding New LLM Models

1. Edit `librechat.yaml`
2. Add model to `endpoints.custom.models.default`
3. Restart LibreChat
4. Model available in UI dropdown

### Custom Backend Logic

1. Edit `backend/app/main.py`
2. Add new endpoints or modify `process_message()`
3. Can add:
   - Custom preprocessing
   - Response filtering
   - Additional logging
   - Integration with other services

## 📈 Monitoring and Observability

### Logs

All components log to stdout:
```bash
docker-compose -f dev.yaml logs -f
```

### Health Checks

- Backend: `GET /api/health`
- Services: `GET /api/services/health`
- MCP Tools: `GET /api/mcp/tools`

### Metrics (Future)

Could add:
- Prometheus metrics
- Request latency
- Token usage
- Error rates
- Tool call frequency

## 🎯 Design Decisions

### Why LibreChat?

- Mature, production-ready UI
- Built-in authentication
- Multiple model support
- Active community
- Regular updates

### Why OpenRouter?

- Access to many models via one API
- Pay-as-you-go pricing
- No vendor lock-in
- Usage analytics
- Rate limiting handled

### Why FastMCP?

- Simple tool definition
- Python ecosystem
- Easy to extend
- Type safety
- Standard protocol

### Why FastAPI (Backend)?

- Async support
- SSE streaming
- Auto-generated docs
- Type validation
- Fast performance

## 🔄 Future Enhancements

Potential improvements:

1. **Persistent Sessions** - Use Redis/PostgreSQL
2. **WebSocket Support** - Real-time bidirectional
3. **Multi-user Chat** - Shared conversations
4. **Voice Input/Output** - Speech-to-text, text-to-speech
5. **Advanced Tools** - Browser automation, code execution
6. **RAG Integration** - Vector database for knowledge base
7. **Fine-tuned Models** - Custom model support
8. **Analytics Dashboard** - Usage statistics and insights

## 📚 References

- [LibreChat](https://www.librechat.ai)
- [OpenRouter](https://openrouter.ai)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [FastAPI](https://fastapi.tiangolo.com)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

