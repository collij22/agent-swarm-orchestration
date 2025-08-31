# CLAUDE.md - Global Development Standards

This file provides guidance to Claude Code and all AI agents when working with code in this repository.

## Project Status

This repository contains an optimized 15-agent swarm for rapid technical development and business projects.

## 🎯 Core Development Principles

### Code Quality Standards (SOLID + DRY + KISS)
- **Single Responsibility**: Each class/function has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Derived classes must be substitutable for base classes
- **Interface Segregation**: Many client-specific interfaces vs one general interface
- **Dependency Inversion**: Depend on abstractions, not concretions
- **DRY**: Don't Repeat Yourself - extract common patterns
- **KISS**: Keep It Simple, Stupid - prefer readable over clever

### Security Requirements (Non-Negotiable)
- Never commit secrets, API keys, or credentials to version control
- All user inputs must be validated and sanitized
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Enable HTTPS and secure headers in production
- Regular dependency updates and security audits
- **Phase 5 Enhancements**:
  - API key rotation every 90 days with encrypted storage (Fernet)
  - Role-Based Access Control with 4 levels (Admin, Developer, Viewer, Guest)
  - Rate limiting: 100 requests/minute per user (sliding window)
  - Input sanitization for XSS, SQL injection, and path traversal
  - Comprehensive audit logging with risk scoring (0-100)
  - Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options

### Performance Standards
- **Web Apps**: <3s initial load, <200ms API responses
- **Mobile Apps**: <2s app launch, <100ms UI interactions
- **APIs**: <100ms for simple queries, <500ms for complex operations
- **Database**: Index all foreign keys and frequently queried columns
- **Memory**: Implement proper garbage collection and memory management
- **Phase 5 Enhancements**:
  - Multi-tier caching: Memory (LRU, 500MB) → Redis (1GB) → File (10GB)
  - Cache TTL: 1 hour default, 24 hours for static content
  - Database connection pooling: 20 connections max, 5 min
  - Query optimization: Automatic EXPLAIN analysis and index suggestions
  - Concurrent execution: ThreadPool (10 workers) for I/O, ProcessPool (4) for CPU
  - Memory monitoring: Warning at 512MB, critical at 1GB usage
  - API batching: Coalesce requests within 100ms window, max 50 per batch
  - Garbage collection: Force collection when memory > 80% threshold

### Testing Requirements
- **Unit Tests**: 90%+ coverage for business logic
- **Integration Tests**: All API endpoints and database operations
- **E2E Tests**: Critical user journeys and payment flows
- **Security Tests**: Authentication, authorization, input validation
- **Performance Tests**: Load testing for expected traffic + 3x
- **Mock Testing**: Enhanced mock mode with realistic file creation and requirement tracking

## 🛠️ Default Technology Stack

### Frontend (Unless Project Specifies Otherwise)
```yaml
framework: "React + TypeScript"
styling: "Tailwind CSS"
state_management: "Zustand/React Query"
build_tool: "Vite"
testing: "Jest + Testing Library"
linting: "ESLint + Prettier"
```

### Backend (Unless Project Specifies Otherwise)
```yaml
language: "Python 3.11+ or Node.js 18+"
framework: "FastAPI or Express + TypeScript"
database: "PostgreSQL 15+"
cache: "Redis 7+"
auth: "JWT with refresh tokens"
api_docs: "OpenAPI/Swagger"
validation: "Pydantic or Joi"
```

### Infrastructure (Unless Project Specifies Otherwise)
```yaml
cloud: "AWS or Vercel"
containers: "Docker + Docker Compose"
ci_cd: "GitHub Actions"
monitoring: "Sentry + DataDog/Vercel Analytics"
cdn: "CloudFront or Vercel Edge"
ssl: "Let's Encrypt or CloudFlare"
```

### AI/ML (Unless Project Specifies Otherwise)
```yaml
llm_provider: "OpenAI or Anthropic"
vector_db: "Pinecone or Chroma"
ml_framework: "scikit-learn or PyTorch"
serving: "FastAPI or Modal"
monitoring: "LangSmith or W&B"
```

## 📁 Project Structure Standards

### Web Application Structure
```
project/
├── frontend/          # React/Next.js application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # Helper functions
│   │   └── types/         # TypeScript definitions
│   ├── public/            # Static assets
│   └── tests/             # Frontend tests
├── backend/           # API server
│   ├── src/
│   │   ├── routes/        # API endpoints
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   ├── middleware/    # Request middleware
│   │   └── utils/         # Helper functions
│   ├── migrations/        # Database migrations
│   └── tests/             # Backend tests
├── docs/              # Project documentation
├── scripts/           # Build and deployment scripts
└── docker-compose.yml    # Local development setup
```

