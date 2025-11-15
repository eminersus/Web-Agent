# ⚡ Quick Start Guide

Get up and running with Web Agent in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

## Setup in 4 Steps

### 1️⃣ Clone & Navigate

```bash
cd Web-Agent
```

### 2️⃣ Configure Environment

```bash
# Copy template
cp env.template .env

# Generate secrets (run 3 times to get 3 different keys)
openssl rand -hex 32

   # Edit .env and set:
   # - OPENROUTER_API_KEY=sk-or-v1-your-actual-key
   # - JWT_SECRET=<generated-key-1>
   # - JWT_REFRESH_SECRET=<generated-key-2>
```

### 3️⃣ Start Services

```bash
# Using the dev script
./dev.sh start

# Or using docker-compose directly
docker-compose -f dev.yaml up -d
```

### 4️⃣ Access LibreChat

1. Open: **http://localhost:3080**
2. Click "Sign up"
3. Create an account (email doesn't need to be real)
4. Start chatting!

## 🎯 Try It Out

### Basic Chat

Select a model from the dropdown (try Claude 3.5 Sonnet) and ask a question:

```
Hello! How are you today?
```

### Use MCP Tools

Try these prompts to test the MCP tools:

```
What time is it?
```

```
Calculate 123 * 456 + 789
```

```
Create a task to review the documentation with high priority
```

```
Analyze this text for sentiment: "I love using this application!"
```

## 🔍 Verify Everything Works

```bash
# Check all services are running
./dev.sh status

# Check health of all components
./dev.sh health

# View logs
./dev.sh logs

# Test MCP directly
./dev.sh test-mcp
```

## 📊 Available Ports

- **3080** - LibreChat (frontend)
- **8000** - Backend API
- **8001** - MCP Server
- **27017** - MongoDB

## 🛠️ Common Commands

```bash
# View logs
./dev.sh logs [service]

# Restart services
./dev.sh restart

# Stop everything
./dev.sh stop

# Rebuild after code changes
./dev.sh rebuild

# Reset database
./dev.sh reset-db

# Full cleanup
./dev.sh clean
```

## 🎨 Choose Your Model

In LibreChat, click the model dropdown and select from:

- **Claude 3.5 Sonnet** (Recommended) - Best for complex tasks
- **GPT-4 Turbo** - Great all-rounder
- **Llama 3.1 70B** - Fast and capable
- **Gemini Pro** - Good for creative tasks

## 💡 Tips

1. **Start with Claude 3.5 Sonnet** - It's the most capable
2. **Check costs** - Monitor usage at [openrouter.ai/activity](https://openrouter.ai/activity)
3. **Use tools naturally** - Just ask "what time is it?" or "calculate X"
4. **Adjust temperature** - Lower (0.3) for focused, higher (0.9) for creative

## ❓ Having Issues?

### Services won't start?
```bash
./dev.sh clean
./dev.sh setup
```

### Can't connect to OpenRouter?
- Check your API key in `.env`
- Verify you have credits at openrouter.ai

### MCP tools not working?
```bash
./dev.sh logs mcp-server
```

### Need help?
```bash
./dev.sh help
```

## 📚 Learn More

- [Full Documentation](./README.md)
- [Architecture Details](./ARCHITECTURE.md)
- [Detailed Setup](./GETTING_STARTED.md)

## 🚀 What's Next?

1. **Customize MCP Tools** - Edit `mcp-server/server.py`
2. **Add More Models** - Edit `librechat.yaml`
3. **Integrate Real APIs** - Replace placeholder implementations
4. **Deploy to Production** - See deployment docs

---

**That's it!** You're ready to chat with AI using tools! 🎉

