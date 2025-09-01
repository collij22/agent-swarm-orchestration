# QuickShop MVP - E-commerce Platform

A modern full-stack e-commerce platform with payment integration and admin panel.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd quickshop-mvp

# Start with Docker (recommended)
docker-compose up -d

# Or run locally
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

## 📁 Project Structure

```
quickshop-mvp/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── core/           # Configuration
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── stores/         # Zustand stores
│   ├── tests/              # Frontend tests
│   └── package.json
├── docker-compose.yml      # Multi-container setup
└── docs/                   # Documentation
```

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python 3.11 + SQLAlchemy
- **Database**: PostgreSQL + Redis
- **Deployment**: Docker + Docker Compose
- **Testing**: Pytest + Jest

## [DOC] Features

- [DONE] User Authentication (JWT)
- [DONE] Product Catalog Management
- [DONE] Shopping Cart Functionality
- [DONE] Payment Integration (Stripe)
- [DONE] Order Management System
- [DONE] Admin Dashboard
- [DONE] Responsive UI Design
- [DONE] Email Notifications

## 🔧 Environment Setup

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/quickshop
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
SENDGRID_API_KEY=SG.xxx
```

## 🚦 API Endpoints

- `GET /health` - Health check
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /products` - List products
- `POST /cart/add` - Add to cart
- `POST /orders` - Create order
- `POST /payments/create-intent` - Create payment

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# Coverage reports
pytest --cov=app
npm run test:coverage
```

## 🐳 Docker Deployment

```bash
docker-compose up -d
# Access at http://localhost:3000
```

## [DOC] Success Metrics

- [x] All features functional (100% completion)
- [x] Frontend builds without errors
- [x] Backend starts and responds to health checks
- [x] Database migrations apply cleanly
- [x] Docker containers run for 5+ minutes
- [x] At least 3 products seeded in database
- [x] User can complete purchase flow
- [x] Admin can manage products
- [x] Mobile responsive design verified

## 🔐 Security Features

- JWT authentication with refresh tokens
- Input validation and sanitization
- Rate limiting on API endpoints
- CORS configuration
- Security headers
- SQL injection protection

## 📈 Performance

- Redis caching for frequently accessed data
- Database query optimization
- Lazy loading for images
- Compressed assets
- CDN ready for static files

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Run tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details