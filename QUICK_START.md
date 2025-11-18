# Quick Start Guide

Get your Web Agent up and running in 3 minutes!

## Prerequisites

- Docker and Docker Compose installed
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

## Step 1: Set Up Environment

Create a `.env` file in the project root:

```bash
# Copy the template
cp env.template .env

# Edit with your API key
nano .env  # or use your favorite editor
```

Add your OpenRouter API key:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Step 2: Start the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

Wait for all services to start (~30 seconds).

## Step 3: Open the Frontend

Open your browser and navigate to:

```
http://localhost:3080
```

You should see a clean chat interface! 🎉

## Step 4: Test It Out

Try these example prompts:

### Basic Chat
```
Hello! How are you?
```

### Use Calculator Tool
```
Calculate 123 * 456
```

### Get Current Time
```
What time is it?
```

### Search the Web
```
Search for "Python tutorials"
```

### Check Weather
```
What's the weather in San Francisco?
```

### Search eBay
```
Find iPhone 15 on eBay
```

## Step 5: Verify Everything Works

Run the test script:

```bash
./test_setup.sh
```

This will check:
- ✓ Frontend is accessible
- ✓ Backend API is responding
- ✓ MCP server is healthy
- ✓ Tools are available
- ✓ Chat endpoint works

## Troubleshooting

### Frontend won't load

```bash
# Check if containers are running
docker ps

# Check frontend logs
docker logs web-agent-frontend

# Restart frontend
docker-compose restart frontend
```

### Backend errors

```bash
# Check backend logs
docker logs web-agent-backend

# Verify API key is set
docker exec web-agent-backend env | grep OPENROUTER

# Restart backend
docker-compose restart backend
```

### Tools not working

```bash
# Check MCP server logs
docker logs web-agent-mcp-server

# Test tools endpoint
curl http://localhost:8001/tools

# Restart MCP server
docker-compose restart mcp-server
```

### "Connection Error" in chat

1. Check if your OpenRouter API key is valid
2. Check if you have credits: https://openrouter.ai/credits
3. Try a different model (dropdown at bottom of page)

## Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## What's Next?

- Read [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) for detailed frontend documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- See [MIGRATION_NOTES.md](MIGRATION_NOTES.md) to learn about changes from LibreChat

## Available Services

Once running, you can access:

- **Frontend**: http://localhost:3080
- **Backend API**: http://localhost:8000
- **MCP Server**: http://localhost:8001
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger UI)

## Common Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Restart a service
docker-compose restart frontend

# Rebuild after code changes
docker-compose up --build

# Stop everything
docker-compose down
```

## Customization

### Change the Primary Color

Edit `frontend/styles.css`:

```css
:root {
    --primary-color: #10b981;  /* Change to green */
}
```

Refresh your browser to see changes!

### Add a New Tool

1. Edit `mcp-server/api/tools.py` (or create new file)
2. Add your tool function with `@mcp.tool()` decorator
3. Restart MCP server: `docker-compose restart mcp-server`

### Change the Model

Edit `frontend/app.js` to change the default model:

```javascript
const OPENROUTER_DEFAULT_MODEL = "openai/gpt-4-turbo";
```

Or select it from the dropdown in the UI!

## Getting Help

- Check the [TROUBLESHOOTING.md](mcp-server/api/ebay/TROUBLESHOOTING.md)
- Review [TEST_GUIDE.md](TEST_GUIDE.md) for testing
- Open an issue on GitHub

## Success! 🎉

You should now have a fully functional Web Agent with:
- ✅ Clean, modern chat interface
- ✅ Multiple AI models via OpenRouter
- ✅ Automatic tool execution
- ✅ Real-time streaming responses
- ✅ Easy to customize and extend

Happy chatting! 🤖

