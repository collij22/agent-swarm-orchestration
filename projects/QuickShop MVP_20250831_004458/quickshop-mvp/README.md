# QuickShop MVP

Modern e-commerce platform with essential features built for rapid deployment.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd quickshop-mvp

# Start with Docker (Recommended)
docker-compose up --build

# Or run locally
./scripts/setup.sh
./scripts/dev.sh
```

## [DOC] Features

- [DONE] User Authentication (JWT)
- [DONE] Product Catalog with Search
- [DONE] Shopping Cart Management
- [DONE] Stripe Payment Integration
- [DONE] Order Management
- [DONE] Admin Dashboard
- [DONE] Responsive UI Design

## 🛠 Tech Stack

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS for styling
- Zustand for state management
- Vite for fast development

**Backend:**
- Python FastAPI
- PostgreSQL database
- Redis for caching
- JWT authentication

**Infrastructure:**
- Docker & Docker Compose
- GitHub Actions CI/CD
- AWS deployment ready

## 📱 Demo Accounts

**Admin User:**
- Email: admin@quickshop.com
- Password: admin123

**Customer User:**
- Email: customer@quickshop.com
- Password: customer123

## 🔧 Development

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend development
cd frontend
npm install
npm run dev
```

## 📦 Deployment

```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build

# Deploy to AWS
./scripts/deploy.sh
```

## 📖 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```