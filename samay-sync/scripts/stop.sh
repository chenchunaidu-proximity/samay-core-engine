#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${RED}🛑 Stopping ActivityWatch dev services...${NC}"

# Kill ActivityWatch processes gracefully
pkill -f aw-server
pkill -f aw-watcher-afk
pkill -f aw-watcher-window

sleep 1

# Check if any ActivityWatch processes are still alive
PIDS=$(ps aux | grep -E "aw_server|aw-watcher-afk|aw-watcher-window" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
  echo -e "${GREEN}✅ ActivityWatch processes stopped.${NC}"
else
  echo -e "${YELLOW}⚠️  Still running, force killing: $PIDS${NC}"
  kill -9 $PIDS
  echo -e "${GREEN}✅ ActivityWatch processes force stopped.${NC}"
fi

# Check if port 5600 is still in use
PORT=5600
PID_ON_PORT=$(lsof -ti tcp:$PORT)

if [ -n "$PID_ON_PORT" ]; then
  echo -e "${YELLOW}⚠️ Port $PORT is still in use by PID(s): $PID_ON_PORT${NC}"
  kill -9 $PID_ON_PORT
  echo -e "${GREEN}✅ Freed port $PORT${NC}"
else
  echo -e "${GREEN}✅ Port $PORT is free.${NC}"
fi

# Remove venv from project root folder (go up two directories from samay-sync/scripts/)
VENV_PATH="$(dirname "$0")/../../venv"

if [ -d "$VENV_PATH" ]; then
  echo -e "${YELLOW}⚠️  Removing existing virtual environment ($VENV_PATH)...${NC}"
  rm -rf "$VENV_PATH"
  echo -e "${GREEN}✅ venv folder deleted.${NC}"
else
  echo -e "${GREEN}✅ No venv folder found.${NC}"
fi

echo -e "${BOLD}${GREEN}🎉 All cleanup done.${NC}"
