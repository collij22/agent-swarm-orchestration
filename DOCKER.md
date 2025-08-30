# Docker Deployment Guide for TaskManagerAPI

## Overview
This guide explains how to deploy the TaskManagerAPI using Docker and docker-compose.

## Prerequisites
- Docker (19.03.0+)
- docker-compose (1.27.0+)
- OpenAI API Key

## Deployment Steps

### 1. Environment Configuration
Create a `.env` file in the project root with the following variables:
```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# JWT Configuration
JWT_SECRET=your_secure_secret_key

# Database Configuration
DATABASE_URL=sqlite:///tasks.db

# Application Configuration
APP_PORT=8000
DEBUG=false
```

### 2. Docker Compose Configuration
Our `docker-compose.yml` defines the following services:

#### Backend Service
- Python FastAPI application
- Exposes port 8000
- Mounts source code for development
- Installs dependencies from `requirements.txt`

#### Database Service
- SQLite database (file-based)
- Persisted volume for data retention

### 3. Build and Run
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Deployment Modes

### Development Mode
- Uses volume mounts for live code reloading
- Enables debug logging
- Exposes container ports

### Production Mode
- Uses multi-stage builds
- Minimizes image size
- Disables debug features

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure port 8000 is available
2. **API Key**: Verify OpenAI API key is valid
3. **Permissions**: Check Docker and file system permissions

### Debugging
```bash
# Inspect container
docker-compose exec backend sh

# Check logs
docker-compose logs backend
```

## Security Considerations
- Never commit `.env` to version control
- Use strong, unique secrets
- Limit container network access
- Regularly update dependencies

## Performance Tuning
- Adjust `workers` in Gunicorn configuration
- Monitor container resource usage
- Implement caching strategies

## Scaling
For future scaling:
- Use external databases
- Implement load balancing
- Consider Kubernetes for advanced orchestration