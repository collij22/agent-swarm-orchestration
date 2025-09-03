@echo off
echo ============================================================
echo QUICKSHOP MVP ORCHESTRATION
echo ============================================================
echo.
echo This will generate a complete e-commerce application
echo in projects/quickshop-mvp-test6
echo.
echo ============================================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

echo Attempting to run orchestration...
echo.

REM Try the fixed schemas version first
echo [1/4] Trying FIXED SCHEMAS runner (tools fixed)...
python fix_specific_tools.py
if %ERRORLEVEL% EQU 0 goto SUCCESS

echo.
echo [2/4] Trying PROVEN FIX_IO runner...
python fix_io_and_run.py
if %ERRORLEVEL% EQU 0 goto SUCCESS

echo.
echo [3/4] Trying SUBPROCESS RUNNER (avoids I/O conflicts)...
python quickshop_runner.py
if %ERRORLEVEL% EQU 0 goto SUCCESS

echo.
echo [4/4] Trying direct execution with environment vars...
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
python orchestrate_enhanced.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --summary-level concise --max-parallel 2 --human-log
if %ERRORLEVEL% EQU 0 goto SUCCESS

echo.
echo ============================================================
echo ERROR: All runners failed
echo ============================================================
echo.
echo Troubleshooting:
echo 1. Check that ANTHROPIC_API_KEY is set
echo 2. Ensure Python 3.11+ is installed
echo 3. Run: pip install -r requirements.txt
echo 4. Check the error messages above
echo.
pause
exit /b 1

:SUCCESS
echo.
echo ============================================================
echo SUCCESS! QuickShop MVP has been generated!
echo ============================================================
echo.
echo Next steps:
echo   cd projects\quickshop-mvp-test6
echo   docker-compose up
echo.
echo Then open:
echo   http://localhost:3000 (Frontend)
echo   http://localhost:8000 (Backend API)
echo.
pause
exit /b 0