@echo off
cls
echo ================================================================================
echo              ULTRA-INTELLIGENT ORCHESTRATOR v3.0
echo           Complete Solution with Enhanced Communication
echo ================================================================================
echo.
echo FIXES APPLIED:
echo   [OK] Context serialization fixed - no more dict/string errors
echo   [OK] Inter-agent communication improved with structured data
echo   [OK] File counting accurate with before/after tracking
echo   [OK] Retry mechanism for failed agents (max 2 attempts)
echo   [OK] Enhanced error recovery and progress tracking
echo   [OK] Checkpoint saving every 2 completed agents
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
echo This orchestrator will:
echo   1. Run requirements-analyst alone
echo   2. Run project-architect alone (with fixed context)
echo   3. Run database-expert, rapid-builder, frontend-specialist in PARALLEL
echo   4. Run api-integrator alone (needs backend + frontend)
echo   5. Run devops-engineer and quality-guardian in PARALLEL
echo.
echo Enhanced Features:
echo   - Automatic retry for failed agents (up to 2 attempts)
echo   - Checkpoint saving for recovery
echo   - Accurate file tracking
echo   - Improved agent communication
echo.
echo Press any key to start...
pause >nul

echo.
echo ================================================================================
echo Starting Ultra-Intelligent Orchestration...
echo ================================================================================

python INTELLIGENT_ORCHESTRATOR_ULTRA_FIXED.py

echo.
echo ================================================================================
echo Orchestration Complete!
echo ================================================================================
echo.
echo Check the following for results:
echo   - Output: projects\quickshop-mvp-intelligent\
echo   - Logs: sessions\session_*.json
echo   - Context: projects\quickshop-mvp-intelligent\final_context.json
echo   - Checkpoint: projects\quickshop-mvp-intelligent\checkpoint.json
echo.
pause