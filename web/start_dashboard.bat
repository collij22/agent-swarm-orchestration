@echo off
echo ========================================
echo Agent Swarm Web Dashboard Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo Installing backend dependencies...
pip install -r requirements.txt

echo.
echo Installing frontend dependencies...
cd dashboard
if not exist node_modules (
    npm install
)
cd ..

echo.
echo Starting services...
echo.

REM Start backend server in new window
start "Agent Swarm Backend" cmd /k python web_server.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server in new window
start "Agent Swarm Frontend" cmd /k "cd dashboard && npm run dev"

REM Wait for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Dashboard is running!
echo ========================================
echo.
echo Access points:
echo   Dashboard: http://localhost:5173
echo   API Docs:  http://localhost:8000/docs
echo   WebSocket: ws://localhost:8000/ws
echo.
echo Opening dashboard in browser...
start http://localhost:5173

echo.
echo Press any key to stop all services...
pause >nul

REM Kill the services
taskkill /FI "WindowTitle eq Agent Swarm Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Agent Swarm Frontend*" /T /F >nul 2>&1

echo Services stopped.
pause