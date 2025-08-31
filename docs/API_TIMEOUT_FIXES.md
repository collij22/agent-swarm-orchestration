# API Mode Timeout Fixes - Complete Solution

## Problem Summary
Phase 5 validation tests were timing out after 180 seconds when using `--api-mode` with a valid API key. The root cause was multiple layers of timeouts that were set too low for real Claude API calls.

## Issues Identified

1. **HTTP Client Timeout (agent_runtime.py)**
   - Read timeout was only 10 seconds
   - Claude API responses can take 30-60+ seconds for complex prompts
   - This caused "Request timed out or interrupted" errors

2. **Agent Execution Timeout (orchestration_enhanced.py)**
   - Agent timeout was only 60 seconds in API mode
   - Agents making multiple Claude API calls couldn't complete in time
   - This caused "Agent [name] timed out after 60 seconds" errors

3. **Subprocess Timeout (run_tests.py)**
   - Test runner timeout was 180 seconds for ecommerce test
   - With multiple agents running, this wasn't enough time
   - This caused the overall test to fail with timeout

## Solutions Implemented

### 1. HTTP Client Timeouts (lib/agent_runtime.py)
```python
# BEFORE:
timeout=httpx.Timeout(
    connect=5.0,    # 5 seconds to connect
    read=10.0,      # 10 seconds to read response  
    write=5.0,      # 5 seconds to write request
    pool=5.0        # 5 seconds to acquire connection from pool
)

# AFTER:
timeout=httpx.Timeout(
    connect=10.0,    # 10 seconds to connect
    read=120.0,      # 120 seconds to read response (Claude can take time)  
    write=10.0,      # 10 seconds to write request
    pool=10.0        # 10 seconds to acquire connection from pool
)
```

### 2. Agent Execution Timeout (lib/orchestration_enhanced.py)
```python
# BEFORE:
timeout_seconds = 60 if is_api_mode else 30

# AFTER:
timeout_seconds = 300 if is_api_mode else 30  # 5 minutes for API mode
```

### 3. Test Runner Timeout (tests/phase5_validation/run_tests.py)
```python
# BEFORE:
timeout=test_config.get("estimated_time", 300)

# AFTER:
if self.api_mode:
    timeout_seconds = test_config.get("estimated_time", 300) * 3  # Triple for API mode
else:
    timeout_seconds = test_config.get("estimated_time", 300)
```

### 4. API Validation Timeout (lib/agent_runtime.py)
```python
# BEFORE:
validation_thread.join(timeout=10.0)

# AFTER:
validation_thread.join(timeout=30.0)  # Increased for slower connections
```

## Additional Improvements

### Rich Console Subprocess Detection (lib/agent_logger.py)
- Automatically disables Rich console in subprocess environments
- Prevents hanging in Windows subprocesses
- Falls back to simple print statements when needed

## Testing

Run the verification test:
```bash
python test_api_timeout_verification.py
```

Run Phase 5 validation with API mode:
```bash
python tests/phase5_validation/run_tests.py --test ecommerce --api-mode --verbose
```

## Expected Behavior

With these fixes:
- API key validation completes within 30 seconds
- Individual Claude API calls can take up to 120 seconds
- Each agent has up to 5 minutes to complete
- Full test runs have 9+ minutes (3x estimated time)
- No more premature timeouts with valid API keys

## Performance Considerations

The increased timeouts are necessary for real API calls but won't affect mock mode:
- Mock mode still uses original shorter timeouts (30 seconds per agent)
- API mode uses longer timeouts only when needed
- Early success still returns immediately (timeouts are maximums, not delays)

## Troubleshooting

If timeouts still occur:
1. Check network connectivity
2. Verify API key is valid
3. Check Claude API status page for outages
4. Consider increasing timeouts further for very complex tasks
5. Use `--verbose` flag to see detailed progress

## Related Files Modified

1. `lib/agent_runtime.py` - HTTP client and validation timeouts
2. `lib/orchestration_enhanced.py` - Agent execution timeout
3. `tests/phase5_validation/run_tests.py` - Test runner subprocess timeout
4. `lib/agent_logger.py` - Rich console subprocess detection

## Conclusion

The timeout issues have been comprehensively fixed at all layers. The system now properly handles real Claude API calls that can take significant time to complete, while still maintaining reasonable timeouts to catch actual issues.