#!/bin/bash

# ===============================
# Samay Dev Setup Script (Optimized)
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
SERVER_URL="http://localhost:5600"
SERVER_TIMEOUT=30
BUILD_TIMEOUT=300

# Logging function
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

# Check if services are already running
check_services_running() {
    local pids=$(ps aux | grep -E "aw_server|aw-watcher-window" | grep -v grep | awk '{print $2}' || true)
    if [ -n "$pids" ]; then
        warning "ActivityWatch services are already running (PIDs: $pids)"
        return 0
    fi
    return 1
}

# Wait for server to be ready
wait_for_server() {
    local max_attempts=$((SERVER_TIMEOUT / 2))
    local attempt=0
    
    log "Waiting for ActivityWatch server to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$SERVER_URL/api/0/buckets/" >/dev/null 2>&1; then
            success "Server is ready!"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
        echo -n "."
    done
    
    error "Server failed to start within ${SERVER_TIMEOUT}s"
    return 1
}

# Optimized service launcher
run_service() {
    local dir=$1
    local module=$2
    local service_name=$3
    
    log "Launching $service_name..."
    
    # Check if directory exists
    if [ ! -d "$PROJECT_ROOT/$dir" ]; then
        error "Directory $dir not found!"
        return 1
    fi
    
    # Launch service in background with proper error handling
    if command -v osascript >/dev/null 2>&1; then
        osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_ROOT/$dir && poetry run python3 -m $module"
end tell
EOF
    else
        warning "osascript not available, running in background..."
        cd "$PROJECT_ROOT/$dir" && poetry run python3 -m "$module" &
    fi
}

# Main execution
main() {
    echo -e "${CYAN}${BOLD}--- Samay Dev Setup (Optimized) ---${NC}"
    cd "$PROJECT_ROOT" || exit 1
    
    # Check if already running
    if check_services_running; then
        warning "Services appear to be running. Use stop.sh first if you want to restart."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Aborted by user"
            exit 0
        fi
    fi
    
    # Step 1: Virtual environment
    if [ ! -d "venv" ]; then
        log "Creating virtual environment..."
        python3 -m venv venv
        success "Virtual environment created"
    else
        log "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Step 2: Build components with timeout (macOS compatible)
    log "Building ActivityWatch components..."
    if make build; then
        success "Build completed successfully"
    else
        error "Build failed"
        exit 1
    fi
    
    # Step 3: Launch services
    run_service "aw-server" "aw_server" "ActivityWatch Server"
    sleep 2  # Give server time to start
    run_service "aw-watcher-window" "aw_watcher_window" "Window Watcher"
    
    # Step 4: Wait for server and show info
    if wait_for_server; then
        success "Dev environment started!"
        echo -e "${CYAN}API available at:${NC}"
        echo -e "  • Buckets: $SERVER_URL/api/0/buckets/"
        
        # Get bucket information
        if command -v curl >/dev/null 2>&1; then
            local buckets
            buckets=$(curl -s "$SERVER_URL/api/0/buckets/" | grep -o '"id": "[^"]*"' | cut -d'"' -f4 || true)
            if [ -n "$buckets" ]; then
                echo -e "  • Active buckets:"
                for bucket in $buckets; do
                    echo -e "      - $bucket"
                done
                local first_bucket
                first_bucket=$(echo "$buckets" | head -n1)
                echo -e "\n${CYAN}Example API call:${NC}"
                echo -e "${YELLOW}curl \"$SERVER_URL/api/0/buckets/$first_bucket/events?limit=10\"${NC}"
            fi
        fi
        
        echo -e "\n${YELLOW}💡 Tips:${NC}"
        echo -e "  • Check logs in separate Terminal windows"
        echo -e "  • Use 'curl $SERVER_URL/api/0/buckets/' to see all buckets"
        echo -e "  • Run './scripts/stop.sh' to stop all services"
    else
        error "Failed to start ActivityWatch server"
        exit 1
    fi
}

# Run main function
main "$@"