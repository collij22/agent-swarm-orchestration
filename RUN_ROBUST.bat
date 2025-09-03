@echo off
cls
echo ================================================================================
echo                    ROBUST ORCHESTRATOR v8.0
echo         Tool Call Interception + Communication Flow Validation
echo ================================================================================
echo.
echo CRITICAL IMPROVEMENTS FROM SESSION b2e1d40b:
echo   [FIX] Tool call interception to fix missing content parameters
echo   [FIX] Auto-content generation when agents forget content
echo   [FIX] Communication flow validation with retry guidance
echo   [FIX] Clearer examples in agent prompts
echo   [FIX] Better error recovery with specific instructions
echo.
echo KEY FEATURES:
echo   - Intercepts and fixes tool calls before they fail
echo   - Auto-generates appropriate content based on file type
echo   - Validates communication flow and provides guidance
echo   - Tracks error patterns and successful patterns
echo   - Triggers automated debugger for persistent issues
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
echo This version fixes the exact issue from session b2e1d40b:
echo   - Agent called write_file without content 6+ times
echo   - Agent kept saying "let me fix that" but repeated mistake
echo   - Root cause: Agent didn't understand both params needed in SAME call
echo.
echo Solution:
echo   - Intercept tool calls and add missing content automatically
echo   - Generate appropriate placeholder based on file extension
echo   - Track which files need proper implementation
echo   - Provide clearer guidance in prompts and retries
echo.
echo Output will be in: projects\quickshop-mvp-robust\
echo.
echo Press any key to start...
pause >nul

echo.
echo ================================================================================
echo Starting Robust Orchestration with Tool Interception...
echo ================================================================================

python ROBUST_ORCHESTRATOR.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS - Orchestration completed successfully!
    echo ================================================================================
    echo.
    echo Check interception statistics in execution_report.json
) else if %ERRORLEVEL% EQU 2 (
    echo.
    echo ================================================================================
    echo INTERRUPTED - User cancelled execution
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo FAILED - Orchestration encountered errors
    echo ================================================================================
)

echo.
echo Check results:
echo   - Output: projects\quickshop-mvp-robust\
echo   - Report: projects\quickshop-mvp-robust\execution_report.json
echo   - Logs: robust_orchestrator.log
echo.
echo The report shows:
echo   - How many tool calls were intercepted and fixed
echo   - Which files had auto-generated content
echo   - Communication flow validation results
echo.
pause