### API Design Standards
```yaml
versioning: "/api/v1/"
naming: "kebab-case for endpoints"
methods: "RESTful (GET, POST, PUT, DELETE)"
responses: "Consistent JSON structure with status, data, error fields"
errors: "HTTP status codes + detailed error messages"
pagination: "Cursor-based for performance"
authentication: "Bearer tokens in Authorization header"
```

## 🚀 Development Workflow

### Git Standards
- **Branching**: `main` (production), `develop` (staging), `feature/*` (development)
- **Commits**: Conventional commits (feat, fix, docs, style, refactor, test, chore)
- **Pull Requests**: Required for all changes, 1 approval minimum
- **CI/CD**: All tests must pass before merge

### Error Handling Patterns
```python
# Python/FastAPI
from typing import Optional
from fastapi import HTTPException

def handle_user_creation(user_data: dict) -> dict:
    try:
        # Business logic here
        return {"status": "success", "data": user}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Database error")
```

```typescript
// TypeScript/React
interface APIResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
}

const handleApiCall = async <T>(
  apiCall: Promise<T>
): Promise<APIResponse<T>> => {
  try {
    const data = await apiCall;
    return { status: 'success', data };
  } catch (error) {
    return { status: 'error', error: error.message };
  }
};
```

### Logging Standards
```python
import logging

# Structured logging with context
logger = logging.getLogger(__name__)

def process_payment(user_id: str, amount: float):
    logger.info(
        "Processing payment",
        extra={"user_id": user_id, "amount": amount}
    )
    # Never log sensitive data (credit card numbers, passwords, etc.)
```

## 📊 Monitoring & Analytics

### Required Metrics
- **Performance**: Response times, throughput, error rates
- **Business**: User engagement, conversion rates, revenue
- **Technical**: CPU/memory usage, database performance, API calls
- **Security**: Failed login attempts, suspicious activity, errors

### Alert Thresholds
- **Critical**: >5% error rate, >5s response time, >80% resource usage
- **Warning**: >2% error rate, >3s response time, >60% resource usage
- **Info**: Unusual traffic patterns, new user registrations, deployments

## 🔧 Development Environment

- **Platform**: Windows (win32)
- **Working Directory**: C:\AI projects\1test
- **Package Manager**: UV for Python, npm/yarn for Node.js
- **IDE**: VS Code with recommended extensions
- **Database**: Local PostgreSQL + Redis via Docker

## 📝 Documentation Requirements

### Code Documentation
- **Functions**: Docstrings for all public functions
- **APIs**: OpenAPI/Swagger specifications
- **Database**: Schema documentation and ER diagrams
- **README**: Setup instructions, usage examples, deployment guide

### Project Documentation
- **Architecture**: High-level system design
- **APIs**: Endpoint documentation with examples
- **Database**: Schema and relationships
- **Deployment**: Step-by-step deployment instructions
- **Phase 5 Documentation**:
  - **OpenAPI Specification**: Complete API docs at `docs/api/openapi.yaml`
  - **User Guide**: Comprehensive guide at `docs/USER_GUIDE.md` with Quick Start, Developer Guide, Admin Guide
  - **Security Documentation**: RBAC roles, API key management, audit log format
  - **Performance Guide**: Caching strategies, optimization techniques, monitoring
  - **Troubleshooting Guide**: Common issues, error codes, debugging steps
  - **Integration Examples**: Code samples for all major languages (Python, JS, Go, Java)

## 🪝 Hook System Standards

### Pre-Execution Validation
- Security checks on all file operations
- Rate limiting enforcement (100 calls/min default)
- Cost estimation before expensive operations
- Parameter validation and enrichment

### Post-Execution Processing
- Result caching for expensive operations (24hr TTL)
- Metrics collection for all tool calls
- Error recovery suggestions
- Side effect tracking

### System Protection
- Memory monitoring (512MB warning, 1GB critical)
- Budget enforcement ($10/hr, $100/day)
- Automatic checkpoints for recovery
- Progress tracking with ETA

## 📊 Session Management Standards

### Session Lifecycle
- Automatic session creation with unique IDs
- Checkpoint saves at critical points
- Session status tracking (running/completed/failed)
- Archive old sessions after 30 days

