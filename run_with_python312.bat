@echo off
cd /d "C:\AI projects\1test"
echo Checking for Python 3.12...

if exist "C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" (
    echo Found Python 3.12, using it instead of 3.13...
    "C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" orchestrate_enhanced.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --summary-level concise --max-parallel 2 --human-log
) else if exist "C:\Users\jonlc\AppData\Local\Programs\Python\Python311\python.exe" (
    echo Found Python 3.11, using it instead of 3.13...
    "C:\Users\jonlc\AppData\Local\Programs\Python\Python311\python.exe" orchestrate_enhanced.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --summary-level concise --max-parallel 2 --human-log
) else (
    echo ERROR: Python 3.11 or 3.12 not found. Python 3.13 has stdout issues.
    echo Please install Python 3.12 from https://www.python.org/downloads/
)

pause