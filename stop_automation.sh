#!/bin/bash

# Claude Desktop Automation with n8n Integration
# Shutdown Script

echo "🛑 Stopping Claude Desktop Automation System..."
echo "=============================================="

# Stop local API servers
if [ -f logs/claude_api.pid ]; then
    CLAUDE_PID=$(cat logs/claude_api.pid)
    if kill -0 $CLAUDE_PID 2>/dev/null; then
        echo "→ Stopping Claude API (PID: $CLAUDE_PID)..."
        kill $CLAUDE_PID
        rm logs/claude_api.pid
    fi
fi

if [ -f logs/dashboard_api.pid ]; then
    DASHBOARD_PID=$(cat logs/dashboard_api.pid)
    if kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo "→ Stopping Dashboard API (PID: $DASHBOARD_PID)..."
        kill $DASHBOARD_PID
        rm logs/dashboard_api.pid
    fi
fi

# Stop n8n
echo "→ Stopping n8n..."
docker-compose down

echo ""
echo "✅ All services stopped!"
echo "=============================================="