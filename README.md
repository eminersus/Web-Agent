# Web Agent - Development Environment

A full-stack web application with a chat interface, featuring a Python FastAPI backend and a simple HTML/CSS/JS frontend.

## 🚀 Quick Start

**Get started in 3 commands:**

```bash
cd /Users/emin/Desktop/Web-Agent
./dev.sh start
# Open http://localhost:8080
```

**That's it!** See [GETTING_STARTED.md](./GETTING_STARTED.md) for detailed setup instructions.

## 📁 Project Structure

```
Web-Agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py           # FastAPI application
│   ├── Dockerfile            # Backend Docker configuration
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── index.html            # Main HTML page
│   ├── styles.css            # Styling
│   ├── app.js                # Frontend JavaScript
│   └── Dockerfile            # Frontend Docker configuration
├── docker-compose.yml        # Docker Compose orchestration (includes Ollama)
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## 🚀 Prerequisites

Before you begin, ensure you have the following installed:
- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)

To verify your installation:
```bash
docker --version
docker compose version
```

## ⚙️ Setup Instructions

### 1. Clone or Navigate to the Project

```bash
cd /path/to/Web-Agent
```

### 2. Environment Variables

The project uses environment variables stored in a `.env` file. A template is provided in `.env.example`.

**Important:** The `.env` file is already created for you. If you need to modify settings:

```bash
# View current environment variables
cat .env

# Or copy from example if needed
cp .env.example .env
```

**Available Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `UVICORN_HOST` | `0.0.0.0` | Backend server host |
| `UVICORN_PORT` | `8000` | Backend server port |
| `CORS_ALLOW_ORIGINS` | `http://localhost:8080,...` | Allowed CORS origins |
| `ENVIRONMENT` | `development` | Environment name |
| `DEBUG` | `true` | Debug mode flag |

### 3. Build and Run

Start the entire stack with a single command:

```bash
docker compose up --build
```

**Options:**
- Run in detached mode (background): `docker compose up -d --build`
- Rebuild without cache: `docker compose build --no-cache && docker compose up`

### 4. Pull the LLM Model

After starting the services, pull the Llama model:

```bash
docker exec -it web-agent-ollama ollama pull llama3.1:8b
```

This will download the Llama 3.1 8B model (approximately 4.7GB). The model is stored in a Docker volume and persists across container restarts.

**Note:** The backend service waits for Ollama to be healthy before starting (see `depends_on` in docker-compose.yml).

### 5. Access the Application

Once the containers are running and the model is pulled:

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health
- **Ollama API**: http://localhost:11434

## 🔄 Development Workflow

### Hot Reload / Live Updates

Both services are configured for **hot reload** during development:

#### Backend (FastAPI)
- Source code is mounted as a volume: `./backend/app` → `/app/app`
- Uvicorn runs with the `--reload` flag
- **Any changes to Python files will automatically restart the server**

#### Frontend (HTML/CSS/JS)
- Files are mounted as a volume: `./frontend` → `/usr/share/nginx/html`
- Nginx serves files with cache disabled
- **Refresh your browser to see changes immediately**

### Making Changes

1. Edit files in `backend/app/` or `frontend/` directories
2. Changes are reflected automatically:
   - Backend: Wait ~2-3 seconds for auto-reload
   - Frontend: Refresh browser (F5 or Cmd+R)

### Useful Commands

```bash
# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f llm

# Stop containers
docker compose down

# Stop and remove volumes (WARNING: deletes LLM models)
docker compose down -v

# Restart a specific service
docker compose restart backend
docker compose restart frontend
docker compose restart llm

# Execute commands in running containers
docker compose exec backend bash
docker compose exec frontend sh
docker exec -it web-agent-ollama bash

# Ollama-specific commands
docker exec -it web-agent-ollama ollama list               # List downloaded models
docker exec -it web-agent-ollama ollama pull llama3.1:8b   # Pull a model
docker exec -it web-agent-ollama ollama rm llama3.1:8b     # Remove a model
docker exec -it web-agent-ollama ollama run llama3.1:8b    # Interactive chat

# View running containers
docker ps
```

## 🧪 Testing the Setup

### Test Backend

```bash
# Health check
curl http://localhost:8000/api/health

# Root endpoint
curl http://localhost:8000/

# Or visit in browser
open http://localhost:8000/docs
```

### Test Frontend

Open http://localhost:8080 in your browser. You should see a welcome page with:
- Site header
- Welcome message
- Backend health check logged in browser console (F12)

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Uvicorn ASGI server
- **Language**: Python 3.11
- **Port**: 8000
- **Features**:
  - CORS middleware configured
  - Health check endpoint
  - Auto-reload for development
  - Environment variable configuration

### Frontend (Static)
- **Server**: Nginx Alpine
- **Stack**: Vanilla HTML, CSS, JavaScript
- **Port**: 8080 (mapped to container port 80)
- **Features**:
  - Modern dark theme UI
  - Responsive design
  - No build step required
  - Cache disabled for development

### LLM Service (Ollama)
- **Image**: ollama/ollama:latest
- **Model**: Llama 3.1 8B
- **Port**: 11434
- **Features**:
  - Persistent model storage via Docker volume
  - Health check ensures availability
  - Backend depends on LLM service
  - Pull models with: `docker exec -it web-agent-ollama ollama pull <model>`

### Docker Networking
- Custom bridge network: `web-agent-network`
- Services can communicate using service names
- Frontend can reach backend at `http://backend:8000`
- Backend can reach Ollama at `http://llm:11434`

## 📝 API Endpoints

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with API info |
| `GET` | `/api/health` | Health check endpoint |
| `GET` | `/docs` | Interactive API documentation (Swagger) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

## 🔒 Environment Variables Best Practices

- ✅ **DO**: Keep `.env` file in `.gitignore`
- ✅ **DO**: Use `.env.example` as a template
- ✅ **DO**: Document all environment variables
- ❌ **DON'T**: Commit `.env` files to version control
- ❌ **DON'T**: Store secrets in Dockerfiles

## 🐛 Troubleshooting

### Port Already in Use

If ports 8000 or 8080 are already in use:

```bash
# Check what's using the port (macOS/Linux)
lsof -i :8000
lsof -i :8080

# Kill the process or change ports in docker-compose.yml
# Example: Change "8000:8000" to "8001:8000"
```

### Container Won't Start

```bash
# Check logs for errors
docker compose logs backend
docker compose logs frontend

# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up
```

### Backend Not Reloading

```bash
# Ensure volume is mounted correctly
docker compose down
docker compose up --build

# Check if changes are visible in container
docker compose exec backend ls -la /app/app
```

### CORS Errors

Check your `.env` file and ensure `CORS_ALLOW_ORIGINS` includes your frontend URL:
```bash
CORS_ALLOW_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

### Ollama Model Issues

```bash
# Check if model is downloaded
docker exec -it web-agent-ollama ollama list

# Check Ollama logs
docker compose logs llm

# Re-pull the model
docker exec -it web-agent-ollama ollama pull llama3.1:8b

# Test Ollama directly
curl http://localhost:11434/api/version
```

## 🛠️ Development Helper Script

A convenient helper script (`dev.sh`) is provided for common tasks:

```bash
# View all commands
./dev.sh help

# Common operations
./dev.sh start      # Start all services
./dev.sh stop       # Stop all services
./dev.sh logs       # View logs (all services)
./dev.sh logs-be    # View backend logs only
./dev.sh logs-fe    # View frontend logs only
./dev.sh restart    # Restart services
./dev.sh rebuild    # Full rebuild
./dev.sh test       # Test endpoints
./dev.sh status     # Container status
./dev.sh clean      # Clean up containers & volumes
./dev.sh shell-be   # Backend container shell
./dev.sh shell-fe   # Frontend container shell
```

## 🚧 Next Steps

This is a blank starter template. To add the chat functionality:

1. **Backend**: Add chat endpoints in `backend/app/main.py`
2. **Frontend**: Implement chat UI in `frontend/index.html`
3. **Styling**: Enhance the design in `frontend/styles.css`
4. **Logic**: Add chat logic in `frontend/app.js`

## 📖 Documentation

- **Getting Started**: [GETTING_STARTED.md](./GETTING_STARTED.md) - Complete setup guide
- **This File**: Overview and reference

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## 📄 License

This project is for development purposes.

---

**Happy Coding! 🎉**
