# Getting Started with Web Agent

This guide will help you set up and run the Web Agent application with LibreChat, OpenRouter, and MCP Server.

## 📋 Prerequisites

Before you begin, ensure you have:

1. **Docker Desktop** installed and running
   - Download from: https://www.docker.com/products/docker-desktop/
   - Minimum 8GB RAM allocated to Docker
   - 20GB free disk space

2. **OpenRouter API Key**
   - Sign up at: https://openrouter.ai
   - Navigate to: https://openrouter.ai/keys
   - Create a new API key
   - Add credits to your account (pay-as-you-go)

## 🚀 Setup Steps

### Step 1: Configure Environment

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` and update the following **required** values:
   ```bash
   # Required: Your OpenRouter API key
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   
   # Required: Generate secure random strings (use `openssl rand -hex 32`)
   JWT_SECRET=<generate-random-string>
   JWT_REFRESH_SECRET=<generate-random-string>
   ```

   **Generate secure secrets:**
   ```bash
   # On macOS/Linux:
   openssl rand -hex 32
   
   # Or use Python:
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

### Step 2: Start the Services

Start all services using Docker Compose:

```bash
docker-compose -f dev.yaml up -d
```

This will start:
- LibreChat (frontend) on port 3080
- Backend (middleware) on port 8000
- MCP Server (tools) on port 8001
- MongoDB on port 27017

### Step 3: Wait for Services to Initialize

Check if all services are running:

```bash
docker-compose -f dev.yaml ps
```

Check logs to ensure everything started correctly:

```bash
# Check backend logs
docker-compose -f dev.yaml logs backend

# Check MCP server logs
docker-compose -f dev.yaml logs mcp-server

# Check LibreChat logs
docker-compose -f dev.yaml logs librechat
```

### Step 4: Access LibreChat

1. Open your browser and navigate to: **http://localhost:3080**

2. You'll see the LibreChat registration page

3. Create a new account:
   - Enter your email (doesn't need to be real for local development)
   - Choose a username
   - Create a secure password
   - Click "Submit"

4. Log in with your credentials

### Step 5: Start Chatting!

1. Select the **OpenRouter** endpoint from the dropdown

2. Choose a model (e.g., Claude 3.5 Sonnet, GPT-4, Llama 3.1)

3. Start a conversation!

4. Try using MCP tools by asking questions like:
   - "What time is it?"
   - "Calculate 123 * 456"
   - "Create a task to review the documentation"

## 🔍 Verifying the Setup

### Check Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "environment": "development"
}
```

### Check All Services Health

```bash
curl http://localhost:8000/api/services/health
```

Expected response:
```json
{
  "backend": {"status": "healthy"},
  "openrouter": {"status": "healthy"},
  "mcp_server": {"status": "healthy"}
}
```

### List Available MCP Tools

```bash
curl http://localhost:8000/api/mcp/tools
```

This should return a list of available tools from the MCP server.

## 🛠️ Common Issues

### Issue: Services won't start

**Solution:** Clean up and rebuild

```bash
docker-compose -f dev.yaml down -v
docker-compose -f dev.yaml up --build -d
```

### Issue: "OpenRouter service is unhealthy"

**Possible causes:**
1. Invalid API key
2. No credits in OpenRouter account
3. Network connectivity issues

**Solution:**
- Check your `.env` file for correct `OPENROUTER_API_KEY`
- Verify your OpenRouter account has credits
- Check Docker container logs: `docker-compose -f dev.yaml logs backend`

### Issue: MongoDB connection errors

**Solution:** Restart MongoDB with clean volumes

```bash
docker-compose -f dev.yaml down mongodb
docker volume rm web-agent_mongodb-data
docker-compose -f dev.yaml up -d mongodb
```

Wait for MongoDB to initialize, then restart other services:

```bash
docker-compose -f dev.yaml restart librechat
```

### Issue: "MCP Server is not responding"

**Solution:** Check MCP server logs

```bash
docker-compose -f dev.yaml logs mcp-server
```

Restart MCP server:

```bash
docker-compose -f dev.yaml restart mcp-server
```

### Issue: Port already in use

**Solution:** Change ports in `dev.yaml` or stop conflicting services

Find what's using the port:
```bash
# On macOS/Linux:
lsof -i :3080
lsof -i :8000
lsof -i :8001
```

## 📊 Monitoring

### View logs in real-time

```bash
# All services
docker-compose -f dev.yaml logs -f

# Specific service
docker-compose -f dev.yaml logs -f backend
docker-compose -f dev.yaml logs -f mcp-server
docker-compose -f dev.yaml logs -f librechat
```

### Check resource usage

```bash
docker stats
```

## 🔄 Updating the Application

### Pull latest changes

```bash
git pull origin main
```

### Rebuild and restart services

```bash
docker-compose -f dev.yaml down
docker-compose -f dev.yaml up --build -d
```

## 🧹 Cleaning Up

### Stop all services

```bash
docker-compose -f dev.yaml down
```

### Remove all data (including database)

```bash
docker-compose -f dev.yaml down -v
```

### Remove Docker images

```bash
docker-compose -f dev.yaml down --rmi all
```

## 🎯 Next Steps

1. **Customize MCP Tools**: Edit `mcp-server/server.py` to add your own tools
2. **Configure Models**: Edit `librechat.yaml` to add or remove models
3. **Integrate APIs**: Replace placeholder implementations in MCP tools with real APIs
4. **Deploy to Production**: See deployment documentation

## 📚 Additional Resources

- [LibreChat Documentation](https://www.librechat.ai/docs)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 💡 Tips

- Start with the Claude 3.5 Sonnet model - it's powerful and cost-effective
- Use the `temperature` parameter to control response creativity (0.0 = focused, 1.0 = creative)
- Monitor your OpenRouter usage and costs at https://openrouter.ai/activity
- Keep your `.env` file secure and never commit it to version control

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `docker-compose -f dev.yaml logs`
2. Verify your configuration in `.env`
3. Review this guide's troubleshooting section
4. Open an issue on GitHub with:
   - Error messages
   - Relevant logs
   - Steps to reproduce

Happy chatting! 🚀