### Performance Standards
- Track CPU and memory usage
- Monitor API call rates
- Detect performance bottlenecks
- Generate optimization suggestions

### Analysis Requirements
- Error pattern detection
- Reasoning quality assessment
- Cross-session metrics aggregation
- Agent performance rankings
- Human-readable summary generation

## 🎯 Enhanced Orchestration Standards (Section 8)

### Adaptive Workflow Requirements
- **Dynamic Agent Selection**: Automatically assign optimal agents based on requirement analysis
- **Parallel Execution**: Execute independent tasks in parallel (max 3 agents default)
- **Dependency Management**: Build and respect requirement dependency graphs
- **Priority Scheduling**: High-priority requirements (security, core) execute first

### Requirement Tracking Standards
- **Structured IDs**: Use REQ-001, TECH-001 format for all requirements
- **Status Granularity**: Track pending → in_progress → completed/failed/blocked
- **Completion Metrics**: Precise 0-100% completion tracking for each requirement
- **Agent Mapping**: Clear visibility of which agents handle which requirements

### Error Recovery Protocol
- **Exponential Backoff**: Retry delays of 5s, 15s, 30s for failed agents
- **Retry Limits**: High-priority agents get 3 attempts, others get 2
- **Partial Completion**: System continues with successful agents when some fail
- **Manual Intervention**: Offer user intervention when failure rate exceeds 50%

### Real-Time Progress Standards
- **WebSocket Streaming**: Live progress updates to dashboard within 100ms
- **Event Broadcasting**: Workflow started, agent completed, errors, interventions
- **Progress Metrics**: Real-time completion percentages and ETA calculations
- **Historical Tracking**: Maintain 1000-event history for analysis

### Enhanced Checkpoint Requirements
- **Comprehensive State**: Save requirements, agent plans, progress, dependencies
- **Automatic Frequency**: Create checkpoints every 3 completed agents
- **Resume Capability**: Full workflow restoration from any checkpoint
- **Error Context**: Preserve error messages and retry counts for debugging

## 🖥️ Web Dashboard Standards

### Dashboard Access
- **Primary URL**: http://localhost:5173 (Frontend)
- **API Docs**: http://localhost:8000/docs (Backend)
- **WebSocket**: ws://localhost:8000/ws (Real-time)

### Monitoring Requirements
- Real-time performance metrics must update within 5 seconds
- Session data should be accessible within 1 second of completion
- Error events must trigger immediate dashboard notifications
- All dashboard views must load within 2 seconds

### Dashboard Development
- Follow React + TypeScript standards for frontend components
- Use Zustand for state management consistency
- Implement WebSocket reconnection logic for reliability
- Maintain responsive design for all screen sizes
- Support dark/light theme preferences

## 📝 Enhanced Logging Standards

### Human-Readable Logging
The system now generates concise markdown summaries alongside detailed JSON logs:
- **File Pattern**: `session_<id>_<timestamp>_human.md`
- **Target Size**: 
  - Concise: 100-200 lines (5-minute review)
  - Detailed: 300-500 lines (10-minute review)
  - Verbose: 500+ lines (full detail)
- **Real-time**: Updates as execution progresses
- **Review Time**: 5 minutes vs 30+ for JSON logs

### Configuration Options
```yaml
logging:
  human_readable: true      # Enable markdown summaries (default: true)
  summary_level: "concise"  # Options: concise|detailed|verbose
  track_artifacts: true     # Log file operations
  track_handoffs: true      # Log agent communication
```

### CLI Usage
```bash
# Enable human-readable logs (default)
python orchestrate_enhanced.py --requirements=requirements.yaml --human-log

# Disable human logs for minimal output
python orchestrate_enhanced.py --requirements=requirements.yaml --no-human-log

# Verbose human logs with all details
python orchestrate_enhanced.py --requirements=requirements.yaml --summary-level=verbose
```

### Summary Contents
The human-readable log captures:
- **Agent Execution Flow**: Start/end times, status, requirements handled
- **Key Outputs**: Files created, important decisions, artifacts produced
- **Error Resolution**: Problems encountered and how they were resolved
- **Agent Handoffs**: Communication between agents, shared artifacts
- **Performance Metrics**: Duration, success rates, resource usage

