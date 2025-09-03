@echo off
cls
echo ================================================================================
echo                    JSON FILE CREATION FIX TEST
echo             Targeted Solution for JSON Content Issues
echo ================================================================================
echo.
echo PROBLEM IDENTIFIED:
echo   - Agents successfully create .md files with content
echo   - Agents fail to include content for .json files
echo   - Issue: JSON inside JSON parameters confuses the agent
echo.
echo SOLUTION:
echo   1. Explicit examples showing JSON must be passed as STRING
echo   2. Enhanced write_file tool that auto-converts JSON objects
echo   3. Clear instructions for JSON file creation
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
echo This test will:
echo   - Create both .md and .json files
echo   - Use special prompts for JSON files
echo   - Validate that JSON files contain valid JSON
echo.
echo Output will be in: projects\quickshop-mvp-json-fix\
echo.
echo Press any key to start the JSON fix test...
pause >nul

echo.
echo ================================================================================
echo Running JSON Fix Test...
echo ================================================================================
echo.

python FIX_JSON_ISSUE.py

echo.
echo ================================================================================
echo TEST COMPLETE
echo ================================================================================
echo.
echo Check the results above to see if JSON files were created successfully.
echo.
echo Files to check:
echo   - projects\quickshop-mvp-json-fix\API_SPEC.md
echo   - projects\quickshop-mvp-json-fix\DATABASE_SCHEMA.json
echo   - projects\quickshop-mvp-json-fix\CONFIG.json
echo   - projects\quickshop-mvp-json-fix\json_fix_report.json
echo.
pause