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

### Performance Standards
- **Web Apps**: <3s initial load, <200ms API responses
- **Mobile Apps**: <2s app launch, <100ms UI interactions
- **APIs**: <100ms for simple queries, <500ms for complex operations
- **Database**: Index all foreign keys and frequently queried columns
- **Memory**: Implement proper garbage collection and memory management

### Testing Requirements
- **Unit Tests**: 90%+ coverage for business logic
- **Integration Tests**: All API endpoints and database operations
- **E2E Tests**: Critical user journeys and payment flows
- **Security Tests**: Authentication, authorization, input validation
- **Performance Tests**: Load testing for expected traffic + 3x

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