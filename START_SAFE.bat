@echo off
echo ============================================================
echo QUICKSHOP MVP - SAFE ORCHESTRATION
echo ============================================================
echo.
echo This version prevents response truncation issues by:
echo - Enforcing single file operations
echo - Detecting truncated content
echo - Breaking retry loops
echo - Generating comprehensive placeholders
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

python orchestrate_safe.py

pause
