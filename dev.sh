#!/bin/bash

# Web Agent Development Helper Script
# This script provides convenient commands for development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
}

# Function to display help
show_help() {
    echo ""
    echo "Web Agent Development Helper"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start        - Start all services (build if needed)"
    echo "  stop         - Stop all services"
    echo "  restart      - Restart all services"
    echo "  rebuild      - Rebuild and restart all services"
    echo "  logs         - Show logs (all services)"
    echo "  logs-be      - Show backend logs only"
    echo "  logs-fe      - Show frontend logs only"
    echo "  status       - Show running containers"
    echo "  test         - Test backend and frontend endpoints"
    echo "  clean        - Stop and remove containers, volumes"
    echo "  shell-be     - Open bash in backend container"
    echo "  shell-fe     - Open shell in frontend container"
    echo "  help         - Show this help message"
    echo ""
}

# Start services
start_services() {
    check_docker
    print_info "Starting services..."
    docker compose up --build -d
    print_success "Services started!"
    print_info "Backend: http://localhost:8000"
    print_info "Frontend: http://localhost:8080"
    print_info "API Docs: http://localhost:8000/docs"
}

# Stop services
stop_services() {
    print_info "Stopping services..."
    docker compose down
    print_success "Services stopped!"
}

# Restart services
restart_services() {
    print_info "Restarting services..."
    docker compose restart
    print_success "Services restarted!"
}

# Rebuild services
rebuild_services() {
    check_docker
    print_info "Rebuilding services..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    print_success "Services rebuilt and started!"
}

# Show logs
show_logs() {
    print_info "Showing logs (Ctrl+C to exit)..."
    docker compose logs -f
}

# Show backend logs
show_logs_backend() {
    print_info "Showing backend logs (Ctrl+C to exit)..."
    docker compose logs -f backend
}

# Show frontend logs
show_logs_frontend() {
    print_info "Showing frontend logs (Ctrl+C to exit)..."
    docker compose logs -f frontend
}

# Show status
show_status() {
    print_info "Container status:"
    docker compose ps
    echo ""
    print_info "Resource usage:"
    docker stats --no-stream web-agent-backend web-agent-frontend 2>/dev/null || print_warning "Containers not running"
}

# Test endpoints
test_endpoints() {
    print_info "Testing endpoints..."
    echo ""
    
    # Test backend health
    print_info "Testing backend health endpoint..."
    if curl -s -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_success "Backend health: OK"
        curl -s http://localhost:8000/api/health | python3 -m json.tool
    else
        print_error "Backend health: FAILED"
    fi
    echo ""
    
    # Test backend root
    print_info "Testing backend root endpoint..."
    if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
        print_success "Backend root: OK"
        curl -s http://localhost:8000/ | python3 -m json.tool
    else
        print_error "Backend root: FAILED"
    fi
    echo ""
    
    # Test frontend
    print_info "Testing frontend..."
    if curl -s -f http://localhost:8080/ > /dev/null 2>&1; then
        print_success "Frontend: OK (http://localhost:8080)"
    else
        print_error "Frontend: FAILED"
    fi
    echo ""
}

# Clean up
clean_up() {
    print_warning "This will stop and remove all containers and volumes."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker compose down -v
        print_success "Cleanup complete!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Open backend shell
backend_shell() {
    print_info "Opening backend shell..."
    docker compose exec backend bash
}

# Open frontend shell
frontend_shell() {
    print_info "Opening frontend shell..."
    docker compose exec frontend sh
}

# Main script logic
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    rebuild)
        rebuild_services
        ;;
    logs)
        show_logs
        ;;
    logs-be)
        show_logs_backend
        ;;
    logs-fe)
        show_logs_frontend
        ;;
    status)
        show_status
        ;;
    test)
        test_endpoints
        ;;
    clean)
        clean_up
        ;;
    shell-be)
        backend_shell
        ;;
    shell-fe)
        frontend_shell
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: ${1}"
        show_help
        exit 1
        ;;
esac

