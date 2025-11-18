# Frontend Guide

## Overview

This project now uses a **custom lightweight frontend** instead of LibreChat. The frontend is a simple, modern chat interface built with HTML, CSS, and vanilla JavaScript.

## What Changed

### Removed Components
- ❌ LibreChat (heavy frontend framework)
- ❌ MongoDB (no longer needed for user management)
- ❌ LibreChat initialization scripts

### New Components
- ✅ Simple HTML/CSS/JS frontend
- ✅ Nginx web server for frontend hosting
- ✅ Direct backend API integration
- ✅ Streaming chat with tool support

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                      │
│           (HTML/CSS/JS + Nginx)                 │
│              Port: 3080                         │
└─────────────┬───────────────────────────────────┘
              │ HTTP/SSE
              v
┌─────────────────────────────────────────────────┐
│                Backend Middleware               │
│         (FastAPI + Chat Service)                │
│              Port: 8000                         │
└─────┬───────────────────────┬───────────────────┘
      │                       │
      │ HTTP                  │ HTTP
      v                       v
┌─────────────┐         ┌─────────────┐
│ OpenRouter  │         │ MCP Server  │
│    (LLM)    │         │   (Tools)   │
│   Remote    │         │  Port: 8001 │
└─────────────┘         └─────────────┘
```

## Features

### Frontend Features
- 💬 **Clean Chat Interface**: Modern, responsive design
- 🔄 **Real-time Streaming**: See responses as they're generated
- 🛠️ **Tool Visualization**: See when and how tools are called
- 💾 **Local Storage**: Chat history saved in browser
- 🎨 **Model Selection**: Choose from multiple AI models
- 📱 **Responsive**: Works on desktop and mobile

### Backend Features
- 🔌 **Streaming API**: Server-Sent Events (SSE) for real-time updates
- 🤖 **OpenRouter Integration**: Access to multiple LLM models
- 🛠️ **MCP Tool Execution**: Automatic tool calling and execution
- 📊 **Health Monitoring**: Built-in health checks
- 🔧 **Easy to Customize**: Simple FastAPI backend

## Getting Started

### 1. Set Environment Variables

Make sure you have your `.env` file configured:

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional
ENVIRONMENT=production
DEBUG=false
```

### 2. Start the Application

```bash
# Start all services
docker-compose up --build

# Or use the dev script
./dev.sh up
```

### 3. Access the Frontend

Open your browser and navigate to:

```
http://localhost:3080
```

## Usage

### Basic Chat

1. Type your message in the input box
2. Press Enter or click the Send button
3. Watch the response stream in real-time

### Tool Usage

The assistant can automatically use tools. Try:

- **"What time is it?"** - Uses the time tool
- **"Calculate 123 * 456"** - Uses the calculator
- **"Search for Python tutorials"** - Uses web search
- **"What's the weather in New York?"** - Uses weather API
- **"Find iPhone on eBay"** - Uses eBay search tool

### Model Selection

At the bottom of the page, you can select different models:
- **Claude 3.5 Sonnet** (Default) - Best for complex tasks
- **GPT-4 Turbo** - OpenAI's most capable model
- **GPT-3.5 Turbo** - Fast and cost-effective
- **Gemini Pro** - Google's multimodal model
- **Llama 3.1 70B** - Open-source powerhouse

### Clear Chat

Click the "Clear Chat" button in the header to start a fresh conversation.

## Customization

### Frontend Customization

The frontend is simple and easy to customize:

- **HTML**: `frontend/index.html`
- **CSS**: `frontend/styles.css`
- **JavaScript**: `frontend/app.js`

#### Changing Colors

Edit `frontend/styles.css` and modify the CSS variables:

```css
:root {
    --primary-color: #2563eb;  /* Change primary color */
    --bg-color: #f8fafc;       /* Change background */
    /* ... more variables */
}
```

#### Adding Features

Edit `frontend/app.js` to add new functionality. The code is well-commented and organized.

### Backend Customization

The backend is in `backend/app/`:

- **Main API**: `main.py`
- **Chat Logic**: `chat_service.py`
- **OpenRouter**: `openrouter_service.py`
- **MCP Client**: `mcp_client.py`

## API Endpoints

### Chat Endpoint

```
POST /api/chat/stream
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.7,
  "stream": true
}
```

Returns: Server-Sent Events (SSE) stream

### Health Check

```
GET /api/health
```

### Services Health

```
GET /api/services/health
```

## Troubleshooting

### Frontend Not Loading

1. Check if nginx container is running:
   ```bash
   docker ps | grep frontend
   ```

2. Check nginx logs:
   ```bash
   docker logs web-agent-frontend
   ```

### Backend Connection Error

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check backend logs:
   ```bash
   docker logs web-agent-backend
   ```

### Tools Not Working

1. Check MCP server status:
   ```bash
   curl http://localhost:8001/health
   ```

2. List available tools:
   ```bash
   curl http://localhost:8001/tools
   ```

3. Check MCP server logs:
   ```bash
   docker logs web-agent-mcp-server
   ```

### OpenRouter Errors

1. Verify your API key is set correctly in `.env`
2. Check if you have credits: https://openrouter.ai/credits
3. Try a different model

## Development

### Running in Development Mode

```bash
# Start with live reload
./dev.sh up

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart backend
```

### Making Frontend Changes

Frontend files are mounted as volumes, so changes are reflected immediately. Just refresh your browser.

### Making Backend Changes

Backend code is also mounted as a volume. The server auto-reloads on changes.

## Performance

### Streaming Performance

- The frontend uses Server-Sent Events (SSE) for real-time streaming
- Nginx is configured with buffering disabled for instant updates
- Average latency: < 100ms for first token

### Scalability

- Frontend: Static files served by nginx (very fast)
- Backend: FastAPI with async/await (handles many concurrent requests)
- MCP Server: FastMCP with async tools (efficient tool execution)

## Comparison with LibreChat

| Feature | LibreChat | Custom Frontend |
|---------|-----------|-----------------|
| **Setup** | Complex | Simple |
| **Dependencies** | MongoDB, Redis, etc. | Just nginx |
| **Size** | ~500MB image | ~10MB image |
| **Customization** | Difficult | Easy |
| **Performance** | Good | Excellent |
| **Tool Support** | MCP via SSE | MCP via REST |
| **User Management** | Yes | No (future) |
| **File Uploads** | Yes | No (future) |

## Future Enhancements

Planned features for the frontend:

- 🔐 **User Authentication**: Login and user management
- 📁 **File Uploads**: Support for images and documents
- 🌙 **Dark Mode**: Toggle dark/light themes
- 💬 **Chat History**: Save and load conversations
- 🔍 **Search**: Search through chat history
- 📊 **Usage Stats**: Track token usage and costs
- 🎤 **Voice Input**: Speech-to-text
- 📤 **Export**: Download conversations as PDF/Markdown

## Contributing

Feel free to customize the frontend to your needs! The codebase is simple and well-documented.

## License

Same as the main project.

