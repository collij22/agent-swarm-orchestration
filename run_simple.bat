@echo off
cd /d "C:\AI projects\1test"
echo Starting simplified orchestration...
set ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY%
set DISABLE_RICH_CONSOLE=1
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

echo.
echo Running with Python 3.13...
"C:\Python313\python.exe" orchestrate_simple.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --max-parallel 2 --human-log --summary-level concise

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Orchestration completed successfully!
) else (
    echo.
    echo Orchestration failed with error code %ERRORLEVEL%
)

pause