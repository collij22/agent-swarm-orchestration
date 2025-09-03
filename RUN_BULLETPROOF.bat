@echo off
cls
echo ================================================================================
echo              BULLETPROOF INTELLIGENT ORCHESTRATOR v6.0
echo         Complete Fix with Infinite Loop Prevention
echo ================================================================================
echo.
echo CRITICAL FIXES APPLIED:
echo   [OK] Fixed import errors - create_standard_tools from agent_runtime
echo   [OK] Fixed infinite loop - proper failed agent tracking
echo   [OK] Fixed async issues - using synchronous execution
echo   [OK] Added maximum iteration safety limit
echo   [OK] Proper error truncation to prevent huge logs
echo   [OK] Sequential execution to avoid race conditions
echo   [OK] Enhanced checkpoint saving with limited history
echo.

REM Check API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo [ERROR] ANTHROPIC_API_KEY not set!
    echo.
    echo Please run: set ANTHROPIC_API_KEY=your-key-here
    echo.
    pause
    exit /b 1
)

echo API Key configured: %ANTHROPIC_API_KEY:~0,20%...
echo.
echo This version ensures:
echo   - No infinite loops (max iterations limit)
echo   - Proper failed agent tracking
echo   - Sequential execution for stability
echo   - Clear error messages
echo   - Checkpoint saving every 2 agents
echo   - Clean output directory on start
echo.
echo Output will be in: projects\quickshop-mvp-bulletproof\
echo.
echo Press any key to start...
pause >nul

echo.
echo ================================================================================
echo Starting Bulletproof Orchestration...
echo ================================================================================

python BULLETPROOF_ORCHESTRATOR.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS - Orchestration Completed Successfully!
    echo ================================================================================
) else if %ERRORLEVEL% EQU 2 (
    echo.
    echo ================================================================================
    echo INTERRUPTED - Orchestration was interrupted by user
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo FAILED - Orchestration encountered errors
    echo ================================================================================
)

echo.
echo Check the following:
echo   1. Output files: projects\quickshop-mvp-bulletproof\
echo   2. Checkpoint: projects\quickshop-mvp-bulletproof\checkpoint.json
echo   3. Final context: projects\quickshop-mvp-bulletproof\final_context.json
echo.
pause