# API Mode Timeout Fix Documentation

## Issue Summary
The Phase 5 validation tests were timing out when running in API mode (`--api-mode` flag). The test would hang indefinitely and eventually timeout after 180 seconds with no useful output.

## Root Causes Identified

1. **No timeout on API calls**: The `run_agent_async` method in `agent_runtime.py` had no timeout when making actual Anthropic API calls, allowing it to hang indefinitely if the API didn't respond.

2. **Silent API key failures**: When running without an API key in API mode, the system would silently fall back to simulation mode without clear error messaging.

3. **Subprocess timeout too short**: The test runner's subprocess timeout (180s) would kill the process before getting useful diagnostic information.

## Fixes Applied

### 1. Added Timeout Wrapper to Agent Execution
**File**: `lib/orchestration_enhanced.py` (line 530-553)

```python
# Execute agent with timeout (60 seconds per agent in API mode)
try:
    # Check if we're in API mode (not mock mode)
    import os
    is_api_mode = os.environ.get('MOCK_MODE') != 'true'
    timeout_seconds = 60 if is_api_mode else 30  # Shorter timeout for mock mode
    
    success, result, updated_context = await asyncio.wait_for(
        runtime.run_agent_async(
            agent_name,
            agent_config["prompt"],
            context,
            model=self._get_model(agent_config.get("model", "sonnet")),
            max_iterations=15
        ),
        timeout=timeout_seconds
    )
except asyncio.TimeoutError:
    # Agent execution timed out
    error_msg = f"Agent {agent_name} timed out after {timeout_seconds} seconds"
    self.logger.log_error("orchestrator", error_msg)
    success = False
    result = error_msg
    updated_context = context
```

**Benefits**:
- Prevents indefinite hanging on API calls
- Different timeouts for API (60s) vs mock mode (30s)
- Clear error message when timeout occurs
- Graceful recovery allows workflow to continue

### 2. Added Clear Error for Missing API Key
**File**: `lib/agent_runtime.py` (line 247-256)

### 3. Added API Key Format Validation
**File**: `lib/agent_runtime.py` (line 189-197)

```python
# Validate API key format (should start with 'sk-ant-' for real keys)
if self.api_key and not (self.api_key.startswith('sk-ant-') or os.environ.get('MOCK_MODE') == 'true'):
    self.logger.log_error(
        "agent_runtime",
        f"Invalid API key format. Expected 'sk-ant-...' but got '{self.api_key[:10]}...'",
        "API key validation failed"
    )
    # Treat invalid key format as no key to avoid hanging on API calls
    self.api_key = None
```

**Benefits**:
- Validates API key format before attempting to use it
- Prevents attempts to use invalid keys (e.g., placeholder keys)
- Clear error message shows expected format
- Falls back to simulation mode for invalid keys

### 4. No Retry on Authentication Errors
**File**: `lib/agent_runtime.py` (line 445-451)

```python
# Check for authentication errors (401) - don't retry these
if "401" in error_str or "authentication_error" in error_str or "invalid x-api-key" in error_str:
    self.logger.log_error(
        "claude_api",
        "Authentication failed - invalid API key",
        str(e)
    )
    raise e  # Don't retry authentication errors
```

**Benefits**:
- Authentication errors (401) fail immediately without retries
- Prevents wasting time on retries that will always fail
- Clear error message for authentication failures
- Faster feedback when API key is invalid

### 5. Clear Error for Missing API Key (Enhanced)
**File**: `lib/agent_runtime.py` (line 247-256)

```python
# Use simulation mode only if no client is available (neither real nor mock)
if self.client is None:
    # Check if we're supposed to be in API mode but missing key
    import os
    if os.environ.get('MOCK_MODE') != 'true' and not self.api_key:
        error_msg = "API mode requested but no ANTHROPIC_API_KEY found. Set it with: set ANTHROPIC_API_KEY=your-key-here"
        self.logger.log_error("agent_runtime", error_msg, "Missing API key")
        return False, error_msg, context
    # Simulation mode
    return self._simulate_agent(agent_name, context)
```

**Benefits**:
- Immediate failure with clear error message when API key is missing
- Helpful instructions on how to set the API key
- Prevents confusing fallback to simulation mode
- Logged for debugging

## Testing

### Test Script Created
**File**: `test_api_fix.py`

Verifies:
1. API mode fails gracefully without key
2. Mock mode continues to work
3. Timeout handling is properly integrated

### Test Results
```
✓ Test 1: API mode without key correctly detected and reported
✓ Test 2: Mock mode works without issues
✓ Test 3: Timeout wrapper properly integrated
```

## Usage Instructions

### Running in API Mode (Real Claude)
```bash
# Set your API key first
set ANTHROPIC_API_KEY=your-key-here  # Windows
export ANTHROPIC_API_KEY=your-key-here  # Linux/Mac

# Run the test
python tests/phase5_validation/run_tests.py --test ecommerce --api-mode
```

### Running in Mock Mode (Default, No API Costs)
```bash
# No API key needed
python tests/phase5_validation/run_tests.py --test ecommerce
```

## Impact

1. **Reliability**: Tests no longer hang indefinitely in API mode
2. **Debugging**: Clear error messages when API issues occur
3. **User Experience**: Helpful instructions for configuration
4. **Performance**: Appropriate timeouts prevent resource waste
5. **Flexibility**: Different timeout values for different modes

## Recommendations

1. **Set appropriate API key**: Always set `ANTHROPIC_API_KEY` when using `--api-mode`
2. **Use mock mode for testing**: Default mock mode is faster and free
3. **Monitor timeouts**: Adjust timeout values if needed for slower connections
4. **Check logs**: Session logs now contain clear error messages

## Files Modified

1. `lib/orchestration_enhanced.py` - Added timeout wrapper (lines 530-553)
2. `lib/agent_runtime.py` - Multiple fixes:
   - API key format validation (lines 189-197)
   - No retry on authentication errors (lines 445-451)
   - Clear error for missing API key (lines 247-256)
3. `test_api_fix.py` - Created initial test verification script
4. `test_api_fix_v2.py` - Enhanced test script with all validations
5. `docs/API_MODE_TIMEOUT_FIX.md` - This documentation

---

*Fixed: August 31, 2025*
*Issue: Phase 5 validation test timeout in API mode*
*Solution: Added timeout handling and clear error messaging*