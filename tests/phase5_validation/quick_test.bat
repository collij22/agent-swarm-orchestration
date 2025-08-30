@echo off
REM Phase 5 Validation Quick Test Script for Windows
REM Runs all tests and generates analysis report

echo ========================================
echo Phase 5 Validation Test Suite
echo ========================================
echo.

REM Check Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Create directories if they don't exist
if not exist "results" mkdir results
if not exist "reports" mkdir reports

REM Run all tests
echo Running all 5 test scenarios...
echo ----------------------------------------
python run_tests.py --all --verbose

if %errorlevel% neq 0 (
    echo.
    echo Error: Test execution failed
    exit /b 1
)

echo.
echo ========================================
echo Analyzing test results...
echo ========================================
python analyze_results.py --summary --format all

echo.
echo ========================================
echo Test execution complete!
echo ========================================
echo.
echo Results saved in: results\
echo Reports saved in: reports\
echo.

REM Open the latest HTML report if it exists
for /f "delims=" %%i in ('dir /b /od reports\analysis_report_*.html 2^>nul') do set "latest_report=%%i"
if defined latest_report (
    echo Opening HTML report...
    start "" "reports\%latest_report%"
)

pause