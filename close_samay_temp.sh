#!/bin/bash

# Quick temporary script to close Samay
echo "🛑 Closing Samay..."

# Find and kill Samay processes
pkill -f "aw-qt" 2>/dev/null
pkill -f "aw-server" 2>/dev/null  
pkill -f "aw-watcher-window" 2>/dev/null

sleep 1

# Check if any are still running and force kill if needed
if pgrep -f "aw-qt\|aw-server\|aw-watcher-window" > /dev/null; then
    echo "⚠️  Force killing remaining processes..."
    pkill -9 -f "aw-qt" 2>/dev/null
    pkill -9 -f "aw-server" 2>/dev/null
    pkill -9 -f "aw-watcher-window" 2>/dev/null
fi

echo "✅ Samay closed!"




