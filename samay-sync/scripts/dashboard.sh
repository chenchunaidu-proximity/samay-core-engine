#!/bin/bash
# Samay Sync Dashboard Launcher
# Opens the web dashboard in your default browser

echo "🚀 Starting Samay Sync Web Dashboard..."
echo "======================================"

# Check if dashboard is already running
if curl -s http://localhost:8080/api/status > /dev/null 2>&1; then
    echo "✅ Dashboard is already running!"
    echo "🌐 Opening http://localhost:8080 in your browser..."
    open http://localhost:8080
else
    echo "🔄 Starting dashboard server..."
    
    # Set environment variables
    export SAMAY_OAUTH_CLIENT_ID="demo_client"
    export SAMAY_OAUTH_CLIENT_SECRET="demo_secret"
    
    # Start dashboard in background
    python3 samay-sync/demo/web_dashboard.py &
    DASHBOARD_PID=$!
    
    # Wait for server to start
    echo "⏳ Waiting for server to start..."
    sleep 3
    
    # Check if server started successfully
    if curl -s http://localhost:8080/api/status > /dev/null 2>&1; then
        echo "✅ Dashboard started successfully!"
        echo "🌐 Opening http://localhost:8080 in your browser..."
        open http://localhost:8080
        
        echo ""
        echo "📊 Dashboard Features:"
        echo "   • Real-time module status"
        echo "   • Interactive login/logout"
        echo "   • Database data viewer"
        echo "   • Sync state manager"
        echo "   • Auto-refresh every 5 seconds"
        echo "   • Mobile-friendly interface"
        echo ""
        echo "⏹️  To stop: kill $DASHBOARD_PID"
        echo "🔗 URL: http://localhost:8080"
    else
        echo "❌ Failed to start dashboard"
        kill $DASHBOARD_PID 2>/dev/null
        exit 1
    fi
fi
