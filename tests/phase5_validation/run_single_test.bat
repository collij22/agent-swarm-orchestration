@echo off
REM Run a single test scenario

if "%1"=="" (
    echo Usage: run_single_test.bat [test_name]
    echo.
    echo Available tests:
    echo   ecommerce    - E-Commerce Platform MVP
    echo   analytics    - Real-Time Analytics Dashboard
    echo   microservices - Microservices Migration
    echo   mobile       - Mobile-First Social App
    echo   ai_cms       - AI-Powered Content Management
    exit /b 1
)

echo Running test: %1
python run_tests.py --test %1 --verbose

if %errorlevel% equ 0 (
    echo.
    echo Test completed successfully!
    echo Analyzing results...
    python analyze_results.py --summary
)

pause