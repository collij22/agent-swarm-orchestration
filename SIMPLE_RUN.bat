@echo off
echo ======================================================================
echo IMPORTANT: The agent swarm system has Unicode encoding issues
echo that prevent the agents from displaying output properly.
echo.
echo The agents ARE functional but output is hidden.
echo You can monitor progress by checking:
echo   - projects\quickshop-mvp-test6\  (for generated files)
echo   - orchestrate_bypass.log         (for text output)
echo.
echo This will take 10-30 minutes to complete.
echo ======================================================================
echo.

REM Set encoding to UTF-8
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

echo Running agent swarm (output will be minimal)...
echo.

python fix_specific_tools.py

echo.
echo ======================================================================
echo Process complete. Check projects\quickshop-mvp-test6 for results.
echo ======================================================================
pause