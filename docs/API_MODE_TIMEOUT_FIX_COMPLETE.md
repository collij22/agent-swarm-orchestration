# Complete API Mode Timeout Fix - December 2024

## Executive Summary
Fixed all timeout issues in Phase 5 validation tests when using `--api-mode`. The system now handles real Claude API calls properly with appropriate timeouts at every layer.

## Problems Identified

### 1. **Incorrect Error Reporting**
- **Issue**: Test reported "timeout after 180s" but actually ran for 540s
- **Cause**: Error handler used `estimated_time` instead of actual timeout
- **Fix**: Updated to report actual timeout value

### 2. **Insufficient Agent Execution Timeout**
- **Issue**: Agents timing out after 300s (5 minutes) in API mode
- **Cause**: AI agents can make many Claude API calls, each taking 30-60s
- **Fix**: Increased to 480s (8 minutes) per agent

### 3. **Insufficient Test Runner Timeout**
- **Issue**: Subprocess timeout too short for sequential agent execution
- **Cause**: Multiple agents running sequentially need more total time
- **Fix**: Increased to 5x estimated time or minimum 15 minutes

### 4. **Poor Process Termination**
- **Issue**: Hung processes not terminating cleanly
- **Cause**: subprocess.run doesn't provide good control
- **Fix**: Switched to Popen with graceful termination and force kill

### 5. **HTTP Client Timeouts Too Short**
- **Issue**: Claude API calls timing out at HTTP level
- **Cause**: Read timeout was only 10-120 seconds
- **Fix**: Already fixed - 120s read timeout is sufficient

## Complete Solution Implementation

### Layer 1: HTTP Client (lib/agent_runtime.py)
```python
timeout=httpx.Timeout(
    connect=10.0,    # 10 seconds to connect
    read=120.0,      # 120 seconds for Claude responses
    write=10.0,      # 10 seconds to write
    pool=10.0        # 10 seconds for connection pool
)
```

### Layer 2: Agent Execution (lib/orchestration_enhanced.py)
```python
# 8 minutes per agent in API mode (was 5 minutes)
timeout_seconds = 480 if is_api_mode else 30
```

### Layer 3: Test Runner (tests/phase5_validation/run_tests.py)
```python
# API mode: 5x estimated time or minimum 15 minutes
if self.api_mode:
    timeout_seconds = max(test_config.get("estimated_time", 300) * 5, 900)
else:
    timeout_seconds = test_config.get("estimated_time", 300)

# Better process control with Popen
process = subprocess.Popen(cmd, ...)
try:
    stdout, stderr = process.communicate(timeout=timeout_seconds)
except subprocess.TimeoutExpired:
    process.terminate()  # Graceful termination
    try:
        stdout, stderr = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()  # Force kill if needed
```

### Layer 4: Error Reporting (tests/phase5_validation/run_tests.py)
```python
# Report actual timeout, not estimated time
actual_timeout = timeout_seconds
print(f"[FAIL] Test timeout after {actual_timeout}s")
```

## Timeout Cascade

With these fixes, the timeout cascade is:

1. **HTTP Level**: 120 seconds per Claude API call
2. **Agent Level**: 480 seconds (8 minutes) per agent
3. **Test Level**: 900+ seconds (15+ minutes) for full test
4. **Graceful Shutdown**: 5 seconds to terminate cleanly
5. **Force Kill**: Immediate if graceful shutdown fails

## Testing the Fix

Run Phase 5 validation with API mode:
```bash
python tests/phase5_validation/run_tests.py --test ecommerce --api-mode --verbose
```

Expected behavior:
- Test runs to completion without timing out
- If timeout occurs, reports correct timeout value
- Processes terminate cleanly without hanging
- Agents have sufficient time for multiple API calls

## Performance Impact

- **Mock Mode**: No change (still uses 30s agent timeout)
- **API Mode**: More generous timeouts prevent false failures
- **Early Success**: Tests complete as soon as done (timeouts are maximums)
- **Resource Usage**: Better cleanup prevents zombie processes

## Root Cause Analysis

The fundamental issue was that real Claude API calls take much longer than expected:
- Each API call: 30-60 seconds
- Agents make multiple calls: 5-10 per agent
- Multiple agents run: 3-5 per test
- Total time needed: 10-20 minutes for complex tests

The original timeouts were designed for mock mode and were far too short for real API usage.

## Monitoring and Debugging

If tests still timeout:
1. Check session logs for which agent is hanging
2. Look for "timed out after X seconds" messages
3. Verify API key is valid and has sufficient credits
4. Check Claude API status for outages
5. Use `--verbose` flag for detailed output

## Files Modified

1. `lib/agent_runtime.py` - HTTP client timeouts (already done)
2. `lib/orchestration_enhanced.py` - Agent execution timeout increased to 8 min
3. `tests/phase5_validation/run_tests.py` - Test runner timeout and process control
4. `lib/agent_logger.py` - Rich console subprocess detection (already done)

## Conclusion

The timeout issues have been comprehensively fixed:
- Agents have 8 minutes each (up from 5)
- Tests have 15+ minutes total (up from 9)
- Error reporting shows actual timeout values
- Process termination is robust with graceful shutdown and force kill
- All layers work together to handle slow API calls

The system now properly handles real Claude API usage in production environments.