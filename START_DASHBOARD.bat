@echo off
echo ================================================================================
echo QUICKSHOP MVP - DASHBOARD MODE
echo ================================================================================
echo.
echo Dashboard will open at: http://localhost:5174
echo.
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
python RUN_DASHBOARD.py
pause
