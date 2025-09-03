# QuickShop MVP System Architecture

## Overview
QuickShop is a modern e-commerce platform built with a microservices-ready monolithic architecture, designed for rapid MVP development with future scalability in mind.

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Layer                               │
├─────────────────────┬───────────────────┬───────────────────────────┤
│   Web Application   │  Mobile Web App   │    Admin Dashboard        │
│   (React + TS)      │  (Responsive)     │    (React + TS)          │
└──────────┬──────────┴─────────┬─────────┴────────────┬─────────────┘
           │                    │                       │
           └────────────────────┴───────────────────────┘
                                │
                                │ HTTPS
                                │
┌───────────────────────────────┴─────────────────────────────────────┐
│                          API Gateway                                 │
│                    (Nginx Reverse Proxy)                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────────┐
│                      FastAPI Application                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐│
│  │Auth Service │  │Product Service│  │Cart Service│  │Order Service││
│  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘│
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐│
│  │Payment Svc  │  │Email Service │  │Admin Service│  │Analytics   ││
│  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘│
└───────┬──────────────┬──────────────┬──────────────┬───────────────┘
        │              │              │              │
┌───────┴──────┐ ┌─────┴──────┐ ┌────┴──────┐ ┌────┴──────┐
│  PostgreSQL  │ │   Redis    │ │  Stripe   │ │ SendGrid  │
│  (Primary DB)│ │  (Cache)   │ │ (Payment) │ │  (Email)  │
└──────────────┘ └────────────┘ └───────────┘ └───────────┘
```

### Data Flow Architecture

```
User Request Flow:
1. Client  ->  API Gateway (Nginx)
2. API Gateway  ->  FastAPI Application
3. FastAPI  ->  Service Layer  ->  Repository Layer  ->  Database
4. Response flows back through the same path

Payment Flow:
1. Client  ->  Create Payment Intent  ->  FastAPI
2. FastAPI  ->  Stripe API  ->  Payment Intent
3. Client  ->  Confirm Payment  ->  Stripe
4. Stripe  ->  Webhook  ->  FastAPI  ->  Update Order Status

Caching Strategy:
- Session data: Redis (15-minute TTL)
- Product catalog: Redis (1-hour TTL)
- User cart: Redis (24-hour TTL)
- Static assets: CDN (CloudFlare/AWS CloudFront)
```

## Database Design

### Entity Relationship Diagram

```sql
-- Core Entities and Relationships

users
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE, INDEXED)
├── password_hash (VARCHAR)
├── full_name (VARCHAR)
├── role (ENUM: customer, admin)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

products
├── id (UUID, PK)
├── name (VARCHAR, INDEXED)
├── slug (VARCHAR, UNIQUE, INDEXED)
├── description (TEXT)
├── price (DECIMAL)
├── stock_quantity (INTEGER)
├── category_id (UUID, FK)
├── image_url (VARCHAR)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

categories
├── id (UUID, PK)
├── name (VARCHAR, UNIQUE)
├── slug (VARCHAR, UNIQUE, INDEXED)
├── parent_id (UUID, FK, NULLABLE)
└── created_at (TIMESTAMP)

carts
├── id (UUID, PK)
├── user_id (UUID, FK, NULLABLE)
├── session_id (VARCHAR, INDEXED)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

cart_items
├── id (UUID, PK)
├── cart_id (UUID, FK)
├── product_id (UUID, FK)
├── quantity (INTEGER)
├── price_at_time (DECIMAL)
└── created_at (TIMESTAMP)

orders
├── id (UUID, PK)
├── user_id (UUID, FK)
├── order_number (VARCHAR, UNIQUE, INDEXED)
├── status (ENUM: pending, processing, shipped, delivered, cancelled)
├── total_amount (DECIMAL)
├── shipping_address (JSONB)
├── payment_intent_id (VARCHAR, INDEXED)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

