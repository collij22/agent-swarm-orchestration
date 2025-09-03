@echo off
REM Production orchestrator with all fixes and Phase 1-5 enhancements

echo ============================================================
echo QuickShop MVP Orchestration
echo Phase 1-5 Implementation Complete
echo ============================================================
echo.

REM Set encoding
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

REM Disable problematic MCPs that cause API errors
set DISABLE_BRAVE_SEARCH_MCP=true
set SKIP_MCP_BRAVE=true

REM Use Python 3.12 if available, otherwise default Python
where C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Using Python 3.12...
    C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe run_production.py
) else (
    echo Using default Python...
    python run_production.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo Error running orchestration
    echo Falling back to alternative runner...
    echo ============================================================
    python fix_io_and_run.py
)

echo.
echo ============================================================
echo Orchestration Complete
echo ============================================================
pause