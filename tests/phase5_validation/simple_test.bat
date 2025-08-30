@echo off
REM Simple test to verify Phase 5 validation is working

echo ========================================
echo Phase 5 Validation - Simple Test
echo ========================================
echo.

REM Test 1: Import check  
echo Test 1: Checking Python imports...
cd ..\..
python -c "from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner; print('[OK] Mock runner imported')" 2>&1
cd tests\phase5_validation
if %errorlevel% neq 0 (
    echo [FAIL] Import test failed
    exit /b 1
)

REM Test 2: Check orchestrator help
echo.
echo Test 2: Checking orchestrator help...
cd ..\..
python orchestrate_enhanced.py --help > nul 2>&1
cd tests\phase5_validation
if %errorlevel% neq 0 (
    echo [FAIL] Orchestrator help failed
    exit /b 1
)
echo [OK] Orchestrator help works

REM Test 3: Check if test files exist
echo.
echo Test 3: Checking test files...
if exist "requirements\ecommerce_platform.yaml" (
    echo [OK] E-commerce requirements found
) else (
    echo [FAIL] E-commerce requirements not found
    exit /b 1
)

REM Test 4: Run analysis on existing results if available
echo.
echo Test 4: Checking analysis script...
python analyze_results.py --help > nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Analysis script failed
    exit /b 1
)
echo [OK] Analysis script works

echo.
echo ========================================
echo All basic tests passed!
echo ========================================
echo.
echo Note: Mock mode testing requires API key or mock implementation fixes.
echo The test suite is properly configured but needs additional work for full mock mode support.
echo.

pause