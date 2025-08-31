---
description: Prime Claude with agent swarm project context
allowed-tools: Bash(git status:*), Bash(git log:*), Read, Glob, Grep
model: claude-sonnet-4-20250514
argument-hint: [task-focus]
---

# Agent Swarm Project Context

You're working on a **100% complete, production-ready 15-agent orchestration system** with Claude 4 integration, comprehensive E2E testing, and self-healing capabilities.

## 📋 Project Status & Architecture

Review the core architecture and current implementation status:

@PROJECT_SUMMARY.md
@ultimate_agent_plan.md

## 🏗️ Implementation Standards & Core Runtime

Understand the coding standards and agent execution framework:

@CLAUDE.md
@docs/AGENT_RUNTIME_SUMMARY.md

## 📊 Latest Updates & Testing Framework

Check recent changes, model configuration, and testing status:

@docs/MODEL_UPDATE.md
@docs/TEST_STATUS.md

## 🔍 Current State Check

!git status --short
!git log --oneline -5

## 🎯 System Overview

**Key Components:**
- **15 Optimized Agents** in `.claude/agents/` (Opus/Sonnet/Haiku tier system)
- **5 SFA Agents** in `sfa/` (standalone executables using Claude 4 Sonnet)
- **Session Management** with analysis & replay (`lib/session_manager.py`)
- **Hook System** (7 hooks in `.claude/hooks/`)
- **Web Dashboard** (`web/` - FastAPI + React with WebSocket)
- **E2E Test Framework** (Phases 1-4 complete, 93.7% quality score)
- **Self-Healing System** with continuous improvement engine

**Technology Stack:**
- Models: Claude 4 Sonnet (`claude-sonnet-4-20250514`) primary
- Cost Optimization: 40-60% reduction via intelligent model selection
- Testing: Mock mode + comprehensive E2E test suite (16,500+ lines)
- Platform: Windows (C:\AI projects\1test)

## 🚀 Key Commands

```bash
# Enhanced orchestration (primary)
python orchestrate_enhanced.py --project-type=web_app --requirements=requirements.yaml

# Run standalone agent
uv run sfa/sfa_project_architect.py --prompt "Design system" --output design.md

# Test without API costs (enhanced mock mode)
python tests/test_agents.py --mode mock --enhanced

# Run comprehensive E2E tests
python tests/e2e_phase4/run_phase4_tests.py --verbose

# Session management
python session_cli.py list
python session_cli.py analyze <session_id>
```

## 📌 Task Focus

$ARGUMENTS

## 🎬 Next Actions

Based on the task focus above:
1. Review implementation against 100% completion status
2. Verify all test phases are functioning correctly
3. Check continuous improvement recommendations
4. Consider any optimization opportunities
5. Document any new features or changes

**Remember:** 
- System is 100% complete with all 10 sections implemented
- E2E test framework validates all agent interactions
- Self-healing capabilities enable continuous optimization
- Update PROJECT_SUMMARY.md with significant changes