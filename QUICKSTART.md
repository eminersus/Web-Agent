# Quick Start Guide

Get Web Agent running in 5 minutes!

## Prerequisites

✅ Docker & Docker Compose installed  
✅ OpenRouter API key ([get one here](https://openrouter.ai/keys))

## Steps

### 1. Setup

```bash
# Clone/download the project
cd Web-Agent-master

# Create environment file
cp env.template .env
```

### 2. Configure

Edit `.env` and add your OpenRouter API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

That's it! Other settings have sensible defaults.

### 3. Start

```bash
docker-compose -f dev.yaml up -d
```

Wait 30-60 seconds for services to start.

### 4. Use

Open your browser:
```
http://localhost:3080
```

**Default Login Credentials:**
- **Email:** `user@localhost`
- **Password:** `password`

1. Log in with the default credentials above (no signup needed!)
2. Select **"OpenRouter"** → **"Claude 3.5 Sonnet"**
3. Start chatting!

## Test the Tools

Try these messages:

```
What time is it?
```

```
Calculate 123 * 456
```

```
Create a task to review the project documentation
```

```
List all my tasks
```

## Verify Everything Works

```bash
# Check services
curl http://localhost:8000/api/services/health

# Should return:
# {
#   "backend": {"status": "healthy"},
#   "openrouter": {"status": "healthy"},
#   "mcp_server": {"status": "healthy"}
# }
```

## Stop Services

```bash
docker-compose -f dev.yaml down
```

## Troubleshooting

### Services won't start?
```bash
docker-compose -f dev.yaml down -v
docker-compose -f dev.yaml up --build
```

### Can't access LibreChat?
```bash
docker-compose -f dev.yaml logs librechat
```

### OpenRouter errors?
- Check your API key in `.env`
- Ensure you have credits at [openrouter.ai](https://openrouter.ai)

## Next Steps

📖 Read the [GETTING_STARTED.md](GETTING_STARTED.md) for detailed information  
🏗️ Learn about the [architecture](ARCHITECTURE.md)  
🔧 Add your own [custom tools](README.md#adding-new-mcp-tools)

## Architecture

```
LibreChat (3080) ─SSE─> MCP Server (8001)
                           │
                        Tools API
                           │
Backend (8000) ────────> OpenRouter
   │
Monitoring
```

**Key Points:**
- LibreChat connects **directly** to MCP via SSE
- Backend is for monitoring (doesn't proxy requests)
- Based on sagemind architecture pattern
- FastMCP for easy tool development

## Available Tools

- ⏰ Get current time
- 🔢 Calculate math expressions
- 🌐 Web search (placeholder)
- ☁️ Weather (placeholder)
- ✅ Task management
- 📝 Text analysis

## Configuration Files

- `.env` - Your settings
- `librechat.yaml` - LibreChat + MCP config
- `dev.yaml` - Development docker-compose
- `docker-compose.yaml` - Production docker-compose

## Ports

- **3080** - LibreChat (main UI)
- **8000** - Backend API ([docs](http://localhost:8000/docs))
- **8001** - MCP Server
- **27017** - MongoDB

## Common Commands

```bash
# Start
docker-compose -f dev.yaml up -d

# Stop
docker-compose -f dev.yaml down

# Restart service
docker-compose -f dev.yaml restart mcp-server

# View logs
docker-compose -f dev.yaml logs -f

# Rebuild
docker-compose -f dev.yaml up --build -d
```

## Production

For production deployment:

1. Use `docker-compose.yaml` (not `dev.yaml`)
2. Set secure JWT secrets
3. Set `ENVIRONMENT=production`
4. Set `DEBUG=false`
5. Configure domain and SSL
6. Restrict CORS

See [README.md](README.md) for details.

---

**Questions?** See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed guide!
