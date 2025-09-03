# QuickShop MVP Project Structure

## Complete Project Directory Structure

```
quickshop-mvp/
├── frontend/                      # React frontend application
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── common/          # Shared components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Loading.tsx
│   │   │   │   └── ErrorBoundary.tsx
│   │   │   ├── layout/          # Layout components
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   └── features/        # Feature-specific components
│   │   │       ├── auth/
│   │   │       │   ├── LoginForm.tsx
│   │   │       │   ├── RegisterForm.tsx
│   │   │       │   └── UserProfile.tsx
│   │   │       ├── products/
│   │   │       │   ├── ProductCard.tsx
│   │   │       │   ├── ProductList.tsx
│   │   │       │   ├── ProductDetail.tsx
│   │   │       │   └── ProductFilter.tsx
│   │   │       ├── cart/
│   │   │       │   ├── CartItem.tsx
│   │   │       │   ├── CartSummary.tsx
│   │   │       │   └── CartDropdown.tsx
│   │   │       ├── orders/
│   │   │       │   ├── OrderList.tsx
│   │   │       │   ├── OrderDetail.tsx
│   │   │       │   └── OrderStatus.tsx
│   │   │       └── admin/
│   │   │           ├── Dashboard.tsx
│   │   │           ├── ProductManager.tsx
│   │   │           ├── OrderManager.tsx
│   │   │           └── UserManager.tsx
│   │   ├── pages/               # Page components
│   │   │   ├── Home.tsx
│   │   │   ├── Products.tsx
│   │   │   ├── ProductDetail.tsx
│   │   │   ├── Cart.tsx
│   │   │   ├── Checkout.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Profile.tsx
│   │   │   └── Admin/
│   │   │       ├── Dashboard.tsx
│   │   │       ├── Products.tsx
│   │   │       ├── Orders.tsx
│   │   │       └── Users.tsx
│   │   ├── services/            # API services
│   │   │   ├── api.ts          # Base API configuration
│   │   │   ├── auth.service.ts
│   │   │   ├── product.service.ts
│   │   │   ├── cart.service.ts
│   │   │   ├── order.service.ts
│   │   │   └── admin.service.ts
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useCart.ts
│   │   │   ├── useProducts.ts
│   │   │   ├── useOrders.ts
│   │   │   └── useDebounce.ts
│   │   ├── store/              # State management
│   │   │   ├── AuthContext.tsx
│   │   │   ├── CartContext.tsx
│   │   │   └── AppContext.tsx
│   │   ├── types/              # TypeScript types
│   │   │   ├── auth.types.ts
│   │   │   ├── product.types.ts
│   │   │   ├── cart.types.ts
│   │   │   ├── order.types.ts
│   │   │   └── common.types.ts
│   │   ├── utils/              # Utility functions
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   ├── constants.ts
│   │   │   └── helpers.ts
│   │   ├── styles/             # Styles
│   │   │   ├── globals.css
│   │   │   └── tailwind.css
│   │   ├── App.tsx            # Main App component
│   │   ├── index.tsx          # Entry point
│   │   └── routes.tsx         # Route configuration
│   ├── public/                # Static assets
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── images/
│   ├── .env.example          # Environment variables example
│   ├── .gitignore
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.ts
│
├── backend/                   # FastAPI backend application
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── v1/          # API version 1
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── products.py
│   │   │   │   ├── categories.py
│   │   │   │   ├── cart.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── users.py
│   │   │   │   └── admin.py
│   │   │   └── deps.py      # Dependencies
│   │   ├── core/            # Core functionality
│   │   │   ├── __init__.py
│   │   │   ├── config.py    # Configuration
│   │   │   ├── security.py  # Security utilities
│   │   │   ├── database.py  # Database setup
│   │   │   └── redis.py     # Redis setup
│   │   ├── models/          # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── category.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   └── base.py
│   │   ├── schemas/         # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── category.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   └── common.py
│   │   ├── services/        # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   └── email.py
│   │   ├── middleware/      # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── cors.py
│   │   │   ├── logging.py
│   │   │   └── rate_limit.py
│   │   ├── utils/           # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── pagination.py
│   │   │   ├── exceptions.py
│   │   │   └── validators.py
│   │   ├── __init__.py
│   │   └── main.py         # Application entry point
│   ├── alembic/            # Database migrations
│   │   ├── versions/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/              # Test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── conftest.py
│   │   └── test_*.py
│   ├── scripts/            # Utility scripts
│   │   ├── create_admin.py
│   │   └── seed_data.py
│   ├── .env.example       # Environment variables example
│   ├── .gitignore
│   ├── requirements.txt   # Python dependencies
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── docker/                 # Docker configuration
│   ├── nginx/
│   │   └── nginx.conf
│   ├── postgres/
│   │   └── init.sql
│   └── redis/
│       └── redis.conf
│
├── docs/                   # Documentation
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   └── development/       # Development guides
│
├── scripts/               # Project scripts
│   ├── setup.sh          # Initial setup script
│   ├── deploy.sh         # Deployment script
│   └── backup.sh         # Backup script
│
├── .github/              # GitHub configuration
│   └── workflows/        # GitHub Actions
│       ├── ci.yml
│       └── deploy.yml
│
├── docker-compose.yml    # Docker Compose configuration
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env.example         # Root environment variables
├── .gitignore          # Git ignore file
├── README.md           # Project documentation
├── LICENSE             # License file
└── Makefile           # Make commands

```

