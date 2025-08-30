# TaskManagerAPI System Architecture

## Overview
TaskManagerAPI is a monolithic web application with AI-enhanced task management capabilities, designed for rapid MVP development within a 1-day timeline.

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Container                          │
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────────────────┐   │
│  │   React Frontend│         │    FastAPI Backend          │   │
│  │   (Vite + TW)   │ ──────> │                             │   │
│  │   Port: 3000    │  HTTP   │  ┌───────────────────────┐  │   │
│  └─────────────────┘         │  │   API Routes          │  │   │
│                              │  │  - Auth               │  │   │
│                              │  │  - Tasks              │  │   │
│                              │  │  - Categories         │  │   │
│                              │  └───────────────────────┘  │   │
│                              │                             │   │
│                              │  ┌───────────────────────┐  │   │
│                              │  │   Business Logic      │  │   │
│                              │  │  - Task Service       │  │   │
│                              │  │  - Auth Service       │  │   │
│                              │  │  - AI Service         │  │   │
│                              │  └───────────────────────┘  │   │
│                              │                             │   │
│                              │  ┌───────────────────────┐  │   │
│                              │  │   Data Access Layer   │  │   │
│                              │  │  - SQLAlchemy ORM     │  │   │
│                              │  │  - Repository Pattern │  │   │
│                              │  └───────────────────────┘  │   │
│                              │            │                │   │
│                              │            ▼                │   │
│                              │  ┌───────────────────────┐  │   │
│                              │  │   SQLite Database     │  │   │
│                              │  │   /app/data/tasks.db  │  │   │
│                              │  └───────────────────────┘  │   │
│                              │                             │   │
│                              │  Port: 8000                 │   │
│                              └─────────────────────────────┘   │
│                                           │                     │
│                                           │ HTTPS               │
│                                           ▼                     │
│                              ┌─────────────────────────────┐   │
│                              │    OpenAI API               │   │
│                              │   (External Service)        │   │
│                              └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request Flow**:
   - User interacts with React frontend
   - Frontend sends API request to FastAPI backend
   - Backend validates JWT token (for protected routes)
   - Business logic processes request
   - Data layer interacts with SQLite database
   - Response returned to frontend

2. **AI Processing Flow**:
   - Task created/updated via API
   - Background task triggered for AI processing
   - AI Service calls OpenAI API
   - Results stored in database
   - Frontend polls or receives update via response

3. **Authentication Flow**:
   - User registers/logs in via frontend
   - Backend validates credentials
   - JWT token generated and returned
   - Token included in subsequent requests
   - Token validated on each protected route

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│      User       │       │      Task       │       │    Category     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (UUID) PK    │───┐   │ id (UUID) PK    │   ┌───│ id (UUID) PK    │
│ username        │   │   │ title           │   │   │ name            │
│ email           │   │   │ description     │   │   │ description     │
│ password_hash   │   └──<│ user_id FK      │   │   │ color           │
│ created_at      │       │ category_id FK  │>──┘   │ created_at      │
│ updated_at      │       │ priority        │       └─────────────────┘
└─────────────────┘       │ status          │
                          │ created_at      │
                          │ updated_at      │
                          │ ai_processed    │
                          └─────────────────┘
```

### Key Indexes and Constraints

```sql
-- Primary Keys
CREATE UNIQUE INDEX idx_users_id ON users(id);
CREATE UNIQUE INDEX idx_tasks_id ON tasks(id);
CREATE UNIQUE INDEX idx_categories_id ON categories(id);

-- Foreign Keys
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_category_id ON tasks(category_id);

-- Performance Indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_username ON users(username);

-- Constraints
ALTER TABLE tasks ADD CONSTRAINT chk_priority CHECK (priority >= 1 AND priority <= 5);
ALTER TABLE tasks ADD CONSTRAINT chk_status CHECK (status IN ('todo', 'in_progress', 'done'));
```

### Migration Strategy

1. Use Alembic for database migrations
2. Initial migration creates all tables with constraints
3. Seed data includes default categories
4. Version control all migration files

## API Structure

### RESTful Endpoint Definitions

#### Authentication Endpoints

```yaml
POST /api/v1/auth/register
  Request:
    {
      "username": "string",
      "email": "email",
      "password": "string"
    }
  Response:
    {
      "id": "uuid",
      "username": "string",
      "email": "email",
      "access_token": "jwt_token",
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
      "access_token": "jwt_token",
      "token_type": "bearer",
      "expires_in": 3600
    }

POST /api/v1/auth/refresh
  Headers:
    Authorization: Bearer {refresh_token}
  Response:
    {
      "access_token": "jwt_token",
      "token_type": "bearer"
    }
