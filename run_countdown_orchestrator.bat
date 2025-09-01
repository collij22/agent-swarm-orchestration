@echo off
set MOCK_MODE=true
echo Starting Countdown Game Development with Agent Swarm...
echo ============================================
python orchestrate_enhanced.py --project-type full_stack_api --requirements countdown_requirements.yaml --human-log --summary-level detailed --max-parallel 3 --output-dir countdown_game
echo ============================================
echo Orchestration complete.
pause