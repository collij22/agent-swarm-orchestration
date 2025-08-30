@echo off
echo ========================================
echo Starting DevPortfolio Project Execution
echo ========================================
echo.

REM Create timestamp for unique folder
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,8%_%dt:~8,6%"

REM Set project name
set "project_name=DevPortfolio"

REM Create output directory path
set "output_dir=projects\%project_name%_%timestamp%"

echo Project will be created in: %output_dir%
echo.

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo WARNING: ANTHROPIC_API_KEY not set. Will run in mock mode.
    echo To use real API, set: set ANTHROPIC_API_KEY=your-key-here
    echo.
)

echo Starting agent swarm execution...
echo ========================================
echo.

REM Run the orchestrator with all fixes applied
python orchestrate_enhanced.py ^
    --project-type=full_stack_api ^
    --requirements=requirements_devportfolio.yaml ^
    --output-dir="%output_dir%" ^
    --progress ^
    --max-parallel=2 ^
    --verbose

echo.
echo ========================================
if %errorlevel% equ 0 (
    echo SUCCESS: Project generated in %output_dir%
    echo.
    echo You can find your project files at:
    echo   %cd%\%output_dir%
) else (
    echo ERROR: Execution failed. Check the logs above for details.
)
echo ========================================

pause