order_items
├── id (UUID, PK)
├── order_id (UUID, FK)
├── product_id (UUID, FK)
├── quantity (INTEGER)
├── unit_price (DECIMAL)
└── created_at (TIMESTAMP)

-- Indexes for Performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
```

### Migration Strategy
1. Use Alembic for database migrations
2. Seed data includes: 3 categories, 10 products, 1 admin user
3. All timestamps in UTC
4. UUID primary keys for better distribution and security

## API Structure

### RESTful Endpoint Design

```yaml
# Authentication Endpoints
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout

# User Endpoints
GET    /api/v1/users/me
PUT    /api/v1/users/me
GET    /api/v1/users/orders

# Product Endpoints
GET    /api/v1/products                 # List with pagination, filters
GET    /api/v1/products/{id}           # Get single product
GET    /api/v1/products/search         # Search products
GET    /api/v1/categories              # List categories

# Cart Endpoints
GET    /api/v1/cart                    # Get current cart
POST   /api/v1/cart/items              # Add item to cart
PUT    /api/v1/cart/items/{id}         # Update quantity
DELETE /api/v1/cart/items/{id}         # Remove item
POST   /api/v1/cart/checkout           # Initialize checkout

# Order Endpoints
POST   /api/v1/orders                  # Create order
GET    /api/v1/orders/{id}             # Get order details
GET    /api/v1/orders                  # List user orders

# Payment Endpoints
POST   /api/v1/payments/intent         # Create payment intent
POST   /api/v1/payments/webhook        # Stripe webhook

# Admin Endpoints
GET    /api/v1/admin/products          # List all products
POST   /api/v1/admin/products          # Create product
PUT    /api/v1/admin/products/{id}     # Update product
DELETE /api/v1/admin/products/{id}     # Delete product
GET    /api/v1/admin/orders            # List all orders
PUT    /api/v1/admin/orders/{id}       # Update order status
GET    /api/v1/admin/analytics         # Sales analytics
```

### Authentication Flow

```
1. User Registration:
   Client  ->  POST /auth/register  ->  Validate  ->  Hash Password  ->  Store User  ->  Return JWT

2. User Login:
   Client  ->  POST /auth/login  ->  Validate Credentials  ->  Generate JWT + Refresh Token  ->  Return Tokens

3. Token Refresh:
   Client  ->  POST /auth/refresh (with refresh token)  ->  Validate  ->  Generate New JWT  ->  Return JWT

4. Protected Routes:
   Client  ->  Request with JWT in Authorization header  ->  Validate JWT  ->  Process Request
```

### Rate Limiting Strategy
- Public endpoints: 100 requests/minute per IP
- Authenticated endpoints: 300 requests/minute per user
- Payment endpoints: 10 requests/minute per user
- Admin endpoints: 1000 requests/minute per admin

## Technology Stack Recommendations

### Backend Stack
- **Language**: Python 3.11
- **Framework**: FastAPI (async support, automatic OpenAPI docs)
- **ORM**: SQLAlchemy 2.0 with async support
- **Database**: PostgreSQL 15 (JSONB support, full-text search)
- **Cache**: Redis 7 (session management, caching)
- **Task Queue**: Celery with Redis broker (email sending, order processing)
- **Testing**: Pytest with pytest-asyncio

### Frontend Stack
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand (lightweight, TypeScript-friendly)
- **Styling**: Tailwind CSS with custom components
- **Build Tool**: Vite (fast HMR, optimized builds)
- **Testing**: Jest + React Testing Library
- **API Client**: Axios with interceptors for auth

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy, static files)
- **Process Manager**: Gunicorn with Uvicorn workers
- **Monitoring**: Sentry for error tracking
- **Logging**: Structured JSON logs with correlation IDs

### External Services
- **Payment**: Stripe (PCI compliance handled)
- **Email**: SendGrid (transactional emails)
- **CDN**: CloudFlare (static assets, DDoS protection)
- **Storage**: AWS S3 (product images)

## Security Architecture

### Security Layers
1. **Network Security**
   - HTTPS only with SSL/TLS 1.3
   - CORS properly configured
   - Security headers (HSTS, CSP, X-Frame-Options)

2. **Application Security**
   - Input validation on all endpoints
   - SQL injection prevention via ORM
   - XSS prevention with proper escaping
   - CSRF protection with double-submit cookies

3. **Authentication & Authorization**
   - JWT with short expiry (15 minutes)
   - Refresh tokens with rotation
   - Role-based access control (RBAC)
   - Password hashing with bcrypt

4. **Data Security**
   - Encryption at rest for sensitive data
   - PCI DSS compliance via Stripe
   - GDPR compliance with data retention policies

## Performance Optimization

### Caching Strategy
```python
# Cache Layers
1. CDN Level: Static assets, images (24h TTL)
2. Redis Level:
   - Product catalog: 1 hour TTL
   - Category tree: 6 hours TTL
   - User sessions: 15 minutes TTL
   - Cart data: 24 hours TTL
