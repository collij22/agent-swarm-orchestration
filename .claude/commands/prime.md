---
description: Prime Claude with agent swarm project context
allowed-tools: Bash(git status:*), Bash(git log:*), Read, Glob, Grep
model: claude-sonnet-4-20250514
argument-hint: [task-focus]
---

# Agent Swarm Project Context

You're working on a **production-ready 15-agent orchestration system** with Claude 4 integration. This system automates complex development workflows with minimal human intervention.

## 📋 Project Status & Architecture

Review the core architecture and current implementation status:

@PROJECT_SUMMARY.md
@ultimate_agent_plan.md

## 🏗️ Implementation Standards & Core Runtime

Understand the coding standards and agent execution framework:

@CLAUDE.md
@lib/agent_runtime.py

## 📊 Latest Updates & Configuration

Check recent changes and model configuration:

@docs/MODEL_UPDATE.md

## 🔍 Current State Check

!git status --short
!git log --oneline -5

## 🎯 System Overview

**Key Components:**
- **15 Optimized Agents** in `.claude/agents/` (Opus/Sonnet/Haiku tier system)
- **5 SFA Agents** in `sfa/` (standalone executables using Claude 4 Sonnet)
- **Session Management** (`lib/session_manager.py`, `session_cli.py`)
- **Hook System** (7 hooks in `.claude/hooks/`)
- **Web Dashboard** (`web/` - FastAPI + React)
- **Testing Infrastructure** (`tests/test_agents.py`, `lib/mock_anthropic.py`)

**Technology Stack:**
- Models: Claude 4 Sonnet (`claude-sonnet-4-20250514`) primary
- Cost Optimization: 40-60% reduction via intelligent model selection
- Testing: Mock mode for development without API costs
- Platform: Windows (C:\AI projects\1test)

## 🚀 Key Commands

```bash
# Run orchestrated workflow
uv run orchestrate_v2.py --project-type=web_app --requirements=requirements.yaml

# Run standalone agent
uv run sfa/sfa_project_architect.py --prompt "Design system" --output design.md

# Test without API costs
python tests/test_agents.py --mode mock

# Session management
python session_cli.py list
```

## 📌 Task Focus

$ARGUMENTS

## 🎬 Next Actions

Based on the task focus above:
1. Check if any files need updates for consistency
2. Verify all agents use correct Claude 4 models
3. Review test coverage and add missing tests
4. Consider optimizations for cost/performance
5. Document any new features or changes

**Remember:** 
- All agents must follow CLAUDE.md standards
- Use mock testing before live API calls
- Maintain comprehensive logging with reasoning
- Update PROJECT_SUMMARY.md with significant changes