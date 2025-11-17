# Changelog

All notable changes to the Web Agent project are documented in this file.

## [2.0.0] - 2024-11-15

### 🎉 Major Architecture Overhaul - Sagemind Pattern Implementation

This release completely restructures the project to follow the sagemind architecture pattern with FastMCP and SSE transport.

### Added

#### MCP Server (FastMCP Implementation)
- ✨ **FastMCP Server** with SSE transport (replacing custom HTTP POST implementation)
- 📁 **Modular API Structure** following sagemind pattern:
  - `api/tools.py` - Basic tools (time, calculator, text analysis)
  - `api/web.py` - Web tools (search, weather)
  - `api/tasks.py` - Task management (create, list, update, delete)
- 🔧 **New Tools**:
  - `list_tasks` - List and filter tasks
  - `update_task` - Update task status and properties
  - `delete_task` - Delete tasks
- 🐳 **Updated Dockerfile** for FastMCP dependencies
- 📦 **New requirements**: fastmcp==0.4.0

#### Configuration
- 📄 **docker-compose.yaml** - Production deployment configuration
- 🔧 **Updated librechat.yaml** - SSE connection type for MCP
- 📝 **Enhanced env.template** - Better documentation and structure
- 📋 **.env.example** - Example configuration file

#### Documentation
- 📖 **Comprehensive README.md** - Complete project overview
- 🏗️ **ARCHITECTURE.md** - Detailed architecture documentation
- 🚀 **GETTING_STARTED.md** - Step-by-step setup guide
- 📝 **CHANGELOG.md** - This file

#### Backend Middleware
- 🔄 **Redesigned main.py** - Focus on monitoring and future flow control
- 🏥 **Enhanced health checks** - Service status monitoring
- 🎯 **Flow control placeholders** - `/api/flow/interrupt` and `/api/flow/redirect`
- 📊 **Monitoring endpoints** - Service information and statistics
- 🔍 **Debug endpoints** - Development configuration viewer
- 📝 **Updated mcp_client.py** - Health check focused client

### Changed

#### Architecture
- 🔀 **Direct MCP Connection** - LibreChat now connects directly to MCP via SSE
- ⚡ **Removed Backend Proxy** - Backend no longer proxies tool calls (performance improvement)
- 🎭 **Backend Role Change** - Now serves as monitoring and future flow control layer

#### MCP Server
- 🔄 **Transport Change** - HTTP POST → SSE (Server-Sent Events)
- 📦 **Protocol Change** - Custom implementation → FastMCP library
- 🗂️ **Structure Change** - Single file → Modular API classes
- 🏷️ **Type Safety** - Added comprehensive type annotations

#### Configuration
- 📝 **librechat.yaml** - Changed MCP server type from `streamable-http` to `sse`
- 🌐 **Connection URL** - Changed from `/mcp` to `/sse` endpoint
- ⚙️ **Environment Variables** - Reorganized for clarity

### Removed

- 🗑️ **Custom MCP Implementation** - Replaced with FastMCP library
- 🗑️ **Backend Chat Endpoints** - Removed `/api/chat/messages` (now direct via SSE)
- 🗑️ **Backend SSE Stream** - Removed backend SSE proxy
- 🗑️ **In-Memory Message Store** - No longer needed with direct connection

### Technical Details

#### Dependencies Added
```
fastmcp==0.4.0 (MCP server)
```

#### Dependencies Removed
```
sse-starlette (from MCP server - now part of fastmcp)
```

#### API Changes

**Before (v1.x):**
```
LibreChat → Backend → MCP Server
              ↓
         OpenRouter
```

**After (v2.0):**
```
LibreChat → MCP Server (SSE)
    ↓
OpenRouter
    
Backend (Monitoring)
```

#### Configuration Changes

**librechat.yaml**:
```yaml
# Before
mcpServers:
  web-agent-tools:
    type: streamable-http
    url: "http://mcp-server:8001/mcp"

# After
mcpServers:
  web-agent-mcp:
    type: sse
    url: "http://mcp-server:8001/sse"
    startup: true
```

### Migration Guide

For users upgrading from v1.x:

1. **Update Configuration**:
   ```bash
   cp env.template .env
   # Add your OPENROUTER_API_KEY
   ```

2. **Rebuild Containers**:
   ```bash
   docker-compose -f dev.yaml down -v
   docker-compose -f dev.yaml up --build
   ```

3. **Verify Connection**:
   - Check MCP server: `curl http://localhost:8001/health`
   - Check backend: `curl http://localhost:8000/api/services/health`
   - Open LibreChat: http://localhost:3080

4. **Note**: All previous conversations will be preserved in MongoDB

### Breaking Changes

⚠️ **Breaking Changes in v2.0:**

1. **MCP Server Endpoint**: Changed from `/mcp` to `/sse`
2. **Backend API**: Removed chat endpoints (`/api/chat/messages/*`)
3. **Configuration**: `librechat.yaml` requires update
4. **Docker Compose**: New `docker-compose.yaml` for production

### Performance Improvements

- ⚡ **Reduced Latency**: Direct LibreChat → MCP connection
- 🚀 **Better Streaming**: Native SSE support
- 📊 **Lower Resource Usage**: Backend not proxying all requests

### Comparison with Sagemind

**Similarities**:
- ✅ FastMCP with SSE transport
- ✅ Direct LibreChat to MCP connection
- ✅ Modular API structure
- ✅ OpenRouter integration
- ✅ Docker Compose deployment

**Differences**:
- ➕ Backend middleware for monitoring
- ➕ Future flow control capabilities
- ➕ General-purpose tools (vs. crypto-specific)
- ➕ Enhanced documentation

### Known Issues

- 🔲 Weather API is placeholder (needs real integration)
- 🔲 Web search is placeholder (needs real integration)
- 🔲 Flow interruption not yet implemented
- 🔲 Task persistence only in-memory (resets on restart)

### Future Roadmap

- [ ] Real weather API integration
- [ ] Real web search API integration
- [ ] Flow interruption implementation
- [ ] Task persistence to database
- [ ] Additional MCP servers (code execution, database tools)
- [ ] Advanced monitoring and analytics
- [ ] User authentication for backend API

## [1.0.0] - Previous

### Initial Implementation
- LibreChat frontend
- Custom MCP server (HTTP POST)
- Backend middleware with SSE proxy
- Basic tool set
- OpenRouter integration

---

## Version History

- **v2.0.0** - Current (Sagemind pattern implementation)
- **v1.0.0** - Initial release

## Contributing

See the main [README.md](README.md) for contribution guidelines.
