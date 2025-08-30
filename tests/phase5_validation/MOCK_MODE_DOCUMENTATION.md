# Mock Mode Documentation - Phase 5 Validation Suite

## Overview

The mock mode implementation allows testing of the agent swarm system without requiring an Anthropic API key. It simulates agent behavior, tool execution, and requirement tracking for comprehensive testing.

## Current Status: FUNCTIONAL ✅

The mock mode is now operational with the following capabilities:
- Agent simulation with realistic responses
- Tool execution with mock results
- Requirement tracking
- File system simulation
- Usage metrics and cost estimation
- Progress tracking

## How to Enable Mock Mode

### Method 1: Environment Variable
```python
import os
os.environ['MOCK_MODE'] = 'true'
```

### Method 2: Command Line (Windows)
```batch
set MOCK_MODE=true
python orchestrate_enhanced.py --project-type api_service --requirements requirements.yaml
```

### Method 3: PowerShell
```powershell
$env:MOCK_MODE = 'true'
python orchestrate_enhanced.py --project-type api_service --requirements requirements.yaml
```

## Implementation Details

### 1. MockAnthropicEnhancedRunner
Located in: `lib/mock_anthropic_enhanced.py`

Key features:
- Mimics the AnthropicAgentRunner interface
- Handles tool registration and execution
- Simulates agent responses based on agent type
- Tracks iterations to prevent infinite loops
- Returns mock results for all standard tools

### 2. EnhancedMockAnthropicClient
Provides:
- Realistic message generation
- Agent-specific response patterns
- Requirement tracking (0-100% completion)
- File system simulation in temporary directories
- Controlled failure simulation (5% default rate)
- Tool execution tracking

### 3. Supported Tools
The mock mode provides realistic responses for:
- `write_file` - Creates files in temp directory
- `read_file` - Reads from simulated file system
- `dependency_check` - Returns ready status
- `run_tests` - Returns successful test results
- `analyze_requirements` - Returns requirement analysis
- `create_directory` - Creates directories
- `execute_command` - Returns mock command output
- `git_status` - Returns clean git status
- `install_dependencies` - Returns success
- `build_project` - Returns build success
- `deploy` - Returns deployment success
- `quality_check` - Returns quality score
- `performance_test` - Returns performance metrics
- `security_scan` - Returns security results

## Testing Scripts

### 1. Simple Test (`simple_test.bat`)
Tests basic functionality:
- Python imports
- Orchestrator help
- Requirements file existence
- Analysis script functionality

### 2. Enhanced Mock Test (`test_mock_enhanced.py`)
Comprehensive testing:
- Mock runner instantiation
- Tool registration
- Agent execution
- Usage summary
- Mini orchestration

### 3. Debug Script (`debug_orchestrator.py`)
For troubleshooting:
- Shows return codes
- Captures stderr/stdout
- Handles encoding issues

## Known Limitations

1. **Agent Directory Requirement**: The orchestrator expects `.claude/agents` directory to exist. Without it, agent loading fails.

2. **Tool Result Handling**: Mock tools return simplified results that may not fully match real API responses.

3. **Iteration Limit**: Mock agents stop after 3 tool calls to prevent infinite loops.

4. **Quality Scores**: Tests may show 0% quality if the orchestrator fails to complete successfully.

## Troubleshooting

### Issue: Unicode Encoding Errors
**Solution**: Fixed by adding `encoding='utf-8', errors='replace'` to subprocess calls.

### Issue: Tests Return 0% Quality Score
**Cause**: Orchestrator returning non-zero exit code.
**Solution**: Ensure agent directory exists and requirements are properly formatted.

### Issue: Mock Mode Not Activating
**Check**:
```python
import os
print(f"MOCK_MODE: {os.environ.get('MOCK_MODE')}")
```
Should output: `MOCK_MODE: true`

### Issue: Infinite Loop in Mock Execution
**Solution**: Implemented iteration limit (max 3) in MockAnthropicEnhancedRunner.

## Usage Examples

### Example 1: Run Single Test
```python
import os
os.environ['MOCK_MODE'] = 'true'

from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner
from lib.agent_logger import create_new_session

logger = create_new_session()
runner = MockAnthropicEnhancedRunner(logger)

# Run agent
success, result, context = runner.run_agent(
    agent_name="rapid-builder",
    agent_prompt="Create a Python application",
    context=context,
    max_iterations=3
)
```

### Example 2: Full Test Suite
```batch
cd tests\phase5_validation
set MOCK_MODE=true
python run_tests.py --all
```

### Example 3: Single Scenario Test
```batch
cd tests\phase5_validation
set MOCK_MODE=true
python run_tests.py --test ecommerce --verbose
```

## Performance Metrics

Mock mode provides:
- **Speed**: 10-100x faster than real API calls
- **Cost**: $0 (simulated costs for tracking)
- **Reliability**: No network dependencies
- **Coverage**: Supports all major agent types

## Future Enhancements

1. **Dynamic Response Generation**: Use LLM to generate more realistic responses
2. **State Persistence**: Save/load mock state between runs
3. **Advanced Failure Scenarios**: More sophisticated error simulation
4. **Performance Profiling**: Track mock vs real performance
5. **Response Templates**: Customizable response patterns per agent

## Summary

The mock mode implementation successfully enables testing without API keys. While it has some limitations regarding agent directory structure and simplified responses, it provides a functional testing environment for the Phase 5 validation suite.

### Key Achievements:
✅ No API key required
✅ Tool execution simulation
✅ Requirement tracking
✅ File system operations
✅ Usage metrics
✅ Error handling
✅ Windows compatibility

### Recommendation:
For production testing, use real API keys when available. Mock mode is ideal for:
- CI/CD pipelines
- Local development
- Cost-free testing
- Rapid iteration