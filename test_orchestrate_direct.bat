@echo off
set ANTHROPIC_API_KEY=invalid-key-123
set PYTHONUNBUFFERED=1
echo Testing with invalid API key...
python orchestrate_enhanced.py --project-type api_service --requirements tests/phase5_validation/requirements/ecommerce_platform.yaml --verbose
echo Exit code: %ERRORLEVEL%