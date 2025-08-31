# QuickShop MVP

Modern e-commerce platform with essential features for rapid market entry.

## Tech Stack

- **Frontend**: React + TypeScript, Tailwind CSS, Zustand
- **Backend**: FastAPI (Python), PostgreSQL, Redis
- **Authentication**: JWT
- **Payment**: Stripe Integration
- **Deployment**: Docker + docker-compose

## Quick Start

```bash
# Clone and setup
git clone <repository>
cd quickshop-mvp

# Start with Docker
docker-compose up -d

# Or run locally
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Features

- [DONE] User Authentication (JWT)
- [DONE] Product Catalog with Search
- [DONE] Shopping Cart Management
- [DONE] Stripe Payment Integration
- [DONE] Order Management
- [DONE] Admin Dashboard
- [DONE] Responsive Mobile Design

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Project Structure

```
quickshop-mvp/
├── backend/           # FastAPI application
├── frontend/          # React application
├── database/          # SQL migrations and seeds
├── docker-compose.yml # Development environment
└── docs/             # Project documentation
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `STRIPE_SECRET_KEY`
- `REDIS_URL`

## Development

- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:3000
- Database on localhost:5432
- Redis on localhost:6379

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```