```

#### Task Endpoints

```yaml
GET /api/v1/tasks
  Query Parameters:
    - status: string (optional)
    - category_id: uuid (optional)
    - priority: integer (optional)
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
      "status": "todo|in_progress|done"
    }
  Response:
    {
      "id": "uuid",
      "title": "string",
      "description": "string",
      "category": "string",
      "priority": integer,
      "status": "string",
      "created_at": "iso_datetime",
      "ai_processing": true
    }

GET /api/v1/tasks/{task_id}
PUT /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}

POST /api/v1/tasks/{task_id}/categorize
  Response:
    {
      "task_id": "uuid",
      "category": "string",
      "confidence": float
    }

POST /api/v1/tasks/{task_id}/prioritize
  Response:
    {
      "task_id": "uuid",
      "priority": integer,
      "reasoning": "string"
    }
```

### Authentication Flow

```
1. User Registration/Login
   └─> Validate credentials
   └─> Generate JWT token (1 hour expiry)
   └─> Return token to client

2. Protected Route Access
   └─> Extract token from Authorization header
   └─> Validate token signature and expiry
   └─> Extract user_id from token
   └─> Process request with user context

3. Token Refresh
   └─> Validate refresh token
   └─> Generate new access token
   └─> Return new token
```

### Rate Limiting Strategy

```python
# Configuration
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_PERIOD = 60  # seconds

# Implementation
- Use slowapi (FastAPI compatible)
- Apply limits per IP address
- Different limits for different endpoints:
  - Auth endpoints: 5 requests/minute
  - Task creation: 20 requests/minute
  - Task listing: 100 requests/minute
  - AI endpoints: 10 requests/minute
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
  - Rationale: High performance, automatic OpenAPI docs, async support
- **Database**: SQLite with SQLAlchemy ORM
  - Rationale: Zero configuration, sufficient for MVP, easy migration path
- **Authentication**: python-jose for JWT
  - Rationale: Industry standard, stateless, scalable
- **AI Integration**: OpenAI Python SDK
  - Rationale: Official SDK, well-documented, reliable

### Frontend
- **Framework**: React 18+ with TypeScript
  - Rationale: Type safety, large ecosystem, team familiarity
- **Build Tool**: Vite
  - Rationale: Fast development, optimized production builds
- **Styling**: Tailwind CSS
  - Rationale: Rapid UI development, consistent design system
- **State Management**: React Context + useReducer
  - Rationale: Built-in, sufficient for MVP complexity

### Infrastructure
- **Containerization**: Docker + docker-compose
  - Rationale: Consistent environments, easy deployment
- **Web Server**: Uvicorn (included with FastAPI)
  - Rationale: ASGI server, production-ready, async support

## Security Considerations

1. **Authentication & Authorization**
   - JWT tokens with proper expiration
   - Bcrypt for password hashing
   - Role-based access control (future enhancement)

2. **Input Validation**
   - Pydantic models for request validation
   - SQL injection prevention via ORM
   - XSS prevention in React

3. **API Security**
   - CORS configuration
   - Rate limiting
   - Security headers (Helmet equivalent)
   - HTTPS in production

4. **Data Protection**
   - Environment variables for secrets
   - No sensitive data in logs
   - Prepared statements via SQLAlchemy

## Performance Optimizations

1. **Database**
   - Proper indexing on frequently queried fields
   - Connection pooling
   - Query optimization via ORM

2. **API**
   - Async endpoints for I/O operations
   - Response caching for categories
   - Pagination for list endpoints

3. **AI Processing**
   - Background tasks for AI operations
   - Caching of AI results
   - Fallback mechanisms for API failures

4. **Frontend**
   - Code splitting
   - Lazy loading
   - Optimistic UI updates

## Development Timeline Estimate

### Day 1 (8 hours)
1. **Hours 1-2**: Project setup, Docker configuration, database schema
2. **Hours 3-4**: Authentication system, user management
3. **Hours 5-6**: Task CRUD operations, API structure
4. **Hour 7**: AI integration, background tasks
5. **Hour 8**: Basic React frontend, deployment testing

### Post-MVP Enhancements
- Comprehensive test suite
- Advanced AI features
- Real-time updates (WebSockets)
- Multi-tenancy support
- Advanced analytics

## Deployment Architecture

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/tasks.db
      - JWT_SECRET=${JWT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000
```

## Monitoring & Logging

1. **Application Logs**
   - Structured JSON logging
   - Log levels: DEBUG, INFO, WARNING, ERROR
   - Request/response logging

2. **Performance Metrics**
   - API response times
   - Database query times
   - AI processing duration

3. **Error Tracking**
   - Centralized error logging
   - AI failure tracking
   - Rate limit violations

## Scalability Path

1. **Short Term (10-100 users)**
   - Current architecture sufficient
   - Monitor performance metrics

2. **Medium Term (100-1000 users)**
   - Migrate to PostgreSQL
   - Add Redis for caching
   - Implement CDN for static assets

3. **Long Term (1000+ users)**
   - Microservices architecture
   - Kubernetes deployment
   - Dedicated AI processing service
   - Read replicas for database