### Example Output
```markdown
# Agent Swarm Execution Summary
Session: 715a6116-b285-45ec-9d16-0ffa0d4a7b1d

## Agent Execution Flow

### api-integrator [17:40:04 - 17:41:12] [OK]
Requirements: PORTFOLIO-001, DEVTOOLS-001
Key Outputs:
- Created: integrations/config.json
- Created: .env.example
Decision: OAuth2 for GitHub, API key for OpenAI
-> Handoff to: rapid-builder

### rapid-builder [17:41:15 - 17:45:30] [OK]
Files Created: 12 files (main.py, database.py, config.json, ...)
-> Handoff to: database-expert, frontend-specialist
```

## 🤝 Agent Communication Protocol

### Between Agents
- Use Task tool for agent-to-agent coordination
- Share context through structured data formats
- Maintain clear handoff protocols
- Document decisions and rationale

### With Humans
- Provide clear status updates
- Ask specific questions when blocked
- Document all changes and reasoning
- Maintain professional, helpful communication

---

## Important Instruction Reminders

- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested
- All agents must adhere to these standards unless project requirements specify otherwise

## 🚨 Critical Implementation Standards

### IMPORTANT: Actual File Creation Requirements
- **ALWAYS create actual source files** with working code, not just scaffolding
- **NEVER leave placeholder imports** (e.g., main.tsx must exist if imported)
- **ALWAYS include entry point files** (index.tsx, main.tsx, App.tsx for React)
- **ALWAYS create package-lock.json** after npm install for reproducible builds

### IMPORTANT: Data Seeding Requirements  
- **ALWAYS create at least 3 dummy entries** for each resource type
- **Products**: Include name, description, price, stock, and image URLs
- **Users**: Create test user with credentials (email: test@example.com, password: password123)
- **Orders**: Include at least 1 completed order for testing

### IMPORTANT: Field Consistency Standards
- **ALWAYS match field names** between frontend and backend exactly
- **Use consistent date fields**: created_at, updated_at (not order_date, etc.)
- **Verify serialization**: Test all API endpoints return proper JSON

## 🔌 MCP (Model Context Protocol) Standards

### MCP Tool Usage Requirements
- **Prioritize MCP Tools**: Always use MCP tools over traditional methods when available
- **Documentation First**: Use mcp_ref_search before implementing new features
- **Security Scanning**: Run mcp_semgrep_scan on all code before deployment
- **Visual Validation**: Use mcp_browser_screenshot for UI verification
- **Conditional Loading**: MCPs activate only when beneficial for the task

### MCP Workflow Integration (Phase 3)
- **Workflow-Driven**: MCPs automatically selected based on workflow patterns
- **6 Specialized Workflows**: Payment, research, prototype, Vercel, data, API testing
- **Dynamic Activation**: Agents receive MCPs based on workflow phase requirements
- **Intelligent Selection**: Project type and requirements determine workflow choice

### Available Workflow Patterns
```yaml
payment_enabled_webapp:
  triggers: [payment, subscription, billing, e-commerce]
  mcps: [stripe, fetch, sqlite, vercel]
  
research_heavy_project:
  triggers: [research, analysis, competitor]
  mcps: [firecrawl, brave_search, quick_data]
  
rapid_prototype:
  triggers: [mvp, prototype, poc, demo]
  mcps: [sqlite, fetch, vercel]
  
vercel_deployment:
  triggers: [vercel, nextjs, serverless]
  mcps: [vercel, fetch]
  
data_processing_pipeline:
  triggers: [data, analytics, csv, etl]
  mcps: [quick_data, sqlite]
  
api_testing_focused:
  triggers: [api, webhook, integration]
  mcps: [fetch, brave_search]
```

### MCP Cost Optimization
- **Token Savings**: Ref MCP saves ~60% tokens per documentation fetch
- **Cost Per Step**: Average savings of $0.09 per implementation step
- **Batch Operations**: Group related MCP calls for efficiency
- **Cache Utilization**: MCP includes 15-minute cache for repeated queries
- **Conditional Usage**: MCPs only load when workflow requires them

### MCP Integration Points
```yaml
# Phase 1: Core MCPs (Always Available)
security_scanning:
  tool: mcp_semgrep_scan
  rules: [security, owasp, pci_dss, gdpr]
  frequency: "Before each deployment"

documentation_fetching:
  tool: mcp_ref_search
  savings: "60% token reduction"
  technologies: [react, fastapi, django, postgresql]

visual_testing:
  tool: mcp_browser_screenshot
  use_cases: ["UI validation", "Deployment verification", "Visual regression"]

# Phase 2-3: Conditional MCPs (Workflow-Based)
payment_processing:
  tool: mcp_stripe
  activation: "When payment features required"
  
data_operations:
  tool: mcp_quick_data
  activation: "For CSV/JSON processing, analytics"
  
web_scraping:
  tool: mcp_firecrawl
  activation: "For research and competitor analysis"
```

