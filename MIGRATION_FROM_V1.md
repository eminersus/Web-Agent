# Migration Guide: v1.x to v2.0 (Sagemind Architecture)

This guide helps you understand what changed and how to migrate from the old architecture to the new FastMCP/SSE based architecture.

## What Changed?

### High-Level Architecture

**Before (v1.x):**
```
┌──────────┐      HTTP      ┌──────────┐     HTTP     ┌──────────┐
│LibreChat │ ──────────────> │ Backend  │ ──────────> │   MCP    │
│          │                 │(Proxy)   │             │ Server   │
└──────────┘                 └──────────┘             └──────────┘
                                   │
                                   v
                             OpenRouter API
```

**After (v2.0):**
```
┌──────────┐      SSE       ┌──────────┐
│LibreChat │ ──────────────> │   MCP    │
│          │                 │ Server   │
└──────────┘                 │(FastMCP) │
     │                       └──────────┘
     │
     v
OpenRouter API

┌──────────┐
│ Backend  │  (Monitoring only)
│(Optional)│
└──────────┘
```

### Key Differences

| Aspect | Old (v1.x) | New (v2.0) |
|--------|------------|------------|
| **MCP Connection** | Backend proxy (HTTP) | Direct SSE from LibreChat |
| **MCP Library** | Custom implementation | FastMCP library |
| **MCP Transport** | streamable-http | SSE (Server-Sent Events) |
| **Backend Role** | Proxy + orchestration | Monitoring + future flow control |
| **Tool Structure** | Single file | Modular API classes |
| **Latency** | Higher (two hops) | Lower (one hop) |
| **Inspiration** | Custom | Sagemind architecture |

## Why the Change?

### Benefits of New Architecture

1. **🚀 Performance**: Direct connection = lower latency
2. **📚 Standards**: Using FastMCP library (industry standard)
3. **🔄 Real-time**: Native SSE support for streaming
4. **🏗️ Modularity**: Cleaner tool organization
5. **🎯 Proven**: Based on successful sagemind pattern
6. **🔧 Maintainability**: Easier to add new tools

### Trade-offs

**Gained:**
- Better performance
- Standard library support
- Cleaner architecture
- Easier tool development

**Lost:**
- Backend no longer intercepts all tool calls
- More complex to add custom middleware for every request

**Solution**: Backend still available for monitoring and future flow control features.

## Migration Steps

### Step 1: Backup Current Setup

```bash
# Stop services
docker-compose -f dev.yaml down

# Backup your .env
cp .env .env.backup

# Backup database (optional)
docker run --rm -v web-agent-master_mongodb-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mongodb-backup.tar.gz /data
```

### Step 2: Update Configuration Files

**Before** (`librechat.yaml`):
```yaml
mcpServers:
  web-agent-tools:
    type: streamable-http
    url: "http://mcp-server:8001/mcp"
    initTimeout: 15000
```

**After** (`librechat.yaml`):
```yaml
mcpServers:
  web-agent-mcp:
    type: sse
    url: "http://mcp-server:8001/sse"
    timeout: 600000
    initTimeout: 600000
    startup: true
```

**Changes:**
- ✏️ Type: `streamable-http` → `sse`
- ✏️ URL: `/mcp` → `/sse`
- ✏️ Added: `startup: true` for auto-connection

### Step 3: Update Environment Variables

Your existing `.env` mostly stays the same, but review new template:

```bash
# Check new template
cat env.template

# Merge any new variables you need
nano .env
```

**New optional variables:**
- `MCP_HOST` - MCP server host (default: 0.0.0.0)
- `MCP_PORT` - MCP server port (default: 8001)
- `DEV_MODE` - Development mode flag

### Step 4: Clean and Rebuild

```bash
# Remove old containers and images
docker-compose -f dev.yaml down -v
docker rmi web-agent-master-mcp-server web-agent-master-backend

# Pull latest code
git pull  # or download new version

# Rebuild
docker-compose -f dev.yaml up --build -d
```

### Step 5: Verify Migration

```bash
# Check services
curl http://localhost:8000/api/services/health

# Should show all healthy:
# {
#   "backend": {"status": "healthy"},
#   "openrouter": {"status": "healthy"},
#   "mcp_server": {
#     "status": "healthy",
#     "transport": "SSE"
#   }
# }
```

### Step 6: Test Functionality

1. Open http://localhost:3080
2. Log in (existing account should work)
3. Try a tool:
   ```
   What time is it?
   ```
4. Verify tool execution works

### Step 7: Cleanup

```bash
# If everything works, remove backup
rm .env.backup
rm mongodb-backup.tar.gz  # if you created one
```

## Code Migration

### If You Added Custom Tools

**Before** (v1.x) - Single file:
```python
# mcp-server/server.py

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    # ... 
    if tool_name == "my_tool":
        result = my_tool_function()
```

**After** (v2.0) - Modular:
```python
# mcp-server/api/mytools.py

from fastmcp import FastMCP
from typing import Annotated

class MyToolsAPI:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self._register_tools()
    
    def _register_tools(self):
        self.mcp.tool()(self.my_tool)
    
    def my_tool(
        self,
        param: Annotated[str, "Description"]
    ) -> str:
        """My tool description"""
        return "result"

# mcp-server/server.py
from api.mytools import MyToolsAPI

mytools = MyToolsAPI(mcp)
```

