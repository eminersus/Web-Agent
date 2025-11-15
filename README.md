# Web Agent with LibreChat, OpenRouter, and MCP

A modern web agent application using LibreChat as the frontend, OpenRouter for LLM access, and Model Context Protocol (MCP) for tool integration.

## 🏗️ Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  LibreChat  │ ───────>│   Backend   │ ───────>│ MCP Server  │
│  (Frontend) │         │ (Middleware)│         │   (Tools)   │
└─────────────┘         └─────────────┘         └─────────────┘
      │                        │                        │
      │                        │                        │
      v                        v                        v
   MongoDB              OpenRouter API            FastMCP Tools
  (Database)            (LLM Provider)            (Python)
```

### Components

1. **LibreChat**: Modern chat interface (replaces custom frontend)
2. **Backend**: FastAPI middleware that coordinates between LibreChat and MCP Server
3. **MCP Server**: FastMCP-based server providing tools and capabilities
4. **OpenRouter**: LLM provider supporting multiple models (Claude, GPT-4, Llama, etc.)
5. **MongoDB**: Database for LibreChat

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Web-Agent
   ```

2. **Configure environment variables**
   ```bash
   cp env.template .env
   ```
   
   Edit `.env` and set:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
   - `JWT_SECRET`: A secure random string
   - `JWT_REFRESH_SECRET`: Another secure random string

3. **Start the services**
   ```bash
   docker-compose -f dev.yaml up -d
   ```

4. **Access LibreChat**
   Open your browser and navigate to: `http://localhost:3080`

5. **Create an account**
   - Register a new account in LibreChat
   - Start chatting!

## 📦 Services

### LibreChat (Port 3080)
- Web interface for chat
- Supports multiple models via OpenRouter
- File uploads and rich messaging

### Backend (Port 8000)
- FastAPI middleware
- Coordinates LLM requests and tool calls
- API documentation: `http://localhost:8000/docs`

### MCP Server (Port 8001)
- FastMCP-based tool server
- Provides utilities like:
  - Current time
  - Calculator
  - Web search (placeholder)
  - Weather info (placeholder)
  - Task management
  - Text analysis

### MongoDB (Port 27017)
- Database for LibreChat
- Stores conversations and user data

## 🛠️ Available MCP Tools

The MCP server provides the following tools to the LLM:

1. **get_current_time**: Get current date and time
2. **calculate**: Perform mathematical calculations
3. **search_web**: Search the web (placeholder - integrate with real API)
4. **get_weather**: Get weather information (placeholder - integrate with real API)
5. **create_task**: Create and manage tasks
6. **analyze_text**: Analyze text for sentiment, keywords, or summary

## 🔧 Development

### Project Structure

```
Web-Agent/
├── backend/              # FastAPI backend middleware
│   ├── app/
│   │   ├── main.py              # Main FastAPI app
│   │   ├── openrouter_service.py # OpenRouter client
│   │   ├── mcp_client.py        # MCP client
│   │   └── __init__.py
│   ├── Dockerfile
│   └── requirements.txt
├── mcp-server/           # FastMCP tool server
│   ├── server.py         # MCP server implementation
│   ├── Dockerfile
│   └── requirements.txt
├── librechat.yaml        # LibreChat configuration
├── dev.yaml              # Docker Compose configuration
├── env.template          # Environment variables template
└── README.md             # This file
```

### Running in Development Mode

To run services with hot-reload:

```bash
docker-compose -f dev.yaml up
```

Watch logs for a specific service:

```bash
docker-compose -f dev.yaml logs -f backend
docker-compose -f dev.yaml logs -f mcp-server
```

### Adding New MCP Tools

1. Edit `mcp-server/server.py`
2. Add a new tool using the `@mcp.tool()` decorator:

```python
@mcp.tool()
def my_new_tool(param: str) -> Dict[str, Any]:
    """
    Description of your tool
    
    Args:
        param: Description of parameter
    
    Returns:
        Result dictionary
    """
    # Your implementation
    return {"result": "success"}
```

3. Restart the MCP server:
   ```bash
   docker-compose -f dev.yaml restart mcp-server
   ```

## 🌐 Supported Models (via OpenRouter)

The system supports any model available on OpenRouter, including:

- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **OpenAI**: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
- **Meta**: Llama 3.1 (8B, 70B, 405B)
- **Google**: Gemini Pro, Gemini Pro Vision
- **Mistral**: Mistral Large, Mistral Medium

Configure your preferred models in `librechat.yaml`.

## 🔐 Security

- Change all default secrets in `.env` before production deployment
- Never commit `.env` file to version control
- Use strong JWT secrets
- Restrict CORS origins in production
- Keep OpenRouter API key secure

## 📚 API Documentation

### Backend API

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

Key endpoints:
- `GET /api/health` - Health check
- `GET /api/services/health` - Check all services health
- `POST /api/chat/messages` - Create a new chat message
- `GET /api/chat/messages/{id}/events` - Stream chat events (SSE)
- `GET /api/mcp/tools` - List available MCP tools
- `POST /api/mcp/tools/call` - Call an MCP tool directly

## 🐛 Troubleshooting

### Services won't start
```bash
docker-compose -f dev.yaml down -v
docker-compose -f dev.yaml up --build
```

### Can't connect to OpenRouter
- Check your `OPENROUTER_API_KEY` in `.env`
- Verify your account has credits at openrouter.ai

### MCP tools not working
```bash
docker-compose -f dev.yaml logs mcp-server
```

### LibreChat database issues
```bash
docker-compose -f dev.yaml down mongodb
docker volume rm web-agent_mongodb-data
docker-compose -f dev.yaml up -d mongodb
```

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.
