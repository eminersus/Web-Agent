# Changelog

## Version 2.0.0 - Major Architecture Redesign

### 🎯 Overview

Complete restructuring of the Web Agent application to use:
- **LibreChat** as the primary chat interface (replaces custom frontend)
- **OpenRouter** as the LLM provider (replaces Ollama)
- **FastMCP** for the MCP server implementation
- **Three-tier architecture**: LibreChat → Backend → MCP Server

### ✨ New Components

#### Added
- **LibreChat Frontend**
  - Professional chat interface with authentication
  - Multi-model support via OpenRouter
  - File uploads and rich messaging
  - Configuration: `librechat.yaml`

- **MCP Server** (`mcp-server/`)
  - Built with FastMCP Python library
  - Provides tools: time, calculator, web search, weather, tasks, text analysis
  - HTTP-based tool execution
  - Extensible tool framework

- **OpenRouter Integration** (`backend/app/openrouter_service.py`)
  - Support for 100+ LLM models
  - Streaming responses
  - Function calling / tool use
  - Pay-as-you-go pricing

- **MCP Client** (`backend/app/mcp_client.py`)
  - HTTP client for MCP server communication
  - Tool discovery and execution
  - Resource access

#### Services
- **MongoDB**: Database for LibreChat (users, conversations, messages)

### 🗑️ Removed Components

#### Deleted
- **Old Frontend** (`frontend/`)
  - `index.html`, `app.js`, `styles.css`
  - Nginx-based static frontend
  - Replaced by LibreChat

- **Ollama Integration** (`backend/app/llm_service.py`)
  - Local LLM service
  - Replaced by OpenRouter

- **Old Docker Compose** (`docker-compose.yml`)
  - Replaced by `dev.yaml` with new architecture

### 🔄 Modified Components

#### Backend (`backend/app/main.py`)
- **Role Changed**: Now acts as middleware between LibreChat and MCP Server
- **New Features**:
  - MCP tool discovery and orchestration
  - OpenRouter streaming integration
  - Tool call execution flow
  - Enhanced SSE streaming with tool events
- **New Endpoints**:
  - `GET /api/services/health` - Check all services
  - `GET /api/mcp/tools` - List available tools
  - `POST /api/mcp/tools/call` - Direct tool invocation

#### Backend Requirements (`backend/requirements.txt`)
- Updated `pydantic` to 2.10.3
- Removed Ollama dependencies
- Added support for newer FastAPI features

### 📁 New Files

#### Configuration
- `librechat.yaml` - LibreChat configuration with OpenRouter and MCP endpoints
- `dev.yaml` - Docker Compose for new architecture
- `.gitignore` - Git ignore patterns

#### Documentation
- `README.md` - Complete rewrite for new architecture
- `GETTING_STARTED.md` - Detailed setup guide
- `QUICKSTART.md` - 5-minute quick start
- `ARCHITECTURE.md` - Deep dive into system architecture
- `CHANGELOG.md` - This file

#### Scripts
- `dev.sh` - Enhanced development script with new commands

#### Environment
- `env.template` - Updated with OpenRouter and new service configuration

### 🏗️ Architecture Changes

#### Before (v1.x)
```
Frontend (Nginx) → Backend (FastAPI) → Ollama (Local LLM)
```

#### After (v2.0)
```
LibreChat → Backend → OpenRouter (LLM Provider)
                ↓
           MCP Server (Tools)
```

### 🔐 Configuration Changes

#### New Environment Variables
```bash
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_TIMEOUT=120.0

# MCP Server
MCP_SERVER_URL=http://mcp-server:8001
MCP_SERVER_NAME=Web-Agent-MCP-Server
MCP_TIMEOUT=60.0

# LibreChat
APP_URL=http://localhost:3080
SESSION_EXPIRY=900000
REFRESH_TOKEN_EXPIRY=604800000
JWT_SECRET=<your-secret>
JWT_REFRESH_SECRET=<your-secret>

# Databases
MONGO_URI=mongodb://mongodb:27017/LibreChat
```

