# QuickShop MVP

A modern e-commerce platform built with FastAPI and React.

## 🚀 Quick Start

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
docker-compose up -d postgres redis
python -m alembic upgrade head
python scripts/seed_data.py

# Start backend
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
quickshop-mvp/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── db/             # Database models
│   │   └── services/       # Business logic
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   └── services/       # API services
│   └── package.json
├── docker-compose.yml      # Development environment
└── README.md
```

## 🔧 Features

- [DONE] User Authentication (JWT)
- [DONE] Product Catalog with Search
- [DONE] Shopping Cart Management
- [DONE] Stripe Payment Integration
- [DONE] Order Management
- [DONE] Admin Dashboard
- [DONE] Responsive Design

## 🛠 Tech Stack

- **Backend**: FastAPI, PostgreSQL, Redis, SQLAlchemy
- **Frontend**: React, TypeScript, Tailwind CSS, Zustand
- **Infrastructure**: Docker, GitHub Actions
- **Integrations**: Stripe, SendGrid

## 📖 Documentation

- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Admin Panel: http://localhost:3000/admin

## 🔐 Default Credentials

- Admin: admin@quickshop.com / admin123
- User: user@quickshop.com / user123