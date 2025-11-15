#!/bin/bash

# Web Agent Development Script
# Provides convenient commands for managing the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if .env exists
check_env() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_info "Copying env.template to .env..."
        cp env.template .env
        print_warning "Please edit .env and add your OPENROUTER_API_KEY and other secrets"
        print_info "Generate secrets with: openssl rand -hex 32"
        exit 1
    fi
}

# Command functions
cmd_start() {
    print_header "Starting Web Agent Services"
    check_env
    docker-compose -f dev.yaml up -d
    print_success "Services started"
    print_info "LibreChat: http://localhost:3080"
    print_info "Backend API: http://localhost:8000"
    print_info "Backend Docs: http://localhost:8000/docs"
    print_info "MCP Server: http://localhost:8001"
}

cmd_stop() {
    print_header "Stopping Web Agent Services"
    docker-compose -f dev.yaml down
    print_success "Services stopped"
}

cmd_restart() {
    print_header "Restarting Web Agent Services"
    docker-compose -f dev.yaml restart
    print_success "Services restarted"
}

cmd_rebuild() {
    print_header "Rebuilding and Restarting Services"
    docker-compose -f dev.yaml down
    docker-compose -f dev.yaml up --build -d
    print_success "Services rebuilt and started"
}

cmd_logs() {
    if [ -z "$1" ]; then
        print_header "Showing All Logs (Ctrl+C to exit)"
        docker-compose -f dev.yaml logs -f
    else
        print_header "Showing Logs for: $1"
        docker-compose -f dev.yaml logs -f "$1"
    fi
}

cmd_status() {
    print_header "Service Status"
    docker-compose -f dev.yaml ps
    echo ""
    print_info "Checking service health..."
    echo ""
    
    # Check backend health
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        print_success "Backend is healthy"
    else
        print_error "Backend is not responding"
    fi
    
    # Check services health
    if curl -s http://localhost:8000/api/services/health > /dev/null 2>&1; then
        echo ""
        print_info "Detailed service health:"
        curl -s http://localhost:8000/api/services/health | python3 -m json.tool
    fi
}

cmd_clean() {
    print_header "Cleaning Up"
    print_warning "This will remove all containers, volumes, and images"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f dev.yaml down -v --rmi all
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

cmd_reset_db() {
    print_header "Resetting Database"
    print_warning "This will delete all user data and conversations"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f dev.yaml down mongodb
        docker volume rm web-agent_mongodb-data 2>/dev/null || true
        docker-compose -f dev.yaml up -d mongodb
        print_success "Database reset complete"
        print_info "Waiting for MongoDB to initialize..."
        sleep 5
        docker-compose -f dev.yaml restart librechat
        print_success "LibreChat restarted"
    else
        print_info "Reset cancelled"
    fi
}

cmd_shell() {
    service=${1:-backend}
    print_header "Opening shell in: $service"
    docker-compose -f dev.yaml exec "$service" /bin/sh
}

cmd_health() {
    print_header "Health Check"
    
    echo "Backend:"
    curl -s http://localhost:8000/api/health | python3 -m json.tool || print_error "Backend not responding"
    
    echo ""
    echo "All Services:"
    curl -s http://localhost:8000/api/services/health | python3 -m json.tool || print_error "Cannot get services health"
    
    echo ""
    echo "MCP Tools:"
    curl -s http://localhost:8000/api/mcp/tools | python3 -m json.tool || print_error "Cannot get MCP tools"
}

cmd_test_mcp() {
    print_header "Testing MCP Tool: get_current_time"
    curl -X POST http://localhost:8000/api/mcp/tools/call \
        -H "Content-Type: application/json" \
        -d '{"tool_name": "get_current_time", "arguments": {}}' | python3 -m json.tool
}

cmd_setup() {
    print_header "Initial Setup"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker Desktop."
        exit 1
    fi
    print_success "Docker found"
    
    # Check .env
    if [ ! -f .env ]; then
        print_info "Creating .env from template..."
        cp env.template .env
        print_warning "Please edit .env and add your secrets:"
        print_info "  - OPENROUTER_API_KEY (get from https://openrouter.ai/keys)"
        print_info "  - JWT_SECRET (generate with: openssl rand -hex 32)"
        print_info "  - JWT_REFRESH_SECRET (generate with: openssl rand -hex 32)"
        exit 0
    fi
    print_success ".env file exists"
    
    # Check for API key
    if grep -q "your_openrouter_api_key_here" .env; then
        print_error "Please set your OPENROUTER_API_KEY in .env"
        exit 1
    fi
    print_success "OPENROUTER_API_KEY is set"
    
    # Start services
    print_info "Starting services..."
    cmd_start
    
    print_success "Setup complete!"
    print_info "Access LibreChat at: http://localhost:3080"
}

cmd_help() {
    cat << EOF
Web Agent Development Script

Usage: ./dev.sh [command] [options]

Commands:
    setup           Initial setup (create .env and start services)
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    rebuild         Rebuild and restart all services
    logs [service]  Show logs (all or specific service)
    status          Show service status and health
    health          Detailed health check of all services
    shell [service] Open shell in service container (default: backend)
    clean           Remove all containers, volumes, and images
    reset-db        Reset MongoDB database
    test-mcp        Test MCP server with a simple tool call
    help            Show this help message

Services:
    librechat       LibreChat frontend (port 3080)
    backend         Backend API (port 8000)
    mcp-server      MCP tool server (port 8001)
    mongodb         MongoDB database (port 27017)

Examples:
    ./dev.sh start              # Start all services
    ./dev.sh logs backend       # Show backend logs
    ./dev.sh shell mcp-server   # Open shell in MCP server
    ./dev.sh health             # Check all services health
    ./dev.sh test-mcp           # Test MCP server

EOF
}

# Main command dispatcher
case "$1" in
    setup)
        cmd_setup
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    rebuild)
        cmd_rebuild
        ;;
    logs)
        cmd_logs "$2"
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    clean)
        cmd_clean
        ;;
    reset-db)
        cmd_reset_db
        ;;
    shell)
        cmd_shell "$2"
        ;;
    test-mcp)
        cmd_test_mcp
        ;;
    help|--help|-h|"")
        cmd_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