#### Removed Environment Variables
```bash
# Ollama (no longer needed)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://llm:11434
LLM_MODEL=llama3.1:8b-instruct
```

### 🚀 New Features

1. **Multiple LLM Models**
   - Claude 3.5 Sonnet, Claude 3 Opus
   - GPT-4 Turbo, GPT-4, GPT-3.5
   - Llama 3.1 (8B, 70B, 405B)
   - Gemini Pro, Mistral Large
   - 100+ more models via OpenRouter

2. **MCP Tools**
   - `get_current_time()` - Current date and time
   - `calculate(expression)` - Math calculations
   - `search_web(query)` - Web search (placeholder)
   - `get_weather(location)` - Weather info (placeholder)
   - `create_task(title, description, priority)` - Task management
   - `analyze_text(text, type)` - Text analysis

3. **Enhanced UI**
   - Modern, production-ready interface
   - User authentication and profiles
   - Conversation management
   - File uploads
   - Real-time search
   - Mobile responsive

4. **Development Tools**
   - Enhanced `dev.sh` script
   - Health check endpoints
   - Service monitoring
   - Tool testing commands

### 📊 Port Changes

#### Before
- 8080: Frontend (Nginx)
- 8000: Backend API
- 11434: Ollama

#### After
- 3080: LibreChat
- 8000: Backend API
- 8001: MCP Server
- 27017: MongoDB

### 🔧 Migration Guide

If upgrading from v1.x:

1. **Backup data** (if any)
   ```bash
   # Old version had no persistent data
   ```

2. **Update environment**
   ```bash
   cp env.template .env
   # Edit .env with your OpenRouter API key and secrets
   ```

3. **Remove old containers**
   ```bash
   docker-compose down -v
   ```

4. **Start new architecture**
   ```bash
   docker-compose -f dev.yaml up -d
   ```

5. **Create LibreChat account**
   - Navigate to http://localhost:3080
   - Register a new account
   - Start chatting!

### 💰 Cost Considerations

- **Before**: Free (local Ollama models)
- **After**: Pay-per-use via OpenRouter
  - Typical chat: $0.001 - $0.01 per message
  - Monitor usage at https://openrouter.ai/activity
  - Set spending limits in OpenRouter dashboard

### 🎯 Breaking Changes

1. **Frontend removed** - Must use LibreChat UI at port 3080
2. **Ollama removed** - Must have OpenRouter API key
3. **Port changes** - Frontend moved from 8080 to 3080
4. **Authentication required** - Must create LibreChat account
5. **New docker-compose file** - Use `dev.yaml` instead of `docker-compose.yml`

### 📚 Documentation Updates

All documentation has been rewritten to reflect the new architecture:
- README.md: Complete overview
- GETTING_STARTED.md: Detailed setup
- QUICKSTART.md: Fast 5-minute start
- ARCHITECTURE.md: Technical deep dive

### 🐛 Known Issues

None at release time.

### 🔮 Future Plans

- [ ] WebSocket support for real-time communication
- [ ] Voice input/output integration
- [ ] RAG (Retrieval Augmented Generation) with vector database
- [ ] Advanced tool integrations (browser automation, code execution)
- [ ] Redis for distributed state management
- [ ] Production deployment guides
- [ ] Monitoring and analytics dashboard

### 👥 Contributors

- Restructured architecture
- Implemented MCP server with FastMCP
- Integrated LibreChat frontend
- Added OpenRouter LLM provider
- Created comprehensive documentation

### 📝 Notes

This is a major version update with breaking changes. The new architecture provides:
- More scalable design
- Professional UI/UX
- Access to state-of-the-art models
- Extensible tool framework
- Better separation of concerns

### 🙏 Acknowledgments

- [LibreChat](https://www.librechat.ai) - Modern chat interface
- [OpenRouter](https://openrouter.ai) - LLM API aggregator
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework

