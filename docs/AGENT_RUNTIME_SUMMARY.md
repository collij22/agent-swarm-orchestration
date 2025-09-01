# Agent Runtime Summary

## Overview
The agent runtime (`lib/agent_runtime.py`) provides the core execution framework for all agents with real Anthropic API integration.

## Model Types & Selection
```python
ModelType.HAIKU   # Fast & cheap (~$1/1M input, $5/1M output)
ModelType.SONNET  # Balanced (~$3/1M input, $15/1M output) 
ModelType.OPUS    # Complex reasoning (~$15/1M input, $75/1M output)
```

**Automatic Selection**: `get_optimal_model(agent_name, complexity)`
- Opus agents: project-architect, ai-specialist, debug-specialist, project-orchestrator, meta-agent
- Haiku agents: documentation-writer, api-integrator
- Default: Sonnet for balanced performance

## AgentContext Structure
- `project_requirements`: Project specifications
- `completed_tasks`: List of finished agent tasks
- `artifacts`: Agent outputs and deliverables
- `decisions`: Architectural/technical decisions
- `created_files`: File tracking by agent
- `verification_required`: Critical deliverables needing validation
- `incomplete_tasks`: Failed tasks for retry

## Core Tools Available
- `write_file`: Create files with verification & tracking
- `run_command`: Execute shell commands
- `record_decision`: Document architectural decisions
- `complete_task`: Mark agent task complete
- `dependency_check`: Verify agent prerequisites
- `request_artifact`: Get files from previous agents
- `verify_deliverables`: Validate critical files exist

## API Integration Features
- **Rate Limiting**: 20 calls/min with proactive prevention
- **Retry Logic**: Exponential backoff up to 60s
- **Error Recovery**: Robust handling with context preservation
- **Mock Mode**: Full simulation without API costs
- **Inter-agent Delays**: 3s between executions for stability

## MCP Enhanced Tools
Optional MCP tools for 60% token reduction:
- `mcp_ref_search`: Documentation fetching
- `mcp_semgrep_scan`: Security scanning
- `mcp_playwright_screenshot`: Visual validation