### If You Modified Backend

**Before** - Backend proxied everything:
```python
# Backend received all tool calls
@app.post("/api/chat/messages")
async def create_message(request):
    # Process with OpenRouter
    # Call MCP tools
    # Stream response
```

**After** - Backend for monitoring:
```python
# Backend monitors, doesn't proxy
@app.get("/api/mcp/info")
async def mcp_info():
    # Check MCP health
    # Return status

@app.post("/api/flow/interrupt")
async def interrupt(request):
    # Future: interrupt LLM flow
```

## API Changes

### Removed Endpoints

These backend endpoints no longer exist:

- ❌ `POST /api/chat/messages` - (Use LibreChat directly)
- ❌ `GET /api/chat/messages/{id}/events` - (SSE from MCP now)
- ❌ `GET /api/chat/messages/{id}/status` - (Not needed)
- ❌ `POST /api/mcp/tools/call` - (LibreChat calls directly)
- ❌ `GET /api/mcp/tools` - (Tools listed via SSE)

### New/Changed Endpoints

Backend now provides:

- ✅ `GET /api/services/health` - All services status
- ✅ `GET /api/mcp/info` - MCP server information
- ✅ `GET /api/openrouter/models` - Available models
- ✅ `POST /api/flow/interrupt` - (Placeholder) Interrupt flow
- ✅ `POST /api/flow/redirect` - (Placeholder) Redirect flow
- ✅ `GET /api/logs/stats` - (Placeholder) Usage stats

## Docker Compose Changes

### Files

**Before:**
- `dev.yaml` - Development only

**After:**
- `dev.yaml` - Development (volume mounts)
- `docker-compose.yaml` - Production

### Service Changes

**MCP Server:**
```yaml
# Before
mcp-server:
  build: ./mcp-server
  ports:
    - "8001:8001"
  environment:
    - MCP_SERVER_NAME=Web-Agent-MCP-Server

# After
mcp-server:
  build: ./mcp-server
  ports:
    - "${MCP_PORT:-8001}:${MCP_PORT:-8001}"
  environment:
    - MCP_HOST=${MCP_HOST:-0.0.0.0}
    - MCP_PORT=${MCP_PORT:-8001}
  healthcheck:
    test: ["CMD-SHELL", "timeout 2 bash -c '</dev/tcp/127.0.0.1/8001' || exit 1"]
```

**Backend:**
- Role changed to monitoring
- MCP_SERVER_URL still needed for health checks
- No longer critical path for tool execution

## Troubleshooting Migration

### Problem: LibreChat shows "MCP server unavailable"

**Check:**
```bash
curl http://localhost:8001/health
```

**Solution:**
```bash
docker-compose -f dev.yaml restart mcp-server
docker-compose -f dev.yaml logs mcp-server
```

### Problem: Tools don't appear

**Check librechat.yaml:**
- Verify `type: sse`
- Verify `url: "http://mcp-server:8001/sse"`
- Verify `startup: true`

**Restart LibreChat:**
```bash
docker-compose -f dev.yaml restart librechat
```

### Problem: "fastmcp not found" error

**Solution:**
```bash
# Rebuild MCP server
docker-compose -f dev.yaml up --build mcp-server
```

### Problem: Old tools still showing

**Clear cache:**
```bash
docker-compose -f dev.yaml down -v
docker-compose -f dev.yaml up -d
```

## Rollback Plan

If you need to rollback:

1. **Restore backup:**
   ```bash
   docker-compose -f dev.yaml down -v
   cp .env.backup .env
   ```

2. **Checkout v1.x:**
   ```bash
   git checkout v1.x  # or your previous branch
   ```

3. **Restart:**
   ```bash
   docker-compose -f dev.yaml up --build -d
   ```

4. **Restore database (if backed up):**
   ```bash
   docker volume create web-agent-master_mongodb-data
   docker run --rm -v web-agent-master_mongodb-data:/data -v $(pwd):/backup \
     ubuntu tar xzf /backup/mongodb-backup.tar.gz -C /
   ```

## Getting Help

### Check Status

```bash
# All services
docker-compose -f dev.yaml ps

# Backend status
curl http://localhost:8000/api/services/health

# MCP health
curl http://localhost:8001/health

# View logs
docker-compose -f dev.yaml logs -f
```

### Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup guide
- [CHANGELOG.md](CHANGELOG.md) - What changed

### Common Issues

See [Troubleshooting](GETTING_STARTED.md#troubleshooting) section in Getting Started guide.

## Benefits You'll Notice

After migration:

1. **Faster responses** - Direct SSE connection
2. **Better streaming** - Real-time tool execution
3. **Cleaner logs** - Separated concerns
4. **Easier debugging** - Modular structure
5. **Standard protocol** - FastMCP compatibility

## Conclusion

The new architecture provides:
- ✅ Better performance
- ✅ Industry-standard libraries
- ✅ Proven design pattern
- ✅ Easier maintenance
- ✅ Future extensibility

While requiring some migration effort, the benefits make it worthwhile!

**Questions?** Open an issue or check the documentation.

---

**Migration completed successfully?** Welcome to v2.0! 🎉

