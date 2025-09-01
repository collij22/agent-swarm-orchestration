# QuickShop MVP

Modern e-commerce platform with payment integration and admin panel.

## Features

- 🔐 User Authentication (JWT)
- 📦 Product Catalog Management
- 🛒 Shopping Cart
- 💳 Stripe Payment Integration
- [DOC] Admin Dashboard
- 📱 Responsive Design
- 🚀 Fast Performance

## Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS
- Zustand (state management)
- React Router
- Axios

**Backend:**
- Python 3.11
- FastAPI
- PostgreSQL
- Redis (caching)
- JWT Authentication
- Stripe Integration

**Infrastructure:**
- Docker + Docker Compose
- Health checks
- Auto-migrations

## Quick Start

1. **Prerequisites**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Services**
   ```bash
   docker-compose up --build
   ```

4. **Access Applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Database
```bash
# Run migrations
docker-compose exec backend python app/db/migrations.py

# Seed data
docker-compose exec backend python app/db/seed.py
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token

### Products
- `GET /products` - List products
- `GET /products/{id}` - Get product
- `POST /products` - Create product (admin)
- `PUT /products/{id}` - Update product (admin)
- `DELETE /products/{id}` - Delete product (admin)

### Cart
- `GET /cart` - Get user cart
- `POST /cart/items` - Add item to cart
- `PUT /cart/items/{id}` - Update cart item
- `DELETE /cart/items/{id}` - Remove cart item

### Orders
- `POST /orders` - Create order
- `GET /orders` - Get user orders
- `GET /orders/{id}` - Get order details

### Payments
- `POST /payments/create-intent` - Create payment intent
- `POST /payments/webhook` - Stripe webhook

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

The application is containerized and ready for deployment on:
- AWS EC2
- DigitalOcean Droplets
- Any Docker-compatible hosting

## Environment Variables

See `.env.example` for required configuration.

## License

MIT License