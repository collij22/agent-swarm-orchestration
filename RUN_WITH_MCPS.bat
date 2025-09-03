@echo off
echo ============================================================
echo QUICKSHOP MVP ORCHESTRATION - WITH MCPs ENABLED
echo ============================================================
echo.
echo This will generate a complete e-commerce application
echo with all MCP tools enabled for enhanced capabilities
echo.
echo MCPs provide:
echo   - Semgrep security scanning
echo   - Ref documentation (60%% token savings)
echo   - Playwright visual testing
echo   - Stripe payment integration
echo   - Firecrawl web scraping
echo   - And more based on workflow needs
echo.
echo ============================================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

echo Starting orchestration with MCPs enabled...
echo.

python FIX_SCHEMAS.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS! QuickShop MVP has been generated!
    echo ============================================================
    echo.
    echo Next steps:
    echo   cd projects\quickshop-mvp-test6
    echo   docker-compose up
    echo.
    echo Then open:
    echo   http://localhost:3000 (Frontend)
    echo   http://localhost:8000 (Backend API)
    echo.
) else (
    echo.
    echo ============================================================
    echo ERROR: Orchestration failed
    echo ============================================================
    echo.
    echo Check the error messages above for details.
    echo Common issues:
    echo   1. ANTHROPIC_API_KEY not set
    echo   2. Network connectivity issues
    echo   3. Python dependencies not installed
    echo.
)

pause