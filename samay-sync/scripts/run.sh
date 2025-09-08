#!/bin/bash

# ===============================
# Samay Dev Setup Script
# ===============================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Root path (go up two directories from samay-sync/scripts/ to project root)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SERVER_URL="http://localhost:5600"

echo -e "${CYAN}${BOLD}--- Samay Dev Setup ---${NC}"
cd "$PROJECT_ROOT" || exit

# Step 1: Virtualenv
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi
source venv/bin/activate

# Step 2: Build all components
echo -e "${CYAN}Running make build (installs all modules)...${NC}"
make build

# Helper to run each service in new Terminal
run_service() {
    local dir=$1
    local module=$2
    echo -e "${CYAN}Launching ${dir} (${module}) in new Terminal...${NC}"
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_ROOT/$dir && poetry run python3 -m $module"
end tell
EOF
}

# Step 3: Launch services
run_service "aw-server" "aw_server"
run_service "aw-watcher-window" "aw_watcher_window"

# Step 4: API info
echo -e "${GREEN}${BOLD}✅ Dev environment started!${NC}"
echo -e "${CYAN}API available at:${NC}"
echo -e "  • Buckets: $SERVER_URL/api/0/buckets"

# Try to fetch bucket IDs and print sample /events endpoints
sleep 2
if command -v curl &> /dev/null; then
    BUCKETS=$(curl -s "$SERVER_URL/api/0/buckets/" | grep -o '"id": "[^"]*"' | cut -d'"' -f4)
    if [ -n "$BUCKETS" ]; then
        echo -e "  • Example Events endpoints:"
        for b in $BUCKETS; do
            echo -e "      - $SERVER_URL/api/0/buckets/$b/events"
        done
        # Add ready-made curl example for the first bucket
        FIRST_BUCKET=$(echo "$BUCKETS" | head -n1)
        echo -e "\n${CYAN}Example: Fetch last 10 events from '$FIRST_BUCKET'${NC}"
        echo -e "${YELLOW}curl \"$SERVER_URL/api/0/buckets/$FIRST_BUCKET/events?limit=10\"${NC}"
    else
        echo -e "  • Events (example): $SERVER_URL/api/0/buckets/<bucket_id>/events"
    fi
else
    echo -e "  • Events (example): $SERVER_URL/api/0/buckets/<bucket_id>/events"
fi

echo -e "${YELLOW}Logs are in separate terminal windows.${NC}"
