@echo off
cls
echo ================================================================================
echo           FINAL OPTIMIZED INTELLIGENT ORCHESTRATOR v5.0
echo            Complete Fix with File Creation Verification
echo ================================================================================
echo.
echo CRITICAL FIXES APPLIED:
echo   [OK] Fixed agent_runtime.py line 825 type error
echo   [OK] Fixed project_directory in context.artifacts
echo   [OK] Enhanced file tracking with verification
echo   [OK] Tool call logging for debugging
echo   [OK] File creation emphasis in prompts
echo   [OK] Multiple directory fallbacks for safety
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
echo   - Files are ACTUALLY created on disk
echo   - project_directory is properly set in context
echo   - File paths are handled correctly
echo   - Each agent creates real implementation files
echo   - File verification after each agent
echo.
echo Output will be in: projects\quickshop-mvp-final\
echo.
echo Press any key to start...
pause >nul

echo.
echo ================================================================================
echo Starting Final Optimized Orchestration...
echo ================================================================================

python FINAL_OPTIMIZED_ORCHESTRATOR.py

echo.
echo ================================================================================
echo Orchestration Complete!
echo ================================================================================
echo.
echo Check the following:
echo   1. Output files: projects\quickshop-mvp-final\
echo   2. Logs: Check console output for file creation
echo   3. Context: projects\quickshop-mvp-final\final_context.json
echo.
echo The final_context.json file will list ALL created files.
echo.
pause