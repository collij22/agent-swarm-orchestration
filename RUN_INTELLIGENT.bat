@echo off
REM ========================================
REM INTELLIGENT ORCHESTRATOR - Run Script
REM ========================================

echo ========================================
echo INTELLIGENT ORCHESTRATOR
echo Aggressive Intervention System
echo ========================================
echo.

REM Check for API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY not set
    echo Please set your API key:
    echo   set ANTHROPIC_API_KEY=your-key-here
    exit /b 1
)

echo [OK] API Key configured
echo.

REM Run the intelligent orchestrator
echo Starting Intelligent Orchestrator...
echo ========================================
python INTELLIGENT_ORCHESTRATOR.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Orchestrator failed
    echo ========================================
) else (
    echo.
    echo ========================================
    echo SUCCESS: Orchestrator completed
    echo ========================================
)

pause