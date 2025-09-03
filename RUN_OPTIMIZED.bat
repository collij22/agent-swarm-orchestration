@echo off
cls
echo ================================================================================
echo                 OPTIMIZED INTELLIGENT ORCHESTRATOR v4.0
echo            Complete Fix with Enhanced Communication Flow
echo ================================================================================
echo.
echo CRITICAL FIXES APPLIED:
echo   [OK] Fixed agent_runtime.py line 825 - handles both strings and dicts
echo   [OK] Orchestrator uses strings for completed_tasks (API compatibility)
echo   [OK] Enhanced communication hub for agent data sharing
echo   [OK] Accurate file tracking with before/after comparison
echo   [OK] Artifact sharing between dependent agents
echo   [OK] Improved retry mechanism with context
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
echo This orchestrator features:
echo   - Fixed completed_tasks handling (no more type errors!)
echo   - CommunicationHub for structured agent communication
echo   - FileTracker for accurate file counting
echo   - Artifact sharing (database schema, API endpoints)
echo   - Enhanced prompts with dependency context
echo.
echo Execution Pattern:
echo   1. requirements-analyst (solo)
echo   2. project-architect (solo) - NOW FIXED!
echo   3. [PARALLEL] database-expert, rapid-builder, frontend-specialist
echo   4. api-integrator (solo)
echo   5. [PARALLEL] devops-engineer, quality-guardian
echo.
echo Press any key to start...
pause >nul

echo.
echo ================================================================================
echo Starting Optimized Orchestration...
echo ================================================================================

python OPTIMIZED_ORCHESTRATOR.py

echo.
echo ================================================================================
echo Orchestration Complete!
echo ================================================================================
echo.
echo Check the following for results:
echo   - Output: projects\quickshop-mvp-optimized\
echo   - Logs: sessions\session_*.json
echo   - Context: projects\quickshop-mvp-optimized\final_context.json
echo   - Checkpoint: projects\quickshop-mvp-optimized\checkpoint.json
echo.
echo Key Improvements:
echo   - All agents should complete successfully
echo   - Files properly tracked and counted
echo   - Communication flow optimized
echo.
pause