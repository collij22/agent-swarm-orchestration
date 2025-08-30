# Claude 4 Model Update & Cost Optimization Guide

## 🚀 Overview

The agent swarm has been updated to use the latest Claude 4 models with intelligent cost optimization. This update includes:

- **Claude 4 Sonnet** (`claude-sonnet-4-20250514`) - Primary model for balanced performance
- **Claude 3.5 Haiku** (`claude-3-5-haiku-20241022`) - Fast & cost-optimized
- **Claude 4 Opus** (`claude-opus-4-20250514`) - Complex reasoning tasks

## 📊 Model Selection Strategy

### Automatic Model Selection

The system now automatically selects the optimal model based on:
1. **Agent Type** - Different agents have different complexity requirements
2. **Task Complexity** - Simple tasks use cheaper models
3. **Cost Optimization** - Balances performance with API costs

### Model Assignments by Agent

#### Opus Agents (Complex Reasoning)
- `project-architect` - System design requires deep analysis
- `ai-specialist` - AI/ML integration needs sophisticated understanding
- `debug-specialist` - Complex debugging requires advanced reasoning
- `project-orchestrator` - Workflow coordination needs strategic thinking
- `meta-agent` - Agent creation requires meta-level reasoning

#### Sonnet Agents (Balanced Performance)
- `rapid-builder` - Code generation with good quality
- `quality-guardian` - Testing and security analysis
- `frontend-specialist` - UI/UX implementation
- `database-expert` - Schema design and optimization
- `performance-optimizer` - Performance analysis
- `devops-engineer` - Deployment and infrastructure
- `code-migrator` - Legacy code updates
- `requirements-analyst` - Requirement parsing

#### Haiku Agents (Fast & Cheap)
- `documentation-writer` - Documentation generation
- `api-integrator` - Simple integration tasks

## 💰 Cost Analysis

### Pricing Comparison (per 1M tokens)

| Model | Input Cost | Output Cost | Use Case |
|-------|------------|-------------|----------|
| Claude 3.5 Haiku | ~$1 | ~$5 | Simple tasks, documentation |
| Claude 4 Sonnet | ~$3 | ~$15 | Standard development tasks |
| Claude 3 Opus | ~$15 | ~$75 | Complex reasoning, architecture |

### Expected Savings

- **Before**: All agents using Sonnet = ~$18/1M tokens average
- **After**: Optimized mix = ~$7-10/1M tokens average
- **Savings**: 40-60% reduction in API costs

### Real-World Example

For a typical web app project:
- Architecture phase: 1 Opus call (~$0.20)
- Building phase: 5 Sonnet calls (~$0.30)
- Documentation: 3 Haiku calls (~$0.05)
- **Total**: ~$0.55 vs $1.20 (all Sonnet)

## 🔧 Configuration

### Using Specific Models

```python
from lib.agent_runtime import ModelType, get_optimal_model

# Automatic selection
model = get_optimal_model("rapid-builder")  # Returns SONNET

# Override for simple task
model = get_optimal_model("project-architect", "simple")  # Returns HAIKU

# Force specific model
model = ModelType.OPUS  # Use Opus directly
```

### Environment Setup

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key"

# Install dependencies
pip install anthropic rich pyyaml
```

## 🧪 Testing

### Mock Testing (No Costs)

```bash
# Run tests with mock API
python tests/test_agents.py --mode mock

# Test specific agent
python tests/test_agents.py --mode mock --agent rapid-builder
```

### Live Testing (With Budget)

```bash
# Run tests with real API (limited budget)
python tests/test_agents.py --mode live --budget 1.00

# Monitor costs in real-time
python tests/test_agents.py --mode live --verbose
```

### Performance Benchmarks

```bash
# Run performance benchmarks
python tests/test_agents.py --mode mock --benchmark

# Results show:
# - Average execution time per agent
# - Token usage estimates
# - Cost projections
```

## 📈 Monitoring & Optimization

### Cost Tracking

The system tracks:
- Input/output tokens per agent
- Estimated costs per session
- Agent performance metrics
- Model usage distribution

### View Metrics

```bash
# Session metrics
python session_cli.py metrics --period daily

# Agent performance
python session_cli.py analyze <session_id> --types cost_analysis
```

### Optimization Tips

1. **Batch Operations** - Group similar tasks to reduce API calls
2. **Cache Results** - Reuse responses for similar queries
3. **Use Mock Mode** - Test thoroughly before live execution
4. **Monitor Usage** - Track costs and optimize agent selection

## 🔄 Migration from Old Models

### Updated Files

1. **lib/agent_runtime.py**
   - Updated `ModelType` enum with new models
   - Added `get_optimal_model()` function

2. **SFA Agents** (sfa/*.py)
   - Updated to use `claude-sonnet-4-20250514`
   - Maintained backward compatibility

3. **Testing Infrastructure**
   - Added `lib/mock_anthropic.py` for cost-free testing
   - Created `tests/test_agents.py` for comprehensive testing

### Breaking Changes

None - the update maintains full backward compatibility.

## 🚨 Troubleshooting

### Common Issues

1. **Encoding Errors on Windows**
   - Fixed by removing emoji characters from logger
   - Use ASCII alternatives for better compatibility

2. **Model Not Found**
   - Ensure you're using the exact model names
   - Check API key permissions for model access

3. **High Costs**
   - Review model assignments
   - Use mock mode for development
   - Implement caching for repeated queries

### Debug Commands

```bash
# Check model configuration
python -c "from lib.agent_runtime import ModelType; print([m.value for m in ModelType])"

# Test model selection
python -c "from lib.agent_runtime import get_optimal_model; print(get_optimal_model('rapid-builder'))"

# Verify API connection
python -c "import os; print('API Key Set:', bool(os.getenv('ANTHROPIC_API_KEY')))"
```

## 📚 Additional Resources

- [Anthropic API Documentation](https://docs.anthropic.com)
- [Claude Model Comparison](https://www.anthropic.com/claude)
- [Project README](../README.md)
- [Agent Architecture](../ultimate_agent_plan.md)

## 🎯 Next Steps

1. **Monitor Costs** - Track actual usage vs estimates
2. **Fine-tune Assignments** - Adjust model selection based on results
3. **Implement Caching** - Add response caching for common queries
4. **Add Fallbacks** - Implement graceful degradation for API limits

---

*Last Updated: August 2025*
*Model Version: Claude 4 Sonnet (claude-sonnet-4-20250514)*