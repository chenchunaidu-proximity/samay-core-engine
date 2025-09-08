#!/bin/bash

# ===============================
# Samay Dev Stop Script (Optimized)
# ===============================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
PORT=5600
GRACEFUL_TIMEOUT=10
FORCE_TIMEOUT=5

# Logging functions
log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if services are running
check_services_running() {
    local pids=$(ps aux | grep -E "aw_server|aw-watcher-afk|aw-watcher-window" | grep -v grep | awk '{print $2}' || true)
    if [ -n "$pids" ]; then
        echo "$pids"
        return 0
    fi
    return 1
}

# Graceful shutdown
graceful_shutdown() {
    local pids=$1
    log "Attempting graceful shutdown of ActivityWatch services..."
    
    # Send SIGTERM to all processes
    for pid in $pids; do
        if kill -TERM "$pid" 2>/dev/null; then
            log "Sent SIGTERM to PID $pid"
        fi
    done
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt $GRACEFUL_TIMEOUT ]; do
        local remaining_pids
        remaining_pids=$(check_services_running || true)
        if [ -z "$remaining_pids" ]; then
            success "All services stopped gracefully"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    warning "Graceful shutdown timed out, forcing termination..."
    return 1
}

# Force shutdown
force_shutdown() {
    local pids=$1
    log "Force killing ActivityWatch processes..."
    
    for pid in $pids; do
        if kill -9 "$pid" 2>/dev/null; then
            log "Force killed PID $pid"
        fi
    done
    
    # Double-check
    sleep 1
    local remaining_pids
    remaining_pids=$(check_services_running || true)
    if [ -z "$remaining_pids" ]; then
        success "All processes terminated"
    else
        error "Some processes still running: $remaining_pids"
        return 1
    fi
}

# Clean up port
cleanup_port() {
    local port=$1
    log "Checking port $port..."
    
    local pid_on_port
    pid_on_port=$(lsof -ti "tcp:$port" 2>/dev/null || true)
    
    if [ -n "$pid_on_port" ]; then
        warning "Port $port is still in use by PID(s): $pid_on_port"
        log "Killing processes on port $port..."
        kill -9 $pid_on_port 2>/dev/null || true
        sleep 1
        
        # Verify port is free
        if ! lsof -ti "tcp:$port" >/dev/null 2>&1; then
            success "Port $port is now free"
        else
            error "Failed to free port $port"
            return 1
        fi
    else
        success "Port $port is already free"
    fi
}

# Clean up virtual environment
cleanup_venv() {
    log "Checking virtual environment..."
    
    if [ -d "$VENV_PATH" ]; then
        warning "Removing virtual environment: $VENV_PATH"
        if rm -rf "$VENV_PATH"; then
            success "Virtual environment removed"
        else
            error "Failed to remove virtual environment"
            return 1
        fi
    else
        success "No virtual environment found"
    fi
}

# Main execution
main() {
    echo -e "${BOLD}${RED}🛑 Stopping ActivityWatch Services (Optimized)${NC}"
    
    # Check if services are running
    local running_pids
    if running_pids=$(check_services_running); then
        log "Found running ActivityWatch processes: $running_pids"
        
        # Try graceful shutdown first
        if ! graceful_shutdown "$running_pids"; then
            # Force shutdown if graceful failed
            local remaining_pids
            remaining_pids=$(check_services_running || true)
            if [ -n "$remaining_pids" ]; then
                force_shutdown "$remaining_pids"
            fi
        fi
    else
        success "No ActivityWatch services are running"
    fi
    
    # Clean up port
    cleanup_port "$PORT"
    
    # Clean up virtual environment
    cleanup_venv
    
    # Final status
    echo -e "\n${BOLD}${GREEN}🎉 Cleanup completed successfully!${NC}"
    echo -e "${CYAN}Summary:${NC}"
    echo -e "  • ActivityWatch services: ${GREEN}stopped${NC}"
    echo -e "  • Port $PORT: ${GREEN}free${NC}"
    echo -e "  • Virtual environment: ${GREEN}removed${NC}"
    echo -e "\n${YELLOW}💡 Ready for fresh start with run.sh${NC}"
}

# Run main function
main "$@"