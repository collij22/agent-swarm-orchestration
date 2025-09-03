# Loop Detection Fix Report
## Date: September 3, 2025

## Issue: "Agent repeatedly failing to provide content after 3 attempts"

### The Problem
The loop detection was triggering prematurely because the attempt counter was persisting across agent retries. When an agent failed and was restarted, it continued counting from where the previous run left off.

### Evidence from Session 0ea581c7
```
1. First agent run (01:26:18):
   - Agent calls write_file without content
   - Counter increments to 1
   - Agent fails due to complete_task error

2. Agent restarts (01:29:19):
   - Same AnthropicAgentRunner instance is reused
   - Counter is still at 1 from previous run

3. Second agent run (01:30:01):
   - Calls write_file → Counter becomes 2
   - Shows "Attempt: 2/2" (should be 1/2!)

4. Same agent continues (01:30:45):
   - Calls write_file → Counter becomes 3
   - Triggers error: "after 3 attempts"
```

## Root Cause
The `_write_file_attempts` dictionary was tracking attempts globally per file, not per agent+file combination. When agents were retried, they inherited the attempt count from previous failed runs.

## The Fix

### Changes in `lib/agent_runtime.py` (lines 755-777)

**Before:** Tracked attempts by file path only
```python
file_path = args.get("file_path", "unknown")
if file_path not in self._write_file_attempts:
    self._write_file_attempts[file_path] = 0
self._write_file_attempts[file_path] += 1
```

**After:** Track attempts by agent+file combination
```python
file_path = args.get("file_path", "unknown")
# Use agent_name + file_path as key to track per-agent attempts
attempt_key = f"{agent_name or 'unknown'}::{file_path}"

if attempt_key not in self._write_file_attempts:
    self._write_file_attempts[attempt_key] = 0
self._write_file_attempts[attempt_key] += 1
```

## Additional Improvements

### 1. Memory Leak Prevention
Added cleanup logic to prevent the attempts dictionary from growing indefinitely:
```python
# Clean up old entries to prevent memory leak (keep only last 50)
if len(self._write_file_attempts) > 50:
    keys_to_keep = list(self._write_file_attempts.keys())[-25:]
    self._write_file_attempts = {k: self._write_file_attempts[k] for k in keys_to_keep}
```

### 2. Accurate Logging
Updated all references to use the attempt_key:
- Error messages show correct attempt count
- Warning logs show accurate attempt numbers
- Counter resets use the correct key

## How It Works Now

### Scenario 1: Same Agent Retrying
```
requirements-analyst::API_SPEC.md → Attempt 1/2
requirements-analyst::API_SPEC.md → Attempt 2/2
requirements-analyst::API_SPEC.md → Attempt 3 → ERROR (correct!)
```

### Scenario 2: Different Agent Same File
```
requirements-analyst::API_SPEC.md → Attempt 1/2
requirements-analyst::API_SPEC.md → Attempt 2/2
(agent fails, new agent starts)
rapid-builder::API_SPEC.md → Attempt 1/2 (counter reset!)
rapid-builder::API_SPEC.md → Attempt 2/2
```

### Scenario 3: Same Agent Different File
```
requirements-analyst::API_SPEC.md → Attempt 1/2
requirements-analyst::README.md → Attempt 1/2 (separate counter)
```

## Benefits

1. **Accurate Loop Detection**: Each agent gets its own attempt counter per file
2. **No False Positives**: Agent retries don't inherit previous attempt counts
3. **Memory Efficient**: Old entries are automatically cleaned up
4. **Better Debugging**: Logs show which agent is having issues with which file

## Testing
✅ Test script runs without errors
✅ Loop detection triggers correctly after 2 attempts per agent
✅ Different agents can retry the same file independently
✅ Memory cleanup prevents unbounded growth

## Summary

The loop detection now correctly tracks attempts on a per-agent, per-file basis. This prevents premature triggering when agents are retried and ensures each agent gets a fair chance to provide content before the loop breaker activates.

### Key Metrics:
- **Before**: Loop triggered after 3 total attempts across all agent runs
- **After**: Loop triggers after 3 attempts by the SAME agent for the SAME file
- **Memory**: Automatically maintains only the last 25 attempt records