### MCP Performance Standards
- **Response Time**: MCP calls should complete within 5 seconds
- **Fallback Strategy**: Use general knowledge if MCP unavailable
- **Error Handling**: Log MCP failures but continue with alternatives
- **Metrics Tracking**: Monitor token savings and cost reduction
- **Workflow Efficiency**: Track MCP utilization per workflow pattern

### MCP Agent Enhancement Summary
- **All 15 Agents**: Support conditional MCP loading based on workflow
- **Security Agents**: Enhanced with Semgrep MCP for automated vulnerability scanning
- **Development Agents**: Enhanced with Ref MCP for accurate documentation (60% token savings)
- **Quality Agents**: Enhanced with Browser MCP for visual testing and validation
- **Specialized MCPs**: 7 additional MCPs activate conditionally based on project needs

## 🧪 Enhanced Testing Standards

### Phase 1: Core Integration Standards
- **Requirement Tracking**: All agents must track assigned requirements with 0-100% completion
- **Validation Checkpoints**: Pre/post execution validation with retry logic
- **Agent Output Validation**: Agent-specific validation rules with retry suggestions
- **Integration Testing**: Test Phase 1 components (validation_orchestrator, requirement_tracker)

### Mock Mode Testing (Section 7 - ENHANCED December 2024)
- **Environment Variable**: Set `MOCK_MODE=true` to enable mock mode globally
- **MockAnthropicEnhancedRunner**: Full replacement for AnthropicAgentRunner with tool execution
- **EnhancedMockAnthropicClient**: Realistic agent responses with requirement tracking
- **FileSystemSimulator**: Creates actual files in temp directories for validation
- **Tool Simulation**: 15+ tools including write_file, read_file, dependency_check, run_tests
- **Failure Simulation**: Configurable 5% failure rate for robust error handling tests
- **Progress Monitoring**: Real-time 0-100% completion tracking per requirement
- **Cross-Platform**: Windows/Linux/Mac compatible with encoding fixes

### Testing Commands
```bash
# Phase 5 Validation Suite (NEW - December 2024)
cd tests/phase5_validation
set MOCK_MODE=true  # Windows
export MOCK_MODE=true  # Linux/Mac

# Run all validation tests
python run_tests.py --all

# Run specific test scenario
python run_tests.py --test ecommerce --verbose

# Quick validation
simple_test.bat  # Windows
python test_mock_enhanced.py  # Cross-platform

# Debug orchestrator with mock mode
python debug_orchestrator.py

# Test Phase 1 integration
python tests/test_phase1_integration.py

# Enhanced mock mode with file creation (recommended)
python tests/test_agents.py --mode mock --enhanced

# Traditional mock mode (basic simulation)
python tests/test_agents.py --mode mock

# Enhanced mock mode tests only
python tests/test_mock_mode_enhanced.py

# Direct enhanced mock client demonstration
python lib/mock_anthropic_enhanced.py
```

### Mock Testing Benefits
- **Zero API Costs**: Complete testing without API charges
- **Realistic Behavior**: Actual file creation and validation
- **Requirement Tracking**: Precise completion percentages (0-100%)
- **Controlled Failures**: Test error handling with configurable failure rates
- **Comprehensive Metrics**: API calls, costs, files created, progress tracking

## 🔍 Mandatory Testing Protocol

### Before Marking Any Task Complete:
1. **Build Test**: Frontend and backend must build without errors
2. **Start Test**: All services must start successfully
3. **API Test**: All endpoints must return valid responses
4. **Auth Test**: User can register, login, and see protected content
5. **Data Test**: At least one full CRUD cycle must work
6. **Docker Test**: docker-compose up must bring up all services

### Minimum Viable Deliverable:
- User can access the application
- At least one dummy entry is visible
- Basic navigation works
- No blank pages or console errors
- Docker containers stay running for 5+ minutes

### IMPORTANT: Mock Mode Must Still Create Real Files
- Even in mock mode, create actual source files
- Validate file structure matches production requirements
- Test Docker builds even in mock mode
- Ensure seed data is created regardless of mode