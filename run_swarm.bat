@echo off
echo ======================================================================
echo QUICKSHOP MVP - AGENT SWARM ORCHESTRATION
echo ======================================================================
echo.
echo Starting 15-agent swarm with MCP integrations...
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

REM Clear the log file first
del orchestrate_bypass.log 2>nul

REM Run the orchestrator
python fix_specific_tools.py

REM Show the results from the log
echo.
echo ======================================================================
echo AGENT EXECUTION LOG:
echo ======================================================================
type orchestrate_bypass.log | more

echo.
echo ======================================================================
echo Check projects\quickshop-mvp-test6 for generated application
echo ======================================================================
pause