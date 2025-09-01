@echo off
echo Starting MCP Servers for Agent Swarm...
echo ========================================

REM Kill any existing MCP server processes first
echo Cleaning up any existing MCP servers...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq MCP*" 2>nul

echo.
echo Starting Semgrep MCP Server (Port 3101)...
start "MCP Semgrep Server" /min cmd /c "npx @anthropic/mcp-server-semgrep --port 3101"
timeout /t 2 /nobreak >nul

echo Starting Ref MCP Server (Port 3102)...
start "MCP Ref Server" /min cmd /c "npx @anthropic/mcp-server-ref --port 3102"
timeout /t 2 /nobreak >nul

echo Starting Playwright MCP Server (Port 3103)...
start "MCP Playwright Server" /min cmd /c "npx @agentdeskai/playwright-mcp --port 3103"
timeout /t 2 /nobreak >nul

echo.
echo Verifying servers are running...
timeout /t 3 /nobreak >nul

REM Check if servers are responding
echo.
echo Checking server health...
curl -s http://localhost:3101/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Semgrep MCP Server is running on port 3101
) else (
    echo [WARNING] Semgrep MCP Server may not be running properly
)

curl -s http://localhost:3102/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ref MCP Server is running on port 3102
) else (
    echo [WARNING] Ref MCP Server may not be running properly
)

curl -s http://localhost:3103/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Playwright MCP Server is running on port 3103
) else (
    echo [WARNING] Playwright MCP Server may not be running properly
)

echo.
echo ========================================
echo MCP Servers started. They will run in the background.
echo To stop them, close the command windows or run: taskkill /F /IM node.exe
echo.
echo You can now run: python orchestrate_enhanced.py
echo ========================================
pause