# TaskManagerAPI Project Structure

```
taskmanager-api/
├── backend/                      # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database connection and session
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── middleware.py        # Custom middleware
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   └── category.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── category.py
│   │   │   └── auth.py
│   │   ├── api/                 # API routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── categories.py
│   │   │   │   └── users.py
│   │   │   └── deps.py          # API dependencies
│   │   ├── core/                # Core functionality
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # JWT and password handling
│   │   │   ├── ai_service.py    # OpenAI integration
│   │   │   └── rate_limit.py    # Rate limiting logic
│   │   ├── crud/                # CRUD operations
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   └── category.py
│   │   └── utils/               # Utility functions
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── tests/                   # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_tasks.py
│   │   ├── test_categories.py
│   │   ├── test_ai_service.py
│   │   └── test_security.py
│   ├── alembic/                 # Database migrations
│   │   ├── versions/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── .env.example
│   └── README.md
│
├── frontend/                    # React frontend application
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── common/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── Loading.tsx
│   │   │   │   └── ErrorBoundary.tsx
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── tasks/
│   │   │   │   ├── TaskList.tsx
│   │   │   │   ├── TaskItem.tsx
│   │   │   │   ├── TaskForm.tsx
│   │   │   │   └── TaskFilters.tsx
│   │   │   └── layout/
│   │   │       ├── MainLayout.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useTasks.ts
│   │   │   ├── useCategories.ts
│   │   │   └── useApi.ts
│   │   ├── services/            # API service layer
│   │   │   ├── api.ts
│   │   │   ├── auth.service.ts
│   │   │   ├── task.service.ts
│   │   │   └── category.service.ts
│   │   ├── store/               # State management (Zustand)
│   │   │   ├── authStore.ts
│   │   │   ├── taskStore.ts
│   │   │   └── uiStore.ts
│   │   ├── types/               # TypeScript types
│   │   │   ├── index.ts
│   │   │   ├── task.types.ts
│   │   │   ├── user.types.ts
│   │   │   └── api.types.ts
│   │   ├── utils/               # Utility functions
│   │   │   ├── constants.ts
│   │   │   ├── helpers.ts
│   │   │   └── validators.ts
│   │   ├── styles/              # Global styles
│   │   │   └── globals.css
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .env.example
│   └── README.md
│
├── database/                    # Database files and scripts
│   ├── schema.sql              # Initial schema
│   ├── seed.sql                # Seed data
│   └── migrations/             # Migration scripts
│
├── nginx/                      # Nginx configuration
│   ├── nginx.conf
│   ├── proxy_params.conf
│   └── ssl/                    # SSL certificates (production)
│
├── docs/                       # Documentation
│   ├── architecture.md         # System architecture
│   ├── api.md                  # API documentation
│   ├── deployment.md           # Deployment guide
│   ├── development.md          # Development guide
│   ├── openapi.yaml           # OpenAPI specification
│   └── project-structure.md    # This file
│
├── scripts/                    # Utility scripts
│   ├── setup.sh               # Initial setup script
│   ├── test.sh                # Run all tests
│   ├── deploy.sh              # Deployment script
│   └── backup.sh              # Database backup
│
├── .github/                    # GitHub specific files
│   ├── workflows/
│   │   ├── ci.yml             # CI pipeline
│   │   └── deploy.yml         # CD pipeline
│   └── ISSUE_TEMPLATE/
│
├── docker-compose.yml          # Docker composition
├── docker-compose.dev.yml      # Development overrides
├── docker-compose.prod.yml     # Production overrides
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # Project README
├── LICENSE                    # License file
└── CLAUDE.md                  # AI assistant guidelines
```

## Key Directories Explained

### Backend Structure
- **app/**: Main application code
- **models/**: SQLAlchemy ORM models defining database schema
- **schemas/**: Pydantic models for request/response validation
- **api/**: REST API endpoints organized by version
- **core/**: Core business logic and services
- **crud/**: Database operations layer
- **tests/**: Comprehensive test suite

### Frontend Structure
- **components/**: Reusable React components organized by feature
- **hooks/**: Custom React hooks for logic reuse
- **services/**: API communication layer
- **store/**: Global state management with Zustand
- **types/**: TypeScript type definitions
- **utils/**: Helper functions and constants

### Configuration Files
- **docker-compose.yml**: Main Docker configuration
- **.env.example**: Template for environment variables
- **nginx.conf**: Reverse proxy configuration
- **openapi.yaml**: API specification

## Development Workflow

1. **Backend Development**
   - Work in `backend/app/`
   - Run tests with `pytest`
   - Use `alembic` for migrations

2. **Frontend Development**
   - Work in `frontend/src/`
   - Use `npm run dev` for development
   - Build with `npm run build`

3. **Database Changes**
   - Update `database/schema.sql`
   - Create migration in `backend/alembic/`
   - Test migration before applying

4. **Documentation**
   - Update relevant docs in `docs/`
   - Keep OpenAPI spec in sync
   - Update README for major changes