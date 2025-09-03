@echo off
cls
echo ================================================================================
echo                 ENFORCE FILE WRITING TEST
echo            Force Agents to Actually Create Files
echo ================================================================================
echo.
echo This test uses strong instructions to force agents to write files.
echo.
echo APPROACH:
echo   1. Give agent EXPLICIT instructions to call write_file
echo   2. Verify which files were actually created
echo   3. Retry with STRONGER instructions if files are missing
echo   4. Up to 3 attempts with escalating severity
echo.
echo WHAT MAKES THIS DIFFERENT:
echo   - Tools are properly registered and available
echo   - Instructions are VERY explicit about calling write_file
echo   - Multiple attempts with increasingly forceful language
echo   - Validation checks for actual file creation (not just mentions)
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
echo Expected Behavior:
echo   - Agent will be told to create 3 specific files
echo   - Strong instructions emphasize CALLING write_file, not just talking
echo   - If files aren't created, retry with even stronger instructions
echo   - Goal: Force agent to actually use the write_file tool
echo.
echo Output will be in: projects\quickshop-mvp-enforced\
echo.
echo Press any key to start the enforcement test...
pause >nul

echo.
echo ================================================================================
echo Running Enforcement Test...
echo ================================================================================
echo.

python ENFORCE_FILE_WRITING.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS - Enforcement Worked!
    echo ================================================================================
    echo.
    echo All required files were created by the agent.
    echo The strong instructions successfully forced the agent to use write_file.
    echo.
    echo Check the files:
    echo   - projects\quickshop-mvp-enforced\API_SPEC.md
    echo   - projects\quickshop-mvp-enforced\REQUIREMENTS.md
    echo   - projects\quickshop-mvp-enforced\DATABASE_SCHEMA.json
) else (
    echo.
    echo ================================================================================
    echo WARNING - Partial Success or Failure
    echo ================================================================================
    echo.
    echo Some files may not have been created even with enforcement.
    echo Check the report for details.
)

echo.
echo Report saved to: projects\quickshop-mvp-enforced\enforcement_report.json
echo.
pause