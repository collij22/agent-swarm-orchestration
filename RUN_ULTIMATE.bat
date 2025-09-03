@echo off
cls
echo ================================================================================
echo               ULTIMATE INTELLIGENT ORCHESTRATOR v7.0
echo         Enhanced Prompts, Better Error Handling, Content Validation
echo ================================================================================
echo.
echo CRITICAL IMPROVEMENTS:
echo   [NEW] Enhanced write_file tool with content validation
echo   [NEW] Clear agent prompts emphasizing content requirements
echo   [NEW] Retry logic for placeholder files
echo   [NEW] File content verification (not just existence)
echo   [NEW] Better error messages and recovery
echo   [NEW] Error pattern tracking
echo.

REM Check API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo [ERROR] ANTHROPIC_API_KEY not set!
    echo.
    echo Please run: set ANTHROPIC_API_KEY=your-key-here
    echo.
    pause
    exit /b 1
)

echo API Key configured: %ANTHROPIC_API_KEY:~0,20%...
echo.
echo This version fixes the critical issue from session 3f5898b5:
echo   - Agents not providing content parameter in write_file calls
echo   - Placeholder files being created instead of real code
echo   - Agent getting stuck in retry loops
echo.
echo Key Features:
echo   - Enhanced prompts with clear examples
echo   - Content validation for created files  
echo   - Automatic retry if placeholder detected
echo   - Error pattern tracking
echo   - Better agent guidance
echo.
echo Output will be in: projects\quickshop-mvp-ultimate\
echo.
echo Press any key to start...
pause >nul

echo.
echo ================================================================================
echo Starting Ultimate Orchestration...
echo ================================================================================

python ULTIMATE_ORCHESTRATOR.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS - All agents completed successfully!
    echo ================================================================================
) else if %ERRORLEVEL% EQU 2 (
    echo.
    echo ================================================================================
    echo INTERRUPTED - User cancelled execution
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo FAILED - Some agents encountered errors
    echo ================================================================================
)

echo.
echo Check results:
echo   - Valid files: projects\quickshop-mvp-ultimate\
echo   - Context: projects\quickshop-mvp-ultimate\final_context.json
echo   - Checkpoint: projects\quickshop-mvp-ultimate\checkpoint.json
echo.
echo The final_context.json shows which files have valid content vs placeholders.
echo.
pause