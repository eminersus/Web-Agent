# Web Agent Architecture

This document provides detailed information about the Web Agent architecture, which follows the sagemind pattern of using FastMCP with direct SSE connections.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Components](#components)
4. [Data Flow](#data-flow)
5. [Communication Protocols](#communication-protocols)
6. [Comparison with Sagemind](#comparison-with-sagemind)
7. [Future Enhancements](#future-enhancements)

## Overview

Web Agent implements a modern chat interface with AI capabilities using:
- **LibreChat**: Web frontend
- **FastMCP**: Tool server with SSE transport
- **OpenRouter**: Multi-model LLM provider
- **Backend Middleware**: Monitoring and future flow control

### Key Design Principles

1. **Direct MCP Connection**: LibreChat connects directly to MCP server via SSE
2. **Modular Tools**: Tools organized by domain (tools, web, tasks)
3. **Type Safety**: Pydantic models and type annotations throughout
4. **Extensibility**: Easy to add new tools and capabilities
5. **Observability**: Backend middleware for monitoring and debugging

## Architecture Pattern

### Traditional Architecture (Not Used)

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│LibreChat │──────>│  Backend │──────>│   MCP    │
└──────────┘  HTTP └──────────┘  HTTP └──────────┘
                         │
                         v
                   ┌──────────┐
                   │    LLM   │
                   └──────────┘
```

Problems:
- Backend acts as a proxy for all requests
- Increased latency
- Complex request/response handling
- Backend becomes a bottleneck

### FastMCP/SSE Architecture (Used - Sagemind Pattern)

```
┌────────────────┐
│   LibreChat    │
└────────┬───────┘
         │
         │ SSE (Direct)
         v
┌────────────────┐         ┌────────────────┐
│   MCP Server   │         │    Backend     │
│  (FastMCP/SSE) │         │  (Middleware)  │
└────────┬───────┘         └────────┬───────┘
         │                          │
         │ Tool Execution           │ Monitoring
         v                          v
    ┌────────┐              ┌────────────┐
    │  Tools │              │ OpenRouter │
    └────────┘              └────────────┘
```

Benefits:
- Low latency (direct connection)
- Real-time streaming
- Backend as optional middleware
- Clean separation of concerns

## Components

### 1. LibreChat

**Role**: Web UI and conversation management

**Configuration** (`librechat.yaml`):
```yaml
endpoints:
  custom:
    - name: "OpenRouter"
      type: openai
      baseURL: "https://openrouter.ai/api/v1"
      apiKey: "${OPENROUTER_API_KEY}"

mcpServers:
  web-agent-mcp:
    type: sse
    url: "http://mcp-server:8001/sse"
    startup: true
```

**Key Features**:
- Connects to OpenRouter for LLM inference
- Connects to MCP server via SSE for tools
- Manages conversations and user sessions
- Handles file uploads

### 2. MCP Server (FastMCP)

**Role**: Provide tools to the LLM via MCP protocol

**Implementation** (`mcp-server/server.py`):
```python
from fastmcp import FastMCP

mcp = FastMCP("Web-Agent-MCP", INSTRUCTIONS)

# Tools registered from modular APIs
tools_api = ToolsAPI(mcp)
web_api = WebAPI(mcp)
tasks_api = TasksAPI(mcp)

# Run with SSE transport
mcp.run(transport="sse", host=HOST, port=PORT)
```

**Transport**: SSE (Server-Sent Events)
- LibreChat initiates SSE connection to `/sse`
- Bidirectional communication for tool calls
- Real-time streaming of results

**Tool Organization**:
```
mcp-server/
├── api/
│   ├── tools.py    # Basic: time, calc, text analysis
│   ├── web.py      # Web: search, weather
│   └── tasks.py    # Task management
└── server.py       # FastMCP initialization
```

### 3. Backend Middleware

**Role**: Optional monitoring and future flow control

**Purpose**:
- Health checks for all services
- OpenRouter API wrapper
- Logging and analytics
- **Future**: Interrupt and redirect conversations
- **Future**: Custom processing pipelines

**Key Endpoints**:
- `GET /api/health` - Backend health
- `GET /api/services/health` - All services health
- `GET /api/mcp/info` - MCP server information
- `POST /api/flow/interrupt` - (Placeholder) Interrupt conversation
- `POST /api/flow/redirect` - (Placeholder) Redirect flow

**Why It's Separate**:
- LibreChat → MCP connection is direct for performance
- Backend doesn't proxy tool calls
- Backend focuses on monitoring and control plane
- Allows future advanced features without affecting core flow

### 4. MongoDB

**Role**: Persistence layer for LibreChat

**Stores**:
- User accounts
- Conversations
- Files and attachments
- Session data

### 5. OpenRouter

**Role**: LLM provider

**Features**:
- Multiple model support (Claude, GPT-4, Llama, etc.)
- Pay-per-use pricing
- Unified API interface
- Model fallbacks

## Data Flow

### Normal Conversation Flow

```
1. User sends message
   ┌──────────┐
   │ User     │
   └────┬─────┘
        │ "What time is it?"
        v
   ┌──────────────┐
   │ LibreChat    │
   └────┬─────────┘
        │
        │ (a) Send to OpenRouter
        v
   ┌──────────────┐
   │ OpenRouter   │ LLM decides to call tool
   └────┬─────────┘
        │ "Call get_current_time()"
        v
   ┌──────────────┐
   │ LibreChat    │
   └────┬─────────┘
        │ (b) SSE to MCP
        v
   ┌──────────────┐
   │ MCP Server   │ Execute tool
   └────┬─────────┘
        │ "2024-01-15 14:30:45"
        v
   ┌──────────────┐
   │ LibreChat    │
   └────┬─────────┘
        │ (c) Send result to OpenRouter
        v
   ┌──────────────┐
   │ OpenRouter   │ Generate response
   └────┬─────────┘
        │ "It is 2:30 PM on January 15, 2024"
        v
   ┌──────────────┐
   │ LibreChat    │
   └────┬─────────┘
        │
        v
   ┌──────────┐
   │ User     │
   └──────────┘
```

### Tool Execution Detail

```
LibreChat                    MCP Server
    │                            │
    │ SSE Connection Established │
    ├───────────────────────────>│
    │                            │
    │ JSON-RPC Request           │
    │ {                          │
    │   "method": "tools/call",  │
    │   "params": {              │
    │     "name": "calculate",   │
    │     "arguments": {         │
    │       "expression": "2+2"  │
    │     }                      │
    │   }                        │
    │ }                          │
    ├───────────────────────────>│
    │                            │ Execute tool
    │                            │ calculate("2+2")
    │                            │
    │ JSON-RPC Response          │
    │ {                          │
    │   "result": {              │
    │     "content": [{          │
    │       "type": "text",      │
    │       "text": "Result: 4"  │
    │     }]                     │
    │   }                        │
    │ }                          │
    │<───────────────────────────┤
    │                            │
```

## Communication Protocols

### SSE (Server-Sent Events)

**Why SSE?**
- Native browser support
- Automatic reconnection
- Efficient for server-to-client streaming
- Simpler than WebSockets for one-way streams

**Endpoint**: `http://mcp-server:8001/sse`

**Protocol**: MCP over SSE
- Follows Model Context Protocol specification
- JSON-RPC 2.0 messages
- Bidirectional communication via SSE

### HTTP REST

**Backend API**: Standard REST endpoints
- Health checks
- Service monitoring
- Future control plane operations

## Comparison with Sagemind

### Similarities

1. **FastMCP with SSE**: Both use FastMCP library with SSE transport
2. **Direct Connection**: LibreChat connects directly to MCP server
3. **Modular APIs**: Tools organized in separate API modules
4. **OpenRouter**: Both use OpenRouter for LLM access
5. **Docker Compose**: Similar deployment patterns

### Differences

| Aspect | Sagemind | Web Agent |
|--------|----------|-----------|
| **Domain** | Crypto trading bot management | General-purpose web agent |
| **Tools** | Trading: balances, configs, transfers, market data | General: time, calc, web search, tasks |
| **Backend** | No separate backend | Backend middleware for monitoring |
| **Purpose** | Specific to crypto trading | General-purpose extensible |
| **Additional Services** | run-python-mcp for code execution | None (can be added) |

### Architecture Inheritance

**From Sagemind**:
```python
# Sagemind pattern
mcp = FastMCP("SageBot MCP", INSTRUCTIONS)

# Tool registration via class
class BotAPI:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self._register_tools()
    
    def _register_tools(self):
        self.mcp.tool()(self.get_balances)

bot_api = BotAPI(mcp)

# Run with SSE
mcp.run(transport="sse", host=HOST, port=PORT)
```

**Web Agent Implementation**:
```python
# Same pattern
mcp = FastMCP("Web-Agent-MCP", INSTRUCTIONS)

class ToolsAPI:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self._register_tools()
    
    def _register_tools(self):
        self.mcp.tool()(self.calculate)

tools_api = ToolsAPI(mcp)

# Same SSE transport
mcp.run(transport="sse", host=HOST, port=PORT)
```

## Future Enhancements

### 1. Flow Interruption (Backend Middleware)

**Planned Implementation**:
```python
@app.post("/api/flow/interrupt")
async def interrupt_conversation(conversation_id: str):
    # Interrupt ongoing LLM generation
    # Redirect to different instructions
    # Inject context or constraints
    pass
```

**Use Cases**:
- Emergency stop for sensitive operations
- Budget/rate limiting
- Context switching
- User intervention

### 2. Additional MCP Servers

Following sagemind's pattern of multiple MCP servers:

```yaml
# librechat.yaml
mcpServers:
  web-agent-mcp:
    type: sse
    url: "http://mcp-server:8001/sse"
  
  code-execution-mcp:
    type: sse
    url: "http://code-executor:8002/sse"
  
  database-mcp:
    type: sse
    url: "http://db-tools:8003/sse"
```

### 3. Advanced Tool Integration

**Real APIs**:
- Google Custom Search
- OpenWeatherMap
- Database connections
- File system operations
- API integrations

### 4. Authentication & Authorization

- Tool-level permissions
- User role-based access
- API key management
- Audit logging

### 5. Observability

- Distributed tracing
- Metrics collection
- Log aggregation
- Performance monitoring

## Best Practices

### Adding New Tools

1. **Create module** in `mcp-server/api/`
2. **Follow pattern**:
   ```python
   from fastmcp import FastMCP
   from typing import Annotated
   
   class MyAPI:
       def __init__(self, mcp: FastMCP):
           self.mcp = mcp
           self._register_tools()
       
       def _register_tools(self):
           self.mcp.tool()(self.my_tool)
       
       def my_tool(
           self,
           param: Annotated[str, "Description"]
       ) -> dict:
           """Tool description"""
           return {"result": "value"}
   ```
3. **Register** in `server.py`
4. **Test** via LibreChat

### Security Considerations

1. **Input Validation**: Always validate tool inputs
2. **Sandboxing**: Isolate tool execution
3. **Rate Limiting**: Prevent abuse
4. **Audit Logging**: Track tool usage
5. **Error Handling**: Don't leak sensitive info in errors

### Performance Optimization

1. **Caching**: Cache expensive operations
2. **Async**: Use async/await for I/O
3. **Connection Pooling**: Reuse connections
4. **Lazy Loading**: Load resources on demand

## Debugging

### Enable Debug Logging

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Monitor SSE Connection

```bash
# Watch SSE endpoint
curl -N http://localhost:8001/sse

# Check MCP health
curl http://localhost:8001/health
```

### Inspect Backend

```bash
# Backend health
curl http://localhost:8000/api/services/health

# View config (dev only)
curl http://localhost:8000/api/debug/config
```

## Conclusion

This architecture provides:
- ✅ Low latency direct MCP connections
- ✅ Modular, extensible tool system
- ✅ Optional middleware for advanced features
- ✅ Production-ready with monitoring
- ✅ Based on proven sagemind pattern
- ✅ Easy to understand and extend

For questions or contributions, see the main [README.md](README.md).
