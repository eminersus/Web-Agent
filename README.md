# Web Agent with LibreChat, OpenRouter, and FastMCP

A modern web agent application using LibreChat as the frontend, OpenRouter for LLM access, and FastMCP (Model Context Protocol) for tool integration. This project follows the architecture pattern from sagemind, implementing a clean separation between the frontend, middleware, and MCP tools.

## 🏗️ Architecture

```
┌─────────────────┐
│   LibreChat     │  (Frontend - Port 3080)
│   (Frontend UI) │
└────────┬────────┘
         │
         │ Direct SSE Connection
         │
         ┌────────────────────┐
         │                    │
         v                    v
┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │Backend Middleware│
│   (FastMCP/SSE) │    │   (Optional)     │
│   Port 8001     │    │   Port 8000      │
└─────────────────┘    └─────────────────┘
         │                      │
    Tool Execution         Monitoring &
    via FastMCP           Future Flow Control
         │                      │
         v                      v
   ┌──────────┐          ┌──────────┐
   │   Tools  │          │OpenRouter│
   │   API    │          │   API    │
   └──────────┘          └──────────┘

                  ┌──────────┐
                  │ MongoDB  │
                  │ Port     │
                  │ 27017    │
                  └──────────┘
```

### Key Architecture Features

**Direct MCP Connection**: LibreChat connects directly to the MCP server via SSE (Server-Sent Events), similar to sagemind architecture. This provides:
- Real-time tool execution
- Efficient streaming responses
- Native MCP protocol support

**Backend Middleware**: Optional layer for:
- Monitoring and logging
- Future flow interruption capabilities
- Custom processing pipelines
- Analytics and debugging

