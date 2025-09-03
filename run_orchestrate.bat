@echo off
cd /d "C:\AI projects\1test"
python orchestrate_enhanced.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test5 --progress --summary-level concise --max-parallel 2 --human-log