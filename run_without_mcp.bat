@echo off
cd /d "C:\AI projects\1test"

echo Setting UTF-8 encoding...
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
chcp 65001 >nul

echo Disabling MCP tools to avoid schema issues...
set DISABLE_MCP_TOOLS=1

echo.
echo Starting QuickShop MVP Orchestration (MCP disabled)...
echo ======================================================
echo.

"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" orchestrate_enhanced.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --summary-level concise --max-parallel 2 --human-log

echo.
echo Orchestration complete!
pause