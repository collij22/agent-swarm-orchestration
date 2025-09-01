# System Architecture

## Overview
Microservices architecture with the following components:

### Services
1. **API Gateway** - Entry point for all client requests
2. **Auth Service** - JWT-based authentication
3. **User Service** - User management and profiles
4. **Data Service** - Core business logic

### Technology Stack
- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI (Python 3.11)
- Database: PostgreSQL 15
- Cache: Redis 7
- Message Queue: RabbitMQ

### Deployment
- Docker containers
- Kubernetes orchestration
- AWS/GCP cloud platform
