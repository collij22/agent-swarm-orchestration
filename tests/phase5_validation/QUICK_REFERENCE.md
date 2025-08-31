# Phase 5 Test Mode Quick Reference

## Quick Commands

### Mock Mode (FREE - No API Key Required)
```bash
# Single test
python run_tests.py --test ecommerce

# All tests
python run_tests.py --all

# Parallel execution
python run_tests.py --all --parallel
```

### API Mode (COSTS MONEY - API Key Required)
```bash
# First set your API key
set ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Single test with real API
python run_tests.py --test ecommerce --api-mode

# All tests with real API
python run_tests.py --all --api-mode

# With progress monitoring
python run_tests.py --test ecommerce --api-mode --verbose
```

## Mode Comparison

| Mode | Speed | Cost | API Key | Use Case |
|------|-------|------|---------|----------|
| **Mock** | Fast (1s) | FREE | No | Development, CI/CD |
| **API** | Slow (30-300s) | $0.10-0.40/test | Yes | Final validation |

## Decision Tree

```
Need to test quickly? → Mock Mode (default)
Need real agent intelligence? → API Mode (--api-mode)
Running in CI/CD? → Mock Mode
Final acceptance testing? → API Mode
No API key? → Mock Mode only
```

## Cost Estimates (API Mode Only)

- Single test: $0.10 - $0.40
- All 5 tests: $0.50 - $2.00
- Expect 30-300 seconds per test

## Environment Check

```bash
# Check if API key is set
echo %ANTHROPIC_API_KEY%

# Check if mock mode is active
echo %MOCK_MODE%
```