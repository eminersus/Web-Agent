# Getting Started

Get your Web Agent development environment up and running.

## Prerequisites

- Docker Desktop installed and running
- Terminal/Command line access

**Verify installation:**
```bash
docker --version        # Should be 20.10.x or higher
docker compose version  # Should be 2.x.x or higher
```

**Don't have Docker?** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Quick Start

```bash
cd /Users/emin/Desktop/Web-Agent
./dev.sh start
```

Open http://localhost:8080 — Done! 🎉

## Setup Steps

### 1. Navigate to Project
```bash
cd /Users/emin/Desktop/Web-Agent
```

### 2. Verify Environment Variables

Check your `.env` file exists:
```bash
cat .env
```

If missing, create from template:
```bash
cp env.template .env
```

### 3. Start Services

**Using helper script (recommended):**
```bash
./dev.sh start
```

**Using Docker Compose:**
```bash
docker compose up --build -d
```

### 4. Verify Setup

```bash
# Check running containers
docker ps

# Test endpoints
./dev.sh test

# Or test manually
curl http://localhost:8000/api/health
```

## Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/health |

## Development Commands

### Helper Script Commands

```bash
./dev.sh help       # Show all commands
./dev.sh start      # Start services
./dev.sh stop       # Stop services
./dev.sh restart    # Restart services
./dev.sh rebuild    # Full rebuild
./dev.sh logs       # View all logs
./dev.sh logs-be    # Backend logs only
./dev.sh logs-fe    # Frontend logs only
./dev.sh status     # Container status
./dev.sh test       # Test endpoints
./dev.sh clean      # Clean up
./dev.sh shell-be   # Backend shell
./dev.sh shell-fe   # Frontend shell
```

### Docker Compose Commands

```bash
docker compose up -d              # Start in background
docker compose up --build         # Build and start
docker compose down               # Stop all services
docker compose logs -f            # Follow logs
docker compose logs -f backend    # Backend logs only
docker compose restart            # Restart all
docker compose restart backend    # Restart backend only
docker compose ps                 # List containers
docker compose exec backend bash  # Backend shell
```

## Making Changes

### Backend (Hot Reload Enabled)
1. Edit `backend/app/main.py`
2. Save file
3. Wait 2-3 seconds — auto-reloads ✨

**Example:**
```python
@app.get("/api/hello")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}
```

Test: `curl http://localhost:8000/api/hello?name=Dev`

### Frontend (Live Reload)
1. Edit `frontend/index.html`, `styles.css`, or `app.js`
2. Save file
3. Refresh browser (F5) — changes appear ✨

**Example:**
```html
<h2>My Chat Interface</h2>
```

## Environment Variables

Located in `.env` file:
```bash
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
CORS_ALLOW_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://frontend:80
ENVIRONMENT=development
DEBUG=true
```

To modify, edit `.env` and restart services:
```bash
./dev.sh restart
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using the port
lsof -i :8000
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or change ports in docker-compose.yml
# "8001:8000" instead of "8000:8000"
```

### Docker Not Running

```bash
# Check Docker status
docker info

# If error: Start Docker Desktop application
```

### Containers Won't Start

```bash
# View logs for errors
./dev.sh logs

# Try complete rebuild
./dev.sh rebuild
```

### Changes Not Appearing

**Backend:**
```bash
# Check logs for reload confirmation
./dev.sh logs-be
# Should see: "Reloading..."
```

**Frontend:**
```bash
# Hard refresh browser
# Mac: Cmd + Shift + R
# Windows/Linux: Ctrl + Shift + R
```

### Services Not Accessible

```bash
# Check container status
./dev.sh status

# Restart services
./dev.sh restart

# Clean restart
./dev.sh clean  # Confirm prompt
./dev.sh start
```

### View Detailed Logs

```bash
# All services
./dev.sh logs

# Specific service
docker compose logs backend
docker compose logs frontend

# Follow live logs
docker compose logs -f backend
```

## Daily Workflow

**Start your day:**
```bash
./dev.sh start
```

**Make changes:**
- Edit files in `backend/app/` or `frontend/`
- Changes reload automatically

**View logs:**
```bash
./dev.sh logs
```

**End your day:**
```bash
./dev.sh stop
```

## Testing

**Run automated tests:**
```bash
./dev.sh test
```

**Manual testing:**
```bash
# Backend health
curl http://localhost:8000/api/health

# Backend root
curl http://localhost:8000/

# Frontend
curl -I http://localhost:8080
```

**Browser testing:**
1. Open http://localhost:8080
2. Press F12 (DevTools)
3. Check console for: `Backend health: {status: 'ok'}`

## Next Steps

**Explore the API:**
- Visit http://localhost:8000/docs for interactive API documentation

**Start building:**
- Add chat endpoints in `backend/app/main.py`
- Create chat UI in `frontend/index.html`
- Style it in `frontend/styles.css`
- Add logic in `frontend/app.js`

**Example chat endpoint:**
```python
@app.post("/api/chat")
def chat(message: str):
    return {"response": f"You said: {message}"}
```

**Example frontend fetch:**
```javascript
async function sendMessage(message) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  return response.json();
}
```

## Quick Reference

```
┌─────────────────────────────────────────┐
│  Frontend:  http://localhost:8080      │
│  Backend:   http://localhost:8000      │
│  API Docs:  http://localhost:8000/docs │
├─────────────────────────────────────────┤
│  Start:  ./dev.sh start                │
│  Stop:   ./dev.sh stop                 │
│  Logs:   ./dev.sh logs                 │
│  Test:   ./dev.sh test                 │
└─────────────────────────────────────────┘
```

**You're ready to code! 🚀**
