#!/bin/bash

echo "========================================"
echo "Agent Swarm Web Dashboard Launcher"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python from https://python.org"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

echo "Installing backend dependencies..."
pip3 install -r requirements.txt

echo
echo "Installing frontend dependencies..."
cd dashboard
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

echo
echo "Starting services..."
echo

# Start backend server in background
python3 web_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend server in background
cd dashboard && npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

echo
echo "========================================"
echo "✅ Dashboard is running!"
echo "========================================"
echo
echo "Access points:"
echo "  📊 Dashboard: http://localhost:5173"
echo "  📡 API Docs:  http://localhost:8000/docs"
echo "  🔌 WebSocket: ws://localhost:8000/ws"
echo

# Open browser (works on Mac and most Linux distros)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5173
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:5173 2>/dev/null || echo "Please open http://localhost:5173 in your browser"
fi

echo
echo "Press Ctrl+C to stop all services..."

# Function to cleanup on exit
cleanup() {
    echo
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Services stopped."
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Wait indefinitely
while true; do
    sleep 1
done