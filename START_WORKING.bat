@echo off
echo ======================================================================
echo QUICKSHOP MVP ORCHESTRATION - WORKING VERSION
echo ======================================================================
echo.
echo This will run the agent swarm. The agents ARE working even if you
echo don't see their output immediately. Check the projects\quickshop-mvp-test6
echo directory for generated files.
echo.
echo ======================================================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
set PYTHONDONTWRITEBYTECODE=1

echo Starting orchestration (this may take 10-30 minutes)...
echo.
echo You may see HTTP requests but not agent messages - this is a known issue.
echo The agents ARE working in the background.
echo.

REM Use the version with working tool fixes
python fix_specific_tools.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo SUCCESS! Check projects\quickshop-mvp-test6 for your application
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo FAILED - Check orchestrate_bypass.log for details
    echo ======================================================================
)

pause