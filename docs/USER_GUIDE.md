# Agent Swarm System - Comprehensive User Guide

## Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [Developer Guide](#developer-guide)
3. [Administrator Guide](#administrator-guide)
4. [API Integration Guide](#api-integration-guide)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Best Practices](#best-practices)
7. [Security Guidelines](#security-guidelines)
8. [Performance Tuning](#performance-tuning)

---

## Quick Start Guide

### System Requirements
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.11 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 10GB free space
- **API Key**: Anthropic API key for Claude 4 models

### Installation (5 minutes)

```bash
# Clone the repository
git clone https://github.com/your-org/agent-swarm.git
cd agent-swarm

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Verify installation
python orchestrate_enhanced.py --help
```

### Your First Workflow (2 minutes)

```bash
# Create a simple requirements file
cat > my_app.yaml << EOF
project:
  name: "TodoApp"
  type: "web_app"
  
features:
  - User authentication
  - Task CRUD operations
  - Real-time updates
EOF

# Execute the workflow
python orchestrate_enhanced.py --requirements=my_app.yaml --project-type=web_app

# Monitor progress
python session_cli.py monitor --interval 5
```

---

## Developer Guide

### Understanding the Agent System

The agent swarm consists of **15 specialized agents** organized in three tiers:

#### Tier 1: Core Development Agents
- **project-architect**: System design and architecture
- **rapid-builder**: Fast prototyping and implementation
- **ai-specialist**: AI/ML feature integration
- **quality-guardian**: Testing and security
- **devops-engineer**: Deployment and infrastructure

#### Tier 2: Specialized Technical Agents
- **api-integrator**: Third-party service integration
- **database-expert**: Schema design and optimization
- **frontend-specialist**: UI/UX implementation
- **performance-optimizer**: Performance improvements
- **documentation-writer**: Documentation generation

#### Tier 3: Orchestration & Support Agents
- **project-orchestrator**: Workflow coordination
- **requirements-analyst**: Requirement parsing
- **code-migrator**: Legacy system updates
- **debug-specialist**: Complex debugging
- **meta-agent**: Agent customization

### Creating Custom Workflows

#### Basic Workflow Structure
```yaml
project:
  name: "MyProject"
  type: "web_app"  # Options: web_app, api_service, ai_solution, mobile_app
  timeline: "2 weeks"
  priority: "MVP"  # Options: MVP, full_feature, enterprise

features:
  - "Feature 1 description"
  - "Feature 2 description"
  
tech_overrides:
  frontend:
    framework: "Next.js"
  backend:
    framework: "FastAPI"
    
constraints:
  budget: "$5000"
  deployment: "AWS"
  
success_metrics:
  - "< 200ms API response time"
  - "99.9% uptime"
```

#### Advanced Workflow Options
```python
# Python API for programmatic workflow execution
from orchestrate_enhanced import EnhancedOrchestrator

orchestrator = EnhancedOrchestrator()

# Configure workflow
workflow_config = {
    "project_type": "web_app",
    "requirements": {
        "project_name": "EnterpriseApp",
        "features": ["SSO", "Multi-tenancy", "Analytics"]
    },
    "options": {
        "max_parallel_agents": 5,
        "enable_monitoring": True,
        "checkpoint_frequency": 2,
        "mock_mode": False  # Use real API
    }
}

# Execute
result = orchestrator.execute_workflow(workflow_config)
print(f"Workflow ID: {result['workflow_id']}")
```

### Using Individual Agents

```bash
# Architecture design
python sfa/sfa_project_architect.py \
  --prompt "Design a scalable e-commerce platform" \
  --requirements requirements.yaml \
  --output architecture.md

# AI integration
python sfa/sfa_ai_specialist_enhanced.py \
  --project-path ./my_project \
  --generate all

# DevOps setup
python sfa/sfa_devops_engineer_enhanced.py \
  --project-path ./my_project \
  --generate docker,ci,tests
```

### Testing Your Implementation

#### Mock Mode Testing (No API Costs)
```bash
# Test with enhanced mock mode
python tests/test_agents.py --mode mock --enhanced

# Test specific workflow
python tests/e2e_phase4/run_phase4_tests.py --scenario web_app

# Run comprehensive test suite
pytest tests/ -v --cov=lib --cov-report=html
```

#### Integration Testing
```python
# tests/test_my_integration.py
import asyncio
from lib.agent_runtime import AnthropicAgentRunner, AgentContext

async def test_custom_workflow():
    runner = AnthropicAgentRunner()
    context = AgentContext(
        project_requirements={"name": "TestApp"},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="planning"
    )
    
    success, result, context = await runner.run_agent_async(
        "rapid-builder",
        "Build a REST API",
        context
    )
    
    assert success
    assert "api" in result.lower()
```

---

## Administrator Guide

### System Setup

#### Production Deployment

```bash
# Build production Docker image
docker build -f Dockerfile.production -t agent-swarm:prod .

# Start production stack
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
curl http://localhost:8000/api/v1/monitoring/health
```

#### Environment Configuration

```bash
# .env.production
ANTHROPIC_API_KEY=sk-ant-xxxxx
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/agentswarm
LOG_LEVEL=INFO
MAX_PARALLEL_AGENTS=5
CACHE_TTL_SECONDS=3600
RATE_LIMIT_PER_MINUTE=60
MEMORY_LIMIT_MB=2000
```

### Security Configuration

#### API Key Management
```python
from lib.security_manager import SecurityManager

security = SecurityManager()

# Create admin user
admin = security.rbac_manager.create_user(
    username="admin",
    email="admin@company.com",
    role=AccessLevel.ADMIN
)

# Generate API key
api_key = security.api_key_manager.generate_api_key(
    user_id=admin.user_id,
    project="production"
)

# Rotate keys monthly
security.rotate_api_keys()
```

#### Access Control Configuration
```yaml
# config/rbac.yaml
roles:
  admin:
    permissions:
      - workflow.*
      - agent.*
      - config.*
      - user.*
  
  developer:
    permissions:
      - workflow.execute
      - workflow.read
      - agent.execute
      - logs.read
  
  viewer:
    permissions:
      - workflow.read
      - logs.read
```

### Monitoring & Alerting

#### Prometheus Metrics
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agent-swarm'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Agent Swarm Monitoring",
    "panels": [
      {
        "title": "Workflow Success Rate",
        "targets": [
          {
            "expr": "rate(workflow_success_total[5m])"
          }
        ]
      },
      {
        "title": "Agent Execution Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, agent_duration_seconds)"
          }
        ]
      }
    ]
  }
}
```

#### Alert Rules
```yaml
# alerts.yml
groups:
  - name: agent_swarm
    rules:
      - alert: HighErrorRate
        expr: rate(workflow_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High workflow error rate"
          
      - alert: MemoryPressure
        expr: memory_usage_bytes / memory_limit_bytes > 0.9
        for: 2m
        annotations:
          summary: "High memory usage"
```

### Backup & Recovery

```bash
# Backup sessions and checkpoints
./scripts/backup.sh --include sessions,checkpoints

# Restore from backup
./scripts/restore.sh --backup-id 20240101-1200

# Schedule daily backups
crontab -e
0 2 * * * /path/to/scripts/backup.sh --auto
```

---

## API Integration Guide

### Authentication

```python
import requests

# API Key authentication
headers = {
    "X-API-Key": "sk-production-xxxxx"
}

response = requests.get(
    "http://localhost:8000/api/v1/workflows",
    headers=headers
)
```

### Workflow Execution

```python
# Execute workflow via API
workflow_data = {
    "project_type": "web_app",
    "requirements": {
        "project_name": "MyApp",
        "features": ["auth", "dashboard"],
        "tech_overrides": {
            "frontend": {"framework": "React"}
        }
    },
    "options": {
        "mock_mode": False,
        "max_parallel_agents": 3
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/workflows",
    json=workflow_data,
    headers=headers
)

workflow_id = response.json()["workflow_id"]
```

### WebSocket Real-time Updates

```javascript
// JavaScript WebSocket client
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'subscribe',
        workflow_id: workflowId
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Progress:', data.progress);
    console.log('Active agents:', data.active_agents);
};
```

### Session Analysis

```python
# Get session analysis
analysis = requests.get(
    f"http://localhost:8000/api/v1/sessions/{session_id}/analysis",
    headers=headers
).json()

print(f"Quality Score: {analysis['quality_assessment']['overall_score']}")
print(f"Requirement Coverage: {analysis['requirement_coverage']}")

# Get recommendations
for rec in analysis['recommendations']:
    if rec['priority'] == 'critical':
        print(f"CRITICAL: {rec['recommendation']}")
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: Rate Limit Exceeded
**Error**: `Error 429 - Rate Limit Exceeded`

**Solution**:
```python
# Adjust rate limiting in config
RATE_LIMIT_PER_MINUTE=30  # Reduce concurrent requests

# Or use exponential backoff
from lib.agent_runtime import AnthropicAgentRunner
runner = AnthropicAgentRunner()
runner.max_retries = 5
runner.retry_delay = 2
```

#### Issue: Agent Execution Failure
**Error**: `Agent 'rapid-builder' failed: Tool execution error`

**Solution**:
```bash
# Check agent logs
python session_cli.py view <session_id> --filter errors

# Retry with verbose logging
LOG_LEVEL=DEBUG python orchestrate_enhanced.py \
  --requirements=requirements.yaml \
  --verbose

# Use checkpoint recovery
python orchestrate_enhanced.py \
  --resume-checkpoint checkpoints/workflow_*.json
```

#### Issue: Memory Issues
**Error**: `MemoryError` or high memory usage

**Solution**:
```python
# Optimize memory settings
from lib.performance_optimizer import MemoryManager

memory_mgr = MemoryManager(target_memory_mb=1500)
memory_mgr.optimize_gc()

# Reduce parallel execution
MAX_PARALLEL_AGENTS=2
```

#### Issue: Slow Performance
**Symptom**: Workflow taking longer than expected

**Solution**:
```python
# Enable caching
from lib.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer()
report = optimizer.get_performance_report()

# Apply optimizations
if report["cache_stats"]["hit_rate"] < 0.5:
    optimizer.cache.invalidate()  # Clear stale cache

# Optimize concurrency
optimal = optimizer.executor.optimize_concurrency()
```

### Debug Commands

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Test individual components
python -m lib.security_manager  # Test security
python -m lib.performance_optimizer  # Test performance

# Validate configuration
python scripts/validate_config.py

# Check system health
curl http://localhost:8000/api/v1/monitoring/health | jq
```

---

## Best Practices

### 1. Requirements Writing

**DO:**
- Be specific about features
- Include technical constraints
- Define success metrics
- Specify integrations upfront

**DON'T:**
- Use vague descriptions
- Overload with features
- Skip constraint definition

### 2. Workflow Organization

```yaml
# Good practice: Modular requirements
features:
  auth:
    - "JWT-based authentication"
    - "OAuth2 social login"
  dashboard:
    - "Real-time metrics"
    - "Customizable widgets"
```

### 3. Testing Strategy

```bash
# Always test in mock mode first
python orchestrate_enhanced.py --requirements=req.yaml --mock

# Validate before production
python tests/e2e_phase4/run_phase4_tests.py --scenario your_type

# Monitor actively
python session_cli.py monitor --alert-on-error
```

### 4. Performance Optimization

- Use caching for repeated workflows
- Batch API calls when possible
- Monitor memory usage
- Optimize agent selection

### 5. Security Best Practices

- Rotate API keys monthly
- Use least-privilege access
- Enable audit logging
- Sanitize all inputs
- Monitor for suspicious activity

---

## Security Guidelines

### API Key Security

```bash
# Never commit API keys
echo "ANTHROPIC_API_KEY=*" >> .gitignore

# Use environment variables
export ANTHROPIC_API_KEY=$(vault read -field=key secret/anthropic)

# Rotate regularly
python scripts/rotate_keys.py --all --notify
```

### Input Validation

```python
from lib.security_manager import InputSanitizer

sanitizer = InputSanitizer()

# Always sanitize user input
clean_input = sanitizer.sanitize_string(user_input)
clean_path = sanitizer.sanitize_path(file_path)
clean_json = sanitizer.validate_json(json_data)
```

### Audit Logging

```python
from lib.security_manager import AuditLogger

audit = AuditLogger()

# Log all critical operations
audit.log_event(
    event_type=SecurityEvent.DATA_ACCESS,
    user_id=current_user.id,
    resource="workflows",
    action="execute",
    success=True
)

# Query audit logs
suspicious = audit.query_logs(
    min_risk_score=70,
    event_type=SecurityEvent.UNAUTHORIZED_ACCESS
)
```

---

## Performance Tuning

### Cache Configuration

```python
# Optimize cache settings
CACHE_MAX_MEMORY_MB=1000
CACHE_TTL_SECONDS=7200
REDIS_URL=redis://localhost:6379/0
```

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_workflows_created ON workflows(created_at);

-- Optimize connection pool
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
```

### Concurrent Execution

```python
# Tune based on system resources
from lib.performance_optimizer import ConcurrentExecutor

executor = ConcurrentExecutor(
    max_workers=8,  # 2x CPU cores for I/O
    max_memory_gb=4.0
)

# Get optimization recommendations
optimal = executor.optimize_concurrency()
print(f"Recommended workers: {optimal['optimal_thread_workers']}")
```

### Memory Management

```python
# Configure garbage collection
from lib.performance_optimizer import MemoryManager

mem_mgr = MemoryManager(
    target_memory_mb=2000,
    gc_threshold=0.8
)

# Monitor memory
stats = mem_mgr.get_memory_stats()
if stats["percent_of_target"] > 90:
    gc.collect()  # Force collection
```

---

## Appendix

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Claude API key | Required |
| LOG_LEVEL | Logging level | INFO |
| MAX_PARALLEL_AGENTS | Max concurrent agents | 3 |
| CACHE_TTL_SECONDS | Cache expiration | 3600 |
| RATE_LIMIT_PER_MINUTE | API rate limit | 60 |
| MEMORY_LIMIT_MB | Memory limit | 2000 |
| DATABASE_URL | PostgreSQL URL | sqlite:///local.db |
| REDIS_URL | Redis URL | redis://localhost:6379 |

### Command Reference

| Command | Description |
|---------|-------------|
| orchestrate_enhanced.py | Main workflow orchestrator |
| session_cli.py | Session management CLI |
| sfa/*.py | Standalone agent executors |
| tests/test_agents.py | Agent test suite |
| scripts/deploy.sh | Deployment script |
| scripts/backup.sh | Backup script |

### Support & Resources

- **Documentation**: `/docs` directory
- **API Reference**: `/docs/api/openapi.yaml`
- **Examples**: `/examples` directory
- **Issues**: GitHub Issues
- **Community**: Discord/Slack channel

---

*Last Updated: December 2024 | Version: 1.0.0*