#!/bin/bash

# Claude Desktop Automation with n8n Integration
# Startup Script

set -e

echo "🚀 Starting Claude Desktop Automation System..."
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use. Please free the port or change the configuration."
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking ports..."
check_port 5001 || exit 1
check_port 5002 || exit 1
check_port 5678 || exit 1
echo "✅ All ports are available"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p n8n_data
mkdir -p shared_workspace

# Start local API servers
echo "🌐 Starting API servers..."

# Start Claude Desktop Automation API
echo "  → Starting Claude Desktop Automation API on port 5001..."
python claude_desktop_api_server.py --port 5001 > logs/claude_api.log 2>&1 &
CLAUDE_API_PID=$!
echo "  ✓ Claude API started (PID: $CLAUDE_API_PID)"

# Start Dashboard API
echo "  → Starting Dashboard API on port 5002..."
python dashboard_api.py --port 5002 > logs/dashboard_api.log 2>&1 &
DASHBOARD_API_PID=$!
echo "  ✓ Dashboard API started (PID: $DASHBOARD_API_PID)"

# Wait for APIs to initialize
echo "⏳ Waiting for APIs to initialize..."
sleep 5

# Check if APIs are responding
echo "🏥 Health checks..."
if curl -s http://localhost:5001/health > /dev/null; then
    echo "  ✓ Claude API is healthy"
else
    echo "  ❌ Claude API failed to start. Check logs/claude_api.log"
    kill $CLAUDE_API_PID $DASHBOARD_API_PID 2>/dev/null
    exit 1
fi

if curl -s http://localhost:5002/health > /dev/null; then
    echo "  ✓ Dashboard API is healthy"
else
    echo "  ❌ Dashboard API failed to start. Check logs/dashboard_api.log"
    kill $CLAUDE_API_PID $DASHBOARD_API_PID 2>/dev/null
    exit 1
fi

# Start n8n with Docker Compose
echo "🐳 Starting n8n with Docker Compose..."
docker-compose up -d

# Wait for n8n to be ready
echo "⏳ Waiting for n8n to initialize..."
sleep 10

# Check n8n health
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ n8n is running"
else
    echo "❌ n8n failed to start. Check docker logs."
    kill $CLAUDE_API_PID $DASHBOARD_API_PID 2>/dev/null
    docker-compose down
    exit 1
fi

# Save PIDs for cleanup
echo $CLAUDE_API_PID > logs/claude_api.pid
echo $DASHBOARD_API_PID > logs/dashboard_api.pid

echo ""
echo "✅ All services started successfully!"
echo "=============================================="
echo "📊 Service URLs:"
echo "  - n8n:           http://localhost:5678"
echo "  - Claude API:    http://localhost:5001"
echo "  - Dashboard API: http://localhost:5002"
echo ""
echo "📝 Logs:"
echo "  - Claude API:    logs/claude_api.log"
echo "  - Dashboard API: logs/dashboard_api.log"
echo "  - n8n:          docker-compose logs n8n"
echo ""
echo "🛑 To stop all services, run: ./stop_automation.sh"
echo ""
echo "📚 Next steps:"
echo "  1. Open n8n at http://localhost:5678"
echo "  2. Import the workflow from n8n_workflows/claude_automation_workflow.json"
echo "  3. Configure your project settings"
echo "  4. Start automating!"
echo ""