## File Descriptions

### Frontend Files

#### Components
- **common/**: Reusable UI components used across the application
- **layout/**: Components that define the page structure
- **features/**: Feature-specific components organized by domain

#### Pages
- Route-based components that compose features
- Admin pages are in a separate subdirectory

#### Services
- API service layer for backend communication
- Centralized error handling and request configuration

#### Hooks
- Custom React hooks for shared logic
- Authentication, cart, and data fetching hooks

#### Store
- Context API based state management
- Separate contexts for different domains

#### Types
- TypeScript type definitions
- Shared interfaces and types

### Backend Files

#### API
- RESTful endpoints organized by version
- Dependency injection setup

#### Core
- Application configuration
- Security utilities
- Database and cache connections

#### Models
- SQLAlchemy ORM models
- Database table definitions

#### Schemas
- Pydantic models for request/response validation
- Data transfer objects

#### Services
- Business logic layer
- Separation of concerns from API endpoints

#### Middleware
- Custom middleware for cross-cutting concerns
- CORS, logging, rate limiting

### Docker Files

- **docker-compose.yml**: Base configuration
- **docker-compose.dev.yml**: Development overrides
- **docker-compose.prod.yml**: Production configuration

### Configuration Files

#### Frontend
- **package.json**: NPM dependencies and scripts
- **tsconfig.json**: TypeScript configuration
- **tailwind.config.js**: Tailwind CSS configuration
- **vite.config.ts**: Vite bundler configuration

#### Backend
- **requirements.txt**: Python dependencies
- **alembic.ini**: Database migration configuration
- **pyproject.toml**: Python project configuration

### Documentation

- **README.md**: Project overview and setup instructions
- **docs/**: Detailed documentation
  - API documentation
  - Deployment guides
  - Development guides

## Environment Variables

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=QuickShop
```

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost/quickshop
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Docker Compose (.env)
```
POSTGRES_USER=quickshop
POSTGRES_PASSWORD=password
POSTGRES_DB=quickshop
REDIS_PASSWORD=redis-password
```

## Key Conventions

### Naming Conventions
- **Files**: kebab-case for directories, PascalCase for components
- **Variables**: camelCase for JavaScript/TypeScript
- **Python**: snake_case for functions and variables
- **Database**: snake_case for tables and columns

### Code Organization
- Feature-based organization
- Separation of concerns
- Single responsibility principle
- DRY (Don't Repeat Yourself)

### Git Workflow
- Feature branches: `feature/feature-name`
- Bugfix branches: `bugfix/issue-description`
- Release branches: `release/version-number`