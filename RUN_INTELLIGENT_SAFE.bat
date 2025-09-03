@echo off
REM ========================================
REM INTELLIGENT ORCHESTRATOR - Safe Runner
REM ========================================

echo ========================================
echo INTELLIGENT ORCHESTRATOR - Safe Runner
echo With Enhanced Error Handling
echo ========================================
echo.

REM Check for API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo [WARNING] ANTHROPIC_API_KEY not set
    echo.
    echo To set your API key:
    echo   set ANTHROPIC_API_KEY=your-key-here
    echo.
    echo Continuing with test mode...
    echo.
)

REM Run the safe orchestrator
echo Starting Safe Orchestrator...
echo ========================================
python RUN_INTELLIGENT_SAFE.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Orchestrator failed
    echo Check the error messages above
    echo ========================================
) else (
    echo.
    echo ========================================
    echo SUCCESS: Orchestrator completed
    echo ========================================
)

pause