**FastMCP Implementation**: Uses the FastMCP library (same as sagemind) for:
- Easy tool registration
- SSE transport
- Type-safe API definitions
- Automatic schema generation

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenRouter API key from [openrouter.ai](https://openrouter.ai/keys)

### Setup

1. **Clone and configure**
   ```bash
   git clone <your-repo-url>
   cd Web-Agent-master
   cp env.template .env
   ```

2. **Set your OpenRouter API key in `.env`**
   ```bash
   # Edit .env and set:
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   
   # Generate secure secrets (optional, defaults provided):
   JWT_SECRET=$(openssl rand -hex 32)
   JWT_REFRESH_SECRET=$(openssl rand -hex 32)
   NEXTAUTH_SECRET=$(openssl rand -hex 32)
   ```

3. **Start all services**
   
   For development:
   ```bash
   docker-compose -f dev.yaml up -d
   ```
   
   For production:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - LibreChat UI: http://localhost:3080
   - Backend API: http://localhost:8000/docs
   - Create an account and start chatting!

## 📦 Services Overview

### LibreChat (Port 3080)
- Modern chat interface
- Direct SSE connection to MCP server
- Supports all OpenRouter models
- File uploads and attachments

### MCP Server (Port 8001)
- FastMCP implementation with SSE transport
- Provides tools directly to LibreChat
- Modular API structure (tools, web, tasks)
- Real-time tool execution

**Available Tools:**
- `get_current_time` - Get current date/time
- `calculate` - Safe mathematical expressions
- `search_web` - Web search (placeholder - integrate your API)
- `get_weather` - Weather info (placeholder - integrate your API)
- `create_task`, `list_tasks`, `update_task`, `delete_task` - Task management
- `analyze_text` - Text sentiment/keyword/summary analysis

### Backend Middleware (Port 8000)
- Monitoring and health checks
- OpenRouter service wrapper
- Future: Flow interruption and redirection
- API docs at `/docs`

### MongoDB (Port 27017)
- LibreChat database
- Stores users, conversations, files

## 🔧 Development

### Project Structure

```
Web-Agent-master/
├── backend/                    # Backend middleware (FastAPI)
│   ├── app/
│   │   ├── main.py            # Main app with monitoring endpoints
│   │   ├── openrouter_service.py
│   │   ├── mcp_client.py      # MCP health check client
│   │   └── __init__.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── mcp-server/                 # FastMCP server (similar to sagemind)
│   ├── api/
│   │   ├── tools.py           # Basic tools (time, calc, text)
│   │   ├── web.py             # Web search and weather
│   │   ├── tasks.py           # Task management
│   │   └── __init__.py
│   ├── server.py              # FastMCP SSE server
│   ├── Dockerfile
│   └── requirements.txt
│
├── librechat.yaml             # LibreChat + MCP configuration
├── dev.yaml                   # Development docker-compose
├── docker-compose.yaml        # Production docker-compose
├── env.template               # Environment variables template
├── ARCHITECTURE.md            # Detailed architecture docs
└── README.md                  # This file
```

### Adding New MCP Tools

Following the sagemind pattern:

1. **Create a new API module** (e.g., `mcp-server/api/mytools.py`):

```python
from fastmcp import FastMCP
from typing import Annotated

class MyToolsAPI:
    """My custom tools"""
    
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self._register_tools()
    
    def _register_tools(self):
        """Register tools with MCP"""
        self.mcp.tool()(self.my_tool)
    
    def my_tool(
        self,
        param: Annotated[str, "Description of parameter"]
    ) -> dict:
        """
        Tool description that the LLM sees.
        
        Args:
            param: Parameter description
        
        Returns:
            Result dictionary
        """
        return {"result": f"Processed: {param}"}
```

2. **Register in `server.py`**:

```python
from api.mytools import MyToolsAPI

# After instantiating mcp
mytools_api = MyToolsAPI(mcp)
```

3. **Restart the MCP server**:
   ```bash
   docker-compose -f dev.yaml restart mcp-server
   ```

The tool is now automatically available in LibreChat!

### Local Development

**Watch logs:**
```bash
# All services
docker-compose -f dev.yaml logs -f

# Specific service
docker-compose -f dev.yaml logs -f mcp-server
docker-compose -f dev.yaml logs -f backend
```

**Rebuild after code changes:**
```bash
docker-compose -f dev.yaml up -d --build mcp-server
docker-compose -f dev.yaml up -d --build backend
```

**Test MCP server directly:**
```bash
# Health check
curl http://localhost:8001/health

# SSE endpoint (LibreChat connects here)
curl http://localhost:8001/sse
```

## 🌐 Model Selection (OpenRouter)

Configure models in `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: "OpenRouter"
      models:
        default:
          - "anthropic/claude-3.5-sonnet"
          - "openai/gpt-4-turbo"
          - "meta-llama/llama-3.1-70b-instruct"
        fetch: true  # Auto-fetch available models
```

Supported providers:
- Anthropic (Claude 3.5 Sonnet, Opus, Haiku)
- OpenAI (GPT-4 Turbo, GPT-4, GPT-3.5)
- Meta (Llama 3.1 - 8B, 70B, 405B)
- Google (Gemini Pro)
- Mistral AI
- And many more!

## 🔐 Security Best Practices

**Before production deployment:**

1. **Generate secure secrets:**
   ```bash
   export JWT_SECRET=$(openssl rand -hex 32)
   export JWT_REFRESH_SECRET=$(openssl rand -hex 32)
   export NEXTAUTH_SECRET=$(openssl rand -hex 32)
   ```

2. **Restrict CORS:**
   ```bash
   # In .env
   CORS_ALLOW_ORIGINS=https://yourdomain.com
   ```

3. **Disable debug mode:**
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   ```

4. **Secure your OpenRouter key:**
   - Never commit `.env` to git
   - Use environment variables or secrets manager
   - Rotate keys periodically

## 🐛 Troubleshooting

### Services won't start
```bash
docker-compose -f dev.yaml down -v
docker-compose -f dev.yaml up --build
```

### LibreChat can't connect to MCP
Check MCP server logs:
```bash
docker-compose -f dev.yaml logs mcp-server
```

Verify SSE endpoint is accessible:
```bash
curl http://localhost:8001/health
```

### OpenRouter authentication fails
1. Verify API key in `.env`
2. Check OpenRouter account has credits
3. Test with backend:
   ```bash
   curl http://localhost:8000/api/openrouter/models
   ```

### Tools not appearing in LibreChat
1. Check `librechat.yaml` MCP configuration
2. Restart LibreChat:
   ```bash
   docker-compose -f dev.yaml restart librechat
   ```
3. Verify MCP server is healthy:
   ```bash
   curl http://localhost:8000/api/services/health
   ```

### Database issues
Reset MongoDB:
```bash
docker-compose -f dev.yaml down mongodb
docker volume rm web-agent-master_mongodb-data
docker-compose -f dev.yaml up -d
```

## 📚 Additional Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture documentation
- [GETTING_STARTED.md](GETTING_STARTED.md) - Step-by-step tutorial
- [Backend API Docs](http://localhost:8000/docs) - Interactive API documentation

## 🔄 Comparison with Sagemind

This project follows the sagemind architecture pattern:

**Similarities:**
- FastMCP with SSE transport
- Direct LibreChat to MCP connection
- Modular API structure
- OpenRouter integration

**Differences:**
- Backend middleware for future flow control (sagemind doesn't have this)
- Web Agent specific tools vs crypto trading tools
- Simplified for general-purpose use

## 🚦 Status

- ✅ LibreChat frontend integration
- ✅ FastMCP server with SSE transport
- ✅ Direct MCP to LibreChat connection
- ✅ OpenRouter multi-model support
- ✅ Modular tool architecture
- ✅ Backend monitoring middleware
- 🚧 Flow interruption (placeholder)
- 🚧 Advanced tool integrations (web search, weather APIs)

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

- GitHub Issues: [Your repo issues page]
- Documentation: See [GETTING_STARTED.md](GETTING_STARTED.md)
