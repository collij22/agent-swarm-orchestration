# QuickShop MVP - E-commerce Platform

Modern full-stack e-commerce platform with payment integration and admin panel.

## 🚀 Features

- **User Authentication**: Secure JWT-based registration and login
- **Product Catalog**: CRUD operations with search and filtering
- **Shopping Cart**: Session-based cart with quantity management
- **Payment Processing**: Stripe integration for secure payments
- **Order Management**: Order tracking and history
- **Admin Dashboard**: Product and order management
- **Responsive Design**: Mobile-first design with Tailwind CSS

## 🛠 Tech Stack

### Backend
- **Python 3.11** with **FastAPI**
- **PostgreSQL** database with **SQLAlchemy**
- **Redis** for caching and sessions
- **JWT** authentication with refresh tokens
- **Pytest** for testing

### Frontend
- **React 18** with **TypeScript**
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Zustand** for state management
- **React Router** for navigation

### Infrastructure
- **Docker** + **Docker Compose**
- **PostgreSQL** and **Redis** containers
- Environment-based configuration

## 📦 Project Structure

```
quickshop-mvp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. **Clone and start services**:
```bash
git clone <repository>
cd quickshop-mvp
docker-compose up -d
```

2. **Backend setup** (if running locally):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Frontend setup** (if running locally):
```bash
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🔧 Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/quickshop
REDIS_URL=redis://localhost:6379

# Authentication
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
SENDGRID_API_KEY=SG.xxx
FROM_EMAIL=noreply@quickshop.com
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📚 API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔒 Security Features

- JWT authentication with refresh tokens
- Password hashing with bcrypt
- CORS configuration
- Rate limiting
- Input validation
- SQL injection prevention

## 📈 Performance

- Redis caching for frequent queries
- Database indexing on key fields
- Lazy loading for large datasets
- Image optimization and CDN ready
- API response time < 200ms target

## 🚢 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Monitoring and logging setup
- [ ] Backup strategy implemented

### Scaling Considerations
- Horizontal scaling with load balancer
- Database read replicas
- CDN for static assets
- Microservices architecture ready

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@quickshop.com or create an issue in the repository.