3. Application Level:
   - In-memory caching for frequently accessed configs
```

### Database Optimization
- Connection pooling with SQLAlchemy
- Prepared statements for common queries
- Materialized views for analytics
- Partitioning for orders table (by month)

### API Optimization
- Pagination on all list endpoints
- Field filtering to reduce payload size
- Compression (gzip) for responses
- Async processing for heavy operations

## Scalability Planning

### Horizontal Scaling Path
1. **Phase 1 (MVP)**: Single server with Docker Compose
2. **Phase 2**: Separate database server, add read replicas
3. **Phase 3**: Multiple app servers behind load balancer
4. **Phase 4**: Extract services (Payment, Email, Analytics)
5. **Phase 5**: Full microservices with service mesh

### Vertical Scaling Considerations
- Start with 2GB RAM, 2 vCPUs
- Database: 4GB RAM, SSD storage
- Redis: 1GB RAM
- Monitor and scale based on metrics

## Development Timeline Estimate

### Week 1
- Days 1-2: Database schema, core models, authentication
- Days 3-4: Product catalog, search, categories
- Days 5-6: Cart functionality, order management
- Day 7: Payment integration, testing

### Week 2
- Days 8-9: Admin dashboard, analytics
- Days 10-11: Email notifications, performance optimization
- Days 12-13: Docker setup, deployment configuration
- Day 14: Final testing, documentation, deployment

## Monitoring and Observability

### Metrics to Track
- API response times (p50, p95, p99)
- Database query performance
- Cache hit rates
- Order conversion rates
- Error rates by endpoint

### Logging Strategy
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "correlation_id": "uuid",
  "user_id": "uuid",
  "endpoint": "/api/v1/products",
  "method": "GET",
  "status_code": 200,
  "response_time_ms": 45,
  "message": "Product list retrieved"
}
```

## Disaster Recovery

### Backup Strategy
- Database: Daily automated backups, 30-day retention
- User uploads: S3 versioning enabled
- Configuration: Git repository
- Secrets: Encrypted vault (HashiCorp Vault or AWS Secrets Manager)

### Recovery Procedures
1. Database failure: Restore from latest backup
2. Application failure: Blue-green deployment rollback
3. Service outage: Failover to secondary region
4. Data corruption: Point-in-time recovery

## Compliance Considerations

### PCI DSS
- No credit card data stored (handled by Stripe)
- Secure transmission of payment data
- Regular security audits
- Access control and logging

### GDPR
- User consent for data processing
- Right to erasure implementation
- Data portability via export function
- Privacy by design principles

## Next Steps for Implementation

1. **Database Expert**: Implement the schema with proper migrations
2. **Rapid Builder**: Create the FastAPI application structure
3. **Frontend Specialist**: Set up React application with routing
4. **API Integrator**: Configure Stripe and SendGrid
5. **DevOps Engineer**: Create Docker configuration
6. **Quality Guardian**: Set up testing framework