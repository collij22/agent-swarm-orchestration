# TaskManagerAPI System Architecture

## Overview
The TaskManagerAPI is an AI-enhanced task management system built with FastAPI, React, and OpenAI integration. This document outlines the system architecture, component interactions, and technical decisions.

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│  React Frontend (Vite + Tailwind CSS)                               │
│  - Task Management UI                                               │
│  - Authentication Forms                                             │
│  - Real-time Updates                                               │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS/REST
┌───────────────────────────┴─────────────────────────────────────────┐
│                          API Gateway                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Nginx Reverse Proxy                                                │
│  - Rate Limiting                                                    │
│  - SSL Termination                                                 │
│  - Load Balancing                                                  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                      Application Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                                    │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐     │
│  │   Auth Service  │  │ Task Service │  │ Category Service  │     │
│  │  - JWT Tokens   │  │ - CRUD Ops   │  │ - Management      │     │
│  │  - User Mgmt    │  │ - Validation │  │ - Defaults        │     │
│  └─────────────────┘  └──────────────┘  └───────────────────┘     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                    AI Service Layer                      │      │
│  │  - Task Categorization                                  │      │
│  │  - Priority Scoring                                     │      │
│  │  - OpenAI Integration                                   │      │
│  └─────────────────────────────────────────────────────────┘      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                       Data Layer                                     │
├─────────────────────────────────────────────────────────────────────┤
│  SQLite Database                                                    │
│  - Users Table                                                      │
│  - Tasks Table                                                      │
│  - Categories Table                                                 │
│  - Indexes for Performance                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Authentication Flow**
   ```
   Client  ->  API Gateway  ->  Auth Service  ->  JWT Generation  ->  Client Storage
   ```

2. **Task Creation Flow**
   ```
   Client  ->  API Gateway  ->  Task Service  ->  AI Service (Categorization)  ->  Database  ->  Response
   ```

3. **AI Processing Flow**
   ```
   Task Service  ->  AI Service  ->  OpenAI API  ->  Response Processing  ->  Database Update
   ```

## Database Design

### Entity Relationship Diagram

```sql
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Users       │     │     Tasks       │     │   Categories    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (UUID) PK    │     │ id (UUID) PK    │     │ id (UUID) PK    │
│ username        │     │ title           │     │ name            │
│ email           │     │ description     │     │ description     │
│ password_hash   │     │ category_id FK  │     │ color           │
│ created_at      │     │ priority        │     │ created_at      │
│ updated_at      │     │ status          │     └─────────────────┘
└─────────────────┘     │ user_id FK      │              │
         │              │ created_at      │              │
         │              │ updated_at      │              │
         │              └─────────────────┘              │
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                        1:N              N:1
```

### Key Indexes and Constraints

```sql
-- Primary Keys
CREATE UNIQUE INDEX idx_users_id ON users(id);
CREATE UNIQUE INDEX idx_tasks_id ON tasks(id);
CREATE UNIQUE INDEX idx_categories_id ON categories(id);

-- Foreign Key Constraints
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_category_id ON tasks(category_id);

-- Performance Indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_username ON users(username);

-- Composite Indexes for Common Queries
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_priority ON tasks(user_id, priority DESC);
```

### Migration Strategy

1. **Initial Schema Creation** (V1.0.0)
   - Create all base tables with constraints
   - Insert default categories
   - Create indexes

2. **Future Migrations**
   - Use Alembic for version control
   - Always include rollback scripts
   - Test migrations on staging first

## API Structure

### Endpoint Definitions

#### Authentication Endpoints

```yaml
POST /api/v1/auth/register
  Request:
    {
      "username": "string",
      "email": "string",
      "password": "string"
    }
  Response:
    {
      "access_token": "string",
      "refresh_token": "string",
      "token_type": "bearer"
    }

POST /api/v1/auth/login
  Request:
    {
      "username": "string",
      "password": "string"
    }
  Response:
    {
      "access_token": "string",
      "refresh_token": "string",
      "token_type": "bearer"
    }

POST /api/v1/auth/refresh
  Request:
    {
      "refresh_token": "string"
    }
  Response:
    {
      "access_token": "string",
      "token_type": "bearer"
    }
```

#### Task Endpoints

