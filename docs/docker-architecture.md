# Docker Architecture for TaskManagerAPI

## Container Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    docker-compose Network                     │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │                 │  │                 │  │              │ │
│  │  nginx:alpine   │  │  api:python3.11 │  │ frontend:node│ │
│  │                 │  │                 │  │              │ │
│  │  Port: 80/443   │  │  Port: 8000     │  │  Port: 3000  │ │
│  │                 │  │                 │  │              │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘ │
│           │                    │                    │         │
│           └────────────────────┴────────────────────┘         │
│                              │                                │
│                    ┌─────────┴──────────┐                    │
│                    │                    │                    │
│                    │  Shared Volumes    │                    │
│                    │  - ./data/db.sqlite│                    │
│                    │  - ./logs          │                    │
│                    │                    │                    │
│                    └────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Backend Dockerfile (Multi-stage Build)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Frontend Dockerfile (Multi-stage Build)

```dockerfile
# Stage 1: Builder
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Runtime
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1
```

## docker-compose.yml Configuration

```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: taskmanager-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - api
      - frontend
    networks:
      - taskmanager-network
    restart: unless-stopped

  # FastAPI Backend
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        - BUILD_ENV=production
    container_name: taskmanager-api
    environment:
      - DATABASE_URL=sqlite:///./data/db.sqlite
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost,http://localhost:3000
    volumes:
      - ./data:/app/data
      - ./logs/api:/app/logs
    depends_on:
      - redis
    networks:
      - taskmanager-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # React Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=http://localhost/api/v1
    container_name: taskmanager-frontend
    networks:
      - taskmanager-network
    restart: unless-stopped

  # Redis Cache (Optional)
  redis:
    image: redis:7-alpine
    container_name: taskmanager-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - taskmanager-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  taskmanager-network:
    driver: bridge

volumes:
  redis-data:
```

## Nginx Configuration

```nginx
# nginx/conf.d/default.conf
upstream api {
    server api:8000;
}

upstream frontend {
    server frontend:80;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

server {
    listen 80;
    server_name localhost;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # API routes
    location /api/ {
        # Apply rate limiting
        limit_req zone=api_limit burst=20 nodelay;
        
        # Auth endpoints have stricter limits
        location /api/v1/auth/ {
            limit_req zone=auth_limit burst=5 nodelay;
            proxy_pass http://api;
            include /etc/nginx/proxy_params;
        }
        
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend routes
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## Environment Configuration

### .env.example
```bash
# API Configuration
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=sqlite:///./data/db.sqlite

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=150
OPENAI_TEMPERATURE=0.7

# Redis Configuration (Optional)
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600

# CORS Configuration
CORS_ORIGINS=http://localhost,http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/api.log

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

## Deployment Commands

### Development
```bash
# Build and start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f nginx

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production
```bash
# Build with production optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Update a specific service
docker-compose up -d --no-deps --build api

# Scale services
docker-compose up -d --scale api=3

# Backup database
docker exec taskmanager-api python -m app.scripts.backup_db

# Run migrations
docker exec taskmanager-api alembic upgrade head
```

## Container Security Best Practices

1. **Non-root User**: All containers run as non-root users
2. **Read-only Root Filesystem**: Where possible, use read-only root filesystem
3. **Minimal Base Images**: Use alpine variants for smaller attack surface
4. **No Secrets in Images**: Use environment variables or secrets management
5. **Health Checks**: All services have health check endpoints
6. **Resource Limits**: Set memory and CPU limits in production

## Monitoring and Logging

### Log Structure
```
/logs
├── nginx/
│   ├── access.log
│   └── error.log
├── api/
│   ├── api.log
│   ├── error.log
│   └── slow_queries.log
└── frontend/
    └── build.log
```

### Health Check Endpoints
- Nginx: `http://localhost/health`
- API: `http://localhost:8000/health`
- Redis: `redis-cli ping`

## Backup Strategy

1. **Database Backups**:
   - Daily automated backups of SQLite database
   - Stored in `/backups` volume
   - Retention: 7 days

2. **Configuration Backups**:
   - Version controlled in Git
   - Environment variables backed up separately

3. **Restore Process**:
   ```bash
   # Stop API service
   docker-compose stop api
   
   # Restore database
   docker cp backup.db taskmanager-api:/app/data/db.sqlite
   
   # Start API service
   docker-compose start api
   ```

## Performance Optimization

1. **Multi-stage Builds**: Reduce image size by 60-70%
2. **Layer Caching**: Optimize Dockerfile for better caching
3. **Volume Mounts**: Use volumes for persistent data
4. **Network Optimization**: Use internal networks for service communication
5. **Resource Allocation**: Set appropriate limits based on load testing