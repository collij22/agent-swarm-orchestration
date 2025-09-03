@echo off
cls
echo ================================================================================
echo                    COMPLETE FIX TEST - Both Issues Solved
echo ================================================================================
echo.
echo This test demonstrates fixes for BOTH issues:
echo   1. Missing content parameter in write_file calls
echo   2. Agent saying it will create files but not actually doing it
echo.
echo WHAT IT DOES:
echo   - Intercepts write_file calls to fix missing content
echo   - Detects files mentioned in agent output
echo   - Auto-creates files the agent mentioned but didn't create
echo   - Generates appropriate content based on file type
echo   - Creates a detailed report of all interventions
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
echo Expected behavior:
echo   - Agent will be asked to create 3 specific files
echo   - If agent only talks about creating them, we'll create them
echo   - If agent forgets content, we'll add it
echo   - All 3 files will exist at the end
echo.
echo Output will be in: projects\quickshop-mvp-complete-fix\
echo.
echo Press any key to start the complete fix test...
pause >nul

echo.
echo ================================================================================
echo Running Complete Fix Test...
echo ================================================================================
echo.

python COMPLETE_FIX.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo TEST COMPLETED SUCCESSFULLY
    echo ================================================================================
    echo.
    echo Check the results:
    echo   - Output files: projects\quickshop-mvp-complete-fix\
    echo   - Fix report: projects\quickshop-mvp-complete-fix\complete_fix_report.json
    echo.
    echo Expected files (should all exist):
    echo   - API_SPEC.md
    echo   - REQUIREMENTS.md
    echo   - DATABASE_SCHEMA.json
    echo.
    echo The report shows:
    echo   - Which files the agent mentioned
    echo   - Which files the agent actually created
    echo   - Which files we had to auto-create
    echo   - Which files had missing content fixed
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