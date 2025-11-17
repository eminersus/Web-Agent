# Getting Started with Web Agent

This guide will walk you through setting up and using Web Agent step by step.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Starting the Application](#starting-the-application)
5. [First Steps](#first-steps)
6. [Using MCP Tools](#using-mcp-tools)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

## Prerequisites

Before you begin, ensure you have:

1. **Docker** (version 20.10 or later)
   ```bash
   docker --version
   ```

2. **Docker Compose** (version 2.0 or later)
   ```bash
   docker-compose --version
   ```

3. **OpenRouter API Key**
   - Go to [openrouter.ai](https://openrouter.ai)
   - Sign up for an account
   - Navigate to [API Keys](https://openrouter.ai/keys)
   - Create a new API key
   - Add some credits to your account

4. **Basic Command Line Knowledge**
   - Navigating directories
   - Running commands
   - Editing text files

## Installation

### Step 1: Get the Code

Clone the repository:
```bash
git clone <your-repo-url>
cd Web-Agent-master
```

Or if you have a zip file:
```bash
unzip Web-Agent-master.zip
cd Web-Agent-master
```

### Step 2: Verify Project Structure

Ensure you have these files:
```bash
ls -la
```

You should see:
```
├── backend/
├── mcp-server/
├── librechat.yaml
├── dev.yaml
├── docker-compose.yaml
├── env.template
├── README.md
└── GETTING_STARTED.md (this file)
```

## Configuration

### Step 1: Create Environment File

Copy the template:
```bash
cp env.template .env
```

### Step 2: Set Your OpenRouter API Key

Edit `.env` file:
```bash
nano .env
# or
vim .env
# or use your favorite editor
```

Set your OpenRouter API key:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### Step 3: Generate Secure Secrets (Optional)

For better security, generate random secrets:

```bash
# On macOS/Linux
export JWT_SECRET=$(openssl rand -hex 32)
export JWT_REFRESH_SECRET=$(openssl rand -hex 32)
export NEXTAUTH_SECRET=$(openssl rand -hex 32)

echo "JWT_SECRET=$JWT_SECRET" >> .env
echo "JWT_REFRESH_SECRET=$JWT_REFRESH_SECRET" >> .env
echo "NEXTAUTH_SECRET=$NEXTAUTH_SECRET" >> .env
```

Or just use the defaults in `env.template` (not recommended for production).

### Step 4: Review Configuration

Your `.env` should look like:
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
JWT_SECRET=abc123...
JWT_REFRESH_SECRET=def456...
NEXTAUTH_SECRET=ghi789...
APP_URL=http://localhost:3080
ENVIRONMENT=development
DEBUG=true
```

## Starting the Application

### Development Mode

Start all services:
```bash
docker-compose -f dev.yaml up -d
```

This will:
- Download Docker images (first time only)
- Build custom images for backend and MCP server
- Start all services in the background

### Check Service Status

```bash
docker-compose -f dev.yaml ps
```

You should see:
```
NAME                    STATUS
web-agent-librechat     Up (healthy)
web-agent-mongo         Up (healthy)
web-agent-mcp-server    Up (healthy)
web-agent-backend       Up (healthy)
```

### View Logs

Watch all logs:
```bash
docker-compose -f dev.yaml logs -f
```

Watch specific service:
```bash
docker-compose -f dev.yaml logs -f mcp-server
```

Press `Ctrl+C` to stop watching logs.

## First Steps

### Step 1: Open LibreChat

Open your web browser and go to:
```
http://localhost:3080
```

You should see the LibreChat interface.

### Step 2: Create an Account

1. Click **"Sign Up"** or **"Register"**
2. Enter your email and password
3. Confirm your password
4. Click **"Sign Up"**

Note: In development mode, email verification is disabled.

### Step 3: Log In

1. Enter your credentials
2. Click **"Sign In"**
3. You should see the chat interface

### Step 4: Select a Model

1. Look for the model dropdown (usually at the top)
2. Select **"OpenRouter"** as the endpoint
3. Choose a model (e.g., **"Claude 3.5 Sonnet"**)

### Step 5: Start Chatting!

Type a message and press Enter:
```
Hello! Can you tell me what tools you have access to?
```

The LLM should respond listing the available MCP tools.

## Using MCP Tools

The MCP server provides several tools. Here are examples:

### 1. Get Current Time

```
What time is it right now?
```

The LLM will call `get_current_time()` tool and tell you the current date and time.

### 2. Calculate

```
What is 12345 * 67890?
```

The LLM will use the `calculate` tool:
```
calculate("12345 * 67890")
```

### 3. Create Tasks

```
Create a task to buy groceries tomorrow with high priority
```

The LLM will call:
```
create_task(
    title="Buy groceries",
    description="Tomorrow",
    priority="high"
)
```

### 4. List Tasks

```
Show me all my tasks
```

The LLM will call `list_tasks()`.

### 5. Analyze Text

```
Analyze the sentiment of this text: "I love this product!"
```

The LLM will call:
```
analyze_text(
    text="I love this product!",
    analysis_type="sentiment"
)
```

### 6. Weather (Placeholder)

```
What's the weather in San Francisco?
```

The LLM will call `get_weather("San Francisco")`, which currently returns placeholder data.

**To integrate real weather data**: Edit `mcp-server/api/web.py` and add your weather API integration.

### 7. Web Search (Placeholder)

```
Search the web for Python tutorials
```

The LLM will call `search_web("Python tutorials")`, which currently returns placeholder results.

**To integrate real search**: Edit `mcp-server/api/web.py` and add your search API (Google, Bing, DuckDuckGo).

## Troubleshooting

### Services Won't Start

**Problem**: Docker containers fail to start

**Solution**:
```bash
# Stop everything
docker-compose -f dev.yaml down -v

# Rebuild and start
docker-compose -f dev.yaml up --build -d
```

### Can't Access LibreChat

**Problem**: Browser shows "Connection refused" at http://localhost:3080

**Check**:
```bash
# Is LibreChat running?
docker-compose -f dev.yaml ps librechat

# Check logs
docker-compose -f dev.yaml logs librechat
```

**Solution**:
```bash
# Restart LibreChat
docker-compose -f dev.yaml restart librechat
```

### OpenRouter Errors

**Problem**: "Invalid API key" or "Insufficient credits"

**Check**:
1. Verify your API key in `.env`
2. Check your OpenRouter account has credits
3. Test the key:
   ```bash
   curl http://localhost:8000/api/openrouter/models
   ```

**Solution**:
- Double-check the API key (no extra spaces)
- Add credits at [openrouter.ai](https://openrouter.ai)
- Restart services:
  ```bash
  docker-compose -f dev.yaml restart
  ```

### MCP Tools Not Working

**Problem**: LLM says it doesn't have access to tools

**Check**:
```bash
# Is MCP server healthy?
curl http://localhost:8001/health

# Check services health
curl http://localhost:8000/api/services/health
```

**Solution**:
```bash
# Restart MCP server
docker-compose -f dev.yaml restart mcp-server

# Restart LibreChat
docker-compose -f dev.yaml restart librechat
```

### Database Issues

**Problem**: Can't log in or conversations not saving

**Solution**:
```bash
# Reset MongoDB
docker-compose -f dev.yaml down
docker volume rm web-agent-master_mongodb-data
docker-compose -f dev.yaml up -d
```

Note: This will delete all users and conversations.

### Port Conflicts

**Problem**: "Port already in use"

**Check**:
```bash
# Check what's using the port
lsof -i :3080  # LibreChat
lsof -i :8000  # Backend
lsof -i :8001  # MCP Server
```

**Solution**:
- Stop the conflicting service
- Or change ports in `dev.yaml`

## Next Steps

### 1. Add Custom Tools

Learn how to add your own MCP tools:
```bash
# See examples in:
mcp-server/api/tools.py
mcp-server/api/web.py
mcp-server/api/tasks.py
```

Follow the pattern:
1. Create a new API class
2. Register tools with `@mcp.tool()` decorator
3. Add to `server.py`
4. Rebuild container

See [README.md](README.md) for detailed examples.

### 2. Integrate Real APIs

Replace placeholders with real APIs:

**Weather**:
- Sign up for [OpenWeatherMap](https://openweathermap.org/api)
- Add API key to `.env`
- Update `mcp-server/api/web.py`

**Search**:
- Get [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)
- Or use [DuckDuckGo Instant Answer API](https://duckduckgo.com/api)
- Update `mcp-server/api/web.py`

### 3. Try Different Models

Experiment with different LLMs:
- Anthropic Claude (best for complex reasoning)
- OpenAI GPT-4 (great all-rounder)
- Llama 3.1 70B (powerful open model)
- Google Gemini (good for analysis)

Select from the model dropdown in LibreChat.

### 4. Production Deployment

For production:
1. Use `docker-compose.yaml` (not `dev.yaml`)
2. Set secure secrets
3. Disable debug mode
4. Set up domain and SSL
5. Restrict CORS origins

See production deployment guide in [README.md](README.md).

### 5. Backend Middleware

Explore the backend API:
```
http://localhost:8000/docs
```

Features:
- Service health monitoring
- OpenRouter model listing
- MCP server information
- Future: Flow control and interruption

### 6. Learn the Architecture

Read detailed architecture docs:
- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete architecture guide
- [README.md](README.md) - Project overview

## Common Use Cases

### Use Case 1: Personal Assistant

```
You: Create a task to call mom tomorrow at 3pm
You: What time is it now?
You: Calculate how many hours until the call
```

### Use Case 2: Research Helper

```
You: Search the web for information about FastMCP
You: Analyze the sentiment of this review: "..."
You: Summarize this text in 50 words
```

### Use Case 3: Development Aid

```
You: Calculate 2^10
You: What is the current timestamp?
You: Create a task to review PR #123
```

## Getting Help

### Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
- [Backend API Docs](http://localhost:8000/docs) - API reference

### Logs

Check service logs:
```bash
docker-compose -f dev.yaml logs -f [service-name]
```

Services:
- `librechat` - Frontend
- `mcp-server` - Tools server
- `backend` - Middleware
- `mongodb` - Database

### Health Checks

```bash
# All services
curl http://localhost:8000/api/services/health

# Individual services
curl http://localhost:3080  # LibreChat
curl http://localhost:8000/api/health  # Backend
curl http://localhost:8001/health  # MCP Server
```

## Congratulations! 🎉

You now have a fully functional Web Agent with:
- ✅ AI chat interface (LibreChat)
- ✅ Multiple LLM models (OpenRouter)
- ✅ MCP tools for enhanced capabilities
- ✅ Extensible architecture

Start building and experimenting! Happy coding! 🚀
