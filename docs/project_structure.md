# TaskManagerAPI Project Structure

```
TaskManagerAPI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration and environment variables
│   │   ├── database.py          # Database connection and session management
│   │   ├── dependencies.py      # Shared dependencies (auth, db session)
│   │   │
│   │   ├── models/              # SQLModel database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   └── category.py
│   │   │
│   │   ├── schemas/             # Pydantic schemas for API
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── category.py
│   │   │   └── auth.py
│   │   │
│   │   ├── api/                 # API routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py     # Authentication endpoints
│   │   │   │   ├── tasks.py    # Task CRUD endpoints
│   │   │   │   └── categories.py # Category endpoints
│   │   │   └── router.py       # Main API router
│   │   │
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # JWT handling, password hashing
│   │   │   ├── task.py         # Task business logic
│   │   │   ├── ai.py           # OpenAI integration
│   │   │   └── rate_limit.py   # Rate limiting logic
│   │   │
│   │   ├── core/                # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py     # Security utilities
│   │   │   ├── exceptions.py   # Custom exceptions
│   │   │   └── middleware.py   # Custom middleware
│   │   │
│   │   └── utils/               # Helper utilities
│   │       ├── __init__.py
│   │       └── validators.py    # Custom validators
│   │
│   ├── migrations/              # Alembic migrations
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── tests/                   # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py         # Pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_tasks.py
│   │   ├── test_ai.py
│   │   └── test_integration.py
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── requirements-dev.txt     # Development dependencies
│   ├── pytest.ini              # Pytest configuration
│   └── .env.example            # Example environment variables
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   │
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── main.jsx            # Entry point
│   │   ├── index.css           # Global styles with Tailwind
│   │   │
│   │   ├── components/          # React components
│   │   │   ├── Layout.jsx
│   │   │   ├── TaskList.jsx
│   │   │   ├── TaskForm.jsx
│   │   │   ├── TaskItem.jsx
│   │   │   ├── LoginForm.jsx
│   │   │   └── RegisterForm.jsx
│   │   │
│   │   ├── services/            # API client services
│   │   │   ├── api.js          # Axios configuration
│   │   │   ├── auth.js         # Authentication service
│   │   │   └── tasks.js        # Tasks API service
│   │   │
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.js
│   │   │   └── useTasks.js
│   │   │
│   │   ├── context/             # React context providers
│   │   │   └── AuthContext.jsx
│   │   │
│   │   └── utils/               # Utility functions
│   │       └── constants.js
│   │
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── .env.example
│
├── docker/
│   ├── backend.Dockerfile       # Backend container
│   ├── frontend.Dockerfile      # Frontend container
│   └── nginx.conf              # Nginx configuration
│
├── docs/
│   ├── architecture.md         # System architecture
│   ├── database_schema.sql     # Database schema
│   ├── openapi.yaml           # API specification
│   ├── project_structure.md    # This file
│   └── deployment.md          # Deployment guide
│
├── scripts/
│   ├── init_db.py             # Database initialization
│   ├── seed_data.py           # Seed test data
│   └── test_ai.py             # Test AI integration
│
├── docker-compose.yml          # Docker orchestration
├── docker-compose.dev.yml      # Development overrides
├── .gitignore
├── .env.example               # Root environment example
├── README.md                  # Project documentation
└── Makefile                   # Common commands
```

## Key Files Description

### Backend Core Files

- **main.py**: FastAPI application initialization, middleware setup, route inclusion
- **config.py**: Pydantic settings for environment variables and configuration
- **database.py**: SQLite connection, session management, and base model setup
- **dependencies.py**: Reusable dependencies for authentication and database sessions

### Frontend Core Files

- **App.jsx**: Main application component with routing
- **api.js**: Axios instance with interceptors for authentication
- **AuthContext.jsx**: Authentication state management
- **useAuth.js**: Custom hook for authentication logic

### Docker Files

- **docker-compose.yml**: Production-ready multi-container setup
- **nginx.conf**: Reverse proxy, rate limiting, and static file serving

### Configuration Files

- **.env.example**: Template for required environment variables
- **alembic.ini**: Database migration configuration
- **pytest.ini**: Test runner configuration
- **tailwind.config.js**: Tailwind CSS customization

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite:///./taskmanager.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=["http://localhost:5173"]
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=TaskManager
```

## Development Workflow

1. **Backend Development**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements-dev.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Development**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Docker Development**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

## Testing Strategy

- **Unit Tests**: Individual service and utility functions
- **Integration Tests**: API endpoint testing with test database
- **E2E Tests**: Full workflow testing (optional for MVP)
- **AI Mock Tests**: Testing with mocked OpenAI responses

## Code Standards

- **Python**: Black formatter, isort, flake8
- **JavaScript**: ESLint with Airbnb config, Prettier
- **Git**: Conventional commits, feature branches
- **Documentation**: Docstrings for all public functions