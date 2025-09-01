@echo off
echo Please enter your Anthropic API key (or press Enter to use existing):
set /p API_KEY=API Key: 

if not "%API_KEY%"=="" (
    set ANTHROPIC_API_KEY=%API_KEY%
    echo API key set.
) else (
    echo Using existing ANTHROPIC_API_KEY if set.
)

echo.
echo Starting Countdown Game Development with Agent Swarm...
echo ============================================
python orchestrate_enhanced.py --project-type full_stack_api --requirements countdown_requirements.yaml --human-log --summary-level detailed --max-parallel 3 --output-dir countdown_game --verbose
echo ============================================
echo Orchestration complete.
pause