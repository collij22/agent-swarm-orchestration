@echo off
cls
echo ================================================================================
echo              TOOL INTERCEPTION TEST - Simple Robust Orchestrator
echo ================================================================================
echo.
echo This test demonstrates the tool interception fix for the missing content issue.
echo.
echo WHAT IT DOES:
echo   1. Intercepts write_file tool calls
echo   2. Detects missing content parameter
echo   3. Auto-generates appropriate placeholder content
echo   4. Tracks which files needed fixing
echo   5. Creates a report of interceptions
echo.

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo [ERROR] ANTHROPIC_API_KEY environment variable is not set!
    echo.
    echo To set your API key, run:
    echo   set ANTHROPIC_API_KEY=your-actual-api-key-here
    echo.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo API Key configured: %ANTHROPIC_API_KEY:~0,20%...
echo.
echo This test will:
echo   - Execute a requirements-analyst agent
echo   - Intercept any write_file calls
echo   - Fix missing content parameters automatically
echo   - Generate a report of what was fixed
echo.
echo Output will be in: projects\quickshop-mvp-simple-robust\
echo.
echo Press any key to start the test...
pause >nul

echo.
echo ================================================================================
echo Running Tool Interception Test...
echo ================================================================================
echo.

python SIMPLE_ROBUST.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo TEST COMPLETED SUCCESSFULLY
    echo ================================================================================
    echo.
    echo Check the results:
    echo   - Output files: projects\quickshop-mvp-simple-robust\
    echo   - Interception report: projects\quickshop-mvp-simple-robust\interception_report.json
    echo.
    echo The report shows which tool calls were intercepted and fixed.
) else (
    echo.
    echo ================================================================================
    echo TEST FAILED
    echo ================================================================================
    echo.
    echo Please check the error messages above.
)

echo.
pause