# Migration from LibreChat to Custom Frontend

This document explains the changes made when migrating from LibreChat to a custom frontend.

## Summary of Changes

### What Was Removed

1. **LibreChat Container**
   - Heavy Docker image (~500MB)
   - Complex configuration
   - MongoDB dependency
   - User management system

2. **MongoDB Container**
   - Database for user accounts
   - Conversation storage
   - No longer needed for simple use case

3. **LibreChat Init Scripts**
   - Database initialization
   - Default user creation

### What Was Added

1. **Custom Frontend** (`frontend/`)
   - `index.html` - Main chat interface
   - `styles.css` - Modern, responsive styling
   - `app.js` - Chat logic with streaming support

2. **Nginx Configuration** (`nginx.conf`)
   - Serves frontend static files
   - Proxies API requests to backend
   - Optimized for SSE streaming

3. **Enhanced Backend**
   - `chat_service.py` - Orchestrates chat with tool calling
   - Enhanced `mcp_client.py` - Direct MCP tool execution
   - Streaming endpoint at `/api/chat/stream`

4. **Enhanced MCP Server**
   - REST endpoints for tool listing (`GET /tools`)
   - REST endpoints for tool execution (`POST /tools/{name}`)
   - Maintains SSE endpoint for future use

## Architecture Comparison

### Before (LibreChat Architecture)

```
LibreChat (Frontend + Backend)
    ↓ SSE
MCP Server (Tools)
    ↓ HTTP
OpenRouter (LLM)
```

LibreChat handled:
- Frontend UI
- User management
- OpenRouter API calls
- MCP protocol over SSE
- Conversation storage

### After (Custom Frontend Architecture)

```
Frontend (HTML/CSS/JS + Nginx)
    ↓ HTTP/SSE
Backend (FastAPI)
    ↓ HTTP (REST)         ↓ HTTPS
MCP Server (Tools)    OpenRouter (LLM)
```

Responsibilities are now:
- **Frontend**: Just the UI and display
- **Backend**: Orchestrates chat + tool calling
- **MCP Server**: Executes tools
- **OpenRouter**: LLM inference

## Configuration Changes

### docker-compose.yaml

**Removed:**
```yaml
librechat:
  image: ghcr.io/danny-avila/librechat:latest
  # ... config

mongo:
  image: mongo:6
  # ... config

librechat-init:
  # ... config
```

**Added:**
```yaml
frontend:
  image: nginx:alpine
  volumes:
    - ./frontend:/usr/share/nginx/html:ro
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  ports:
    - "3080:80"
```

### Environment Variables

**No longer needed:**
- `JWT_SECRET`
- `JWT_REFRESH_SECRET`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `MONGO_URI`
- `ALLOW_REGISTRATION`
- `ALLOW_EMAIL_LOGIN`
- `SESSION_EXPIRY`
- `REFRESH_TOKEN_EXPIRY`

**Still needed:**
- `OPENROUTER_API_KEY` - For LLM access
- `ENVIRONMENT` - dev/production
- `DEBUG` - Debug logging

### MCP Server Changes

Added REST endpoints to `mcp-server/server.py`:

```python
@app.get("/tools")
async def list_tools():
    """List all available tools"""
    # Returns tool definitions

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict):
    """Execute a tool"""
    # Executes and returns result
```

These endpoints allow the backend to directly call MCP tools without needing the full MCP protocol implementation.

## Benefits of the Change

### Simplicity
- ✅ **Fewer components**: No MongoDB, no LibreChat
- ✅ **Smaller footprint**: ~10MB nginx vs ~500MB LibreChat
- ✅ **Faster startup**: No database initialization
- ✅ **Easier debugging**: Simple, readable code

### Flexibility
- ✅ **Easy customization**: Plain HTML/CSS/JS
- ✅ **No build step**: Edit and refresh
- ✅ **Full control**: Modify any aspect easily
- ✅ **Better learning**: Understand every part

### Performance
- ✅ **Faster page loads**: Static files from nginx
- ✅ **Lower latency**: Direct API calls
- ✅ **Better streaming**: Optimized SSE setup
- ✅ **Fewer resources**: No database overhead

## Trade-offs

### What You Lose

1. **User Management**: No built-in authentication/authorization
2. **Conversation Persistence**: Chat history only in browser
3. **File Uploads**: No file handling (yet)
4. **Multi-user**: Single-user experience
5. **Mobile Apps**: No official mobile clients
6. **Presets**: No saved prompt templates

### What You Can Add Back

All of these features can be added incrementally:

1. **Simple Auth**: Add JWT tokens + user table
2. **Persistence**: Add a lightweight DB (SQLite, Postgres)
3. **File Uploads**: Add multipart form handling
4. **Multi-user**: Add user sessions
5. **PWA**: Make it installable as a progressive web app

## Migration Steps

If you're migrating an existing installation:

### 1. Backup

```bash
# Backup MongoDB data (if you want to keep conversations)
docker exec web-agent-mongo mongodump --out=/backup

# Copy backup out of container
docker cp web-agent-mongo:/backup ./mongo-backup
```

### 2. Stop Old Containers

```bash
docker-compose down
```

### 3. Update Repository

```bash
git pull origin main
# Or manually update the files
```

### 4. Remove Old Data (Optional)

```bash
# Remove MongoDB data
rm -rf mongo-data/

# Remove LibreChat volumes
docker volume prune
```

### 5. Start New Setup

```bash
docker-compose up --build
```

### 6. Access New Frontend

Open http://localhost:3080

## Troubleshooting Migration

### Port Conflicts

If port 3080 is still in use:
```bash
# Find and kill old containers
docker ps -a | grep librechat
docker rm -f <container_id>
```

### Image Cache Issues

```bash
# Force rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Frontend Not Loading

```bash
# Check nginx logs
docker logs web-agent-frontend

# Verify files are mounted
docker exec web-agent-frontend ls -la /usr/share/nginx/html
```

## Future Plans

The simplified architecture makes it easier to add features incrementally:

1. **Phase 1** (Current): Basic chat with tools ✅
2. **Phase 2**: Add simple authentication
3. **Phase 3**: Add conversation persistence
4. **Phase 4**: Add file upload support
5. **Phase 5**: Add mobile PWA support
6. **Phase 6**: Add multi-user features

## Questions?

See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) for detailed usage instructions.

## Rollback

If you need to go back to LibreChat:

```bash
# Checkout the previous version
git checkout <previous-commit-hash>

# Rebuild
docker-compose down
docker-compose up --build
```

Note: You'll need to restore MongoDB data if you removed it.

