@echo off
echo Installing dependencies for Python 3.12...
echo.

"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install --upgrade pip
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install anthropic
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install rich
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install networkx
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install pyyaml
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install aiofiles
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install httpx
"C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe" -m pip install tenacity

echo.
echo Dependencies installed! Now you can run:
echo C:\Users\jonlc\AppData\Local\Programs\Python\Python312\python.exe orchestrate_enhanced.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --summary-level concise --max-parallel 2 --human-log
pause