```yaml
GET /api/v1/tasks
  Query Parameters:
    - status: enum[todo, in_progress, done]
    - category_id: UUID
    - priority: integer
    - limit: integer (default: 20)
    - offset: integer (default: 0)
  Response:
    {
      "items": [Task],
      "total": integer,
      "limit": integer,
      "offset": integer
    }

POST /api/v1/tasks
  Request:
    {
      "title": "string",
      "description": "string",
      "auto_categorize": boolean (default: true),
      "auto_prioritize": boolean (default: true)
    }
  Response:
    {
      "id": "UUID",
      "title": "string",
      "description": "string",
      "category": "string",
      "priority": integer,
      "status": "todo",
      "created_at": "timestamp"
    }

GET /api/v1/tasks/{id}
PUT /api/v1/tasks/{id}
DELETE /api/v1/tasks/{id}

POST /api/v1/tasks/{id}/categorize
  Response:
    {
      "category": "string",
      "confidence": float
    }

POST /api/v1/tasks/{id}/prioritize
  Response:
    {
      "priority": integer,
      "reasoning": "string"
    }
```

### Authentication Flow

```
1. User Registration/Login
    ->  Validate credentials
    ->  Generate JWT tokens (access + refresh)
    ->  Return tokens to client

2. Authenticated Requests
    ->  Extract JWT from Authorization header
    ->  Validate token signature and expiry
    ->  Extract user_id from token
    ->  Process request with user context

3. Token Refresh
    ->  Validate refresh token
    ->  Generate new access token
    ->  Optionally rotate refresh token
```

### Rate Limiting Strategy

```python
# Per-endpoint rate limits
rate_limits = {
    "/api/v1/auth/*": "5 requests per minute",
    "/api/v1/tasks": "100 requests per minute",
    "/api/v1/tasks/*/categorize": "10 requests per minute",
    "/api/v1/tasks/*/prioritize": "10 requests per minute",
    "default": "60 requests per minute"
}

# Implementation using slowapi
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

## Technology Recommendations

### Backend Stack
- **Framework**: FastAPI 0.104+
  - Rationale: Automatic OpenAPI docs, async support, type hints
- **Database**: SQLite with SQLAlchemy ORM
  - Rationale: Zero configuration, sufficient for MVP, easy migration path
- **Authentication**: python-jose for JWT
  - Rationale: Industry standard, secure, stateless
- **AI Integration**: OpenAI Python SDK
  - Rationale: Official SDK, reliable, good documentation

### Frontend Stack
- **Framework**: React 18+ with TypeScript
  - Rationale: Type safety, large ecosystem, team familiarity
- **Build Tool**: Vite
  - Rationale: Fast HMR, optimized builds, ESM support
- **Styling**: Tailwind CSS
  - Rationale: Rapid development, consistent design, small bundle
- **State Management**: Zustand
  - Rationale: Simple API, TypeScript support, minimal boilerplate

### Infrastructure
- **Containerization**: Docker + docker-compose
  - Rationale: Easy deployment, consistent environments
- **Reverse Proxy**: Nginx
  - Rationale: Production-ready, excellent performance, SSL support
- **Monitoring**: Prometheus + Grafana (future)
  - Rationale: Open source, comprehensive metrics

### Development Tools
- **API Testing**: Pytest + httpx
  - Rationale: Async support, fixtures, good FastAPI integration
- **Code Quality**: Black + Ruff + mypy
  - Rationale: Consistent formatting, fast linting, type checking
- **Documentation**: MkDocs
  - Rationale: Markdown-based, easy to maintain

## Security Considerations

1. **Authentication & Authorization**
   - JWT tokens with short expiry (15 minutes)
   - Refresh tokens with longer expiry (7 days)
   - Role-based access control (future enhancement)

2. **Input Validation**
   - Pydantic models for all inputs
   - SQL injection prevention via ORM
   - XSS prevention in React

3. **API Security**
   - CORS configuration
   - Rate limiting per endpoint
   - Security headers (HSTS, CSP, etc.)

4. **Data Protection**
   - Bcrypt for password hashing
   - Environment variables for secrets
   - HTTPS only in production

## Performance Optimization

1. **Database**
   - Connection pooling
   - Prepared statements
   - Query optimization with indexes

2. **Caching Strategy**
   - In-memory cache for categories
   - Redis for session data (future)
   - HTTP caching headers

3. **API Optimization**
   - Async endpoints
   - Pagination for list endpoints
   - Selective field returns

## Development Timeline Estimate

### Day 1 (8 hours)
- **Hours 1-2**: Project setup, database schema, Docker configuration
- **Hours 3-4**: Authentication system and JWT implementation
- **Hours 5-6**: Task CRUD endpoints and AI integration
- **Hours 7-8**: React frontend, testing, and documentation

This aggressive timeline is achievable with:
- Boilerplate code generation
- Parallel frontend/backend development
- Focus on MVP features only
- Extensive use of libraries/frameworks

## Monitoring and Observability

1. **Application Metrics**
   - Request count and latency
   - Error rates by endpoint
   - AI API usage and costs

2. **Business Metrics**
   - Tasks created per user
   - AI categorization accuracy
   - User engagement rates

3. **Infrastructure Metrics**
   - CPU and memory usage
   - Database query performance
   - Container health checks