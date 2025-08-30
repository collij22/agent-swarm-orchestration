#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
LOG_DIR="./logs"
SSL_DIR="./nginx/ssl"
ENV_FILE=".env.prod"

echo -e "${GREEN}🚀 TaskManager API Production Deployment${NC}"
echo "=================================================="

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}[DONE] Prerequisites check passed${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p $BACKUP_DIR $LOG_DIR/{nginx,backend} $SSL_DIR
echo -e "${GREEN}[DONE] Directories created${NC}"

# Check environment file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file $ENV_FILE not found${NC}"
    echo "Please create $ENV_FILE with the following variables:"
    echo "JWT_SECRET_KEY=your-secret-key"
    echo "OPENAI_API_KEY=your-openai-key"
    echo "GRAFANA_PASSWORD=your-grafana-password"
    echo "REDIS_PASSWORD=your-redis-password"
    echo "API_URL=https://your-domain.com/api/v1"
    echo "CORS_ORIGINS=https://your-domain.com"
    exit 1
fi

# Source environment variables
source $ENV_FILE
echo -e "${GREEN}[DONE] Environment variables loaded${NC}"

# Generate SSL certificates if not exist
if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo -e "${YELLOW}Generating self-signed SSL certificates...${NC}"
    openssl req -x509 -newkey rsa:4096 -keyout $SSL_DIR/key.pem -out $SSL_DIR/cert.pem -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo -e "${GREEN}[DONE] SSL certificates generated${NC}"
fi

# Create nginx auth file for monitoring
echo -e "${YELLOW}Setting up monitoring authentication...${NC}"
if [ ! -f "nginx/.htpasswd" ]; then
    # Default: admin/admin123 (change in production)
    echo 'admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/' > nginx/.htpasswd
    echo -e "${YELLOW}⚠️  Default monitoring credentials: admin/admin123${NC}"
    echo -e "${YELLOW}⚠️  Please change these in production!${NC}"
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker-compose -f docker-compose.prod.yml pull
echo -e "${GREEN}[DONE] Images pulled${NC}"

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down
echo -e "${GREEN}[DONE] Containers stopped${NC}"

# Start services
echo -e "${YELLOW}Starting production services...${NC}"
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}[DONE] Services started${NC}"

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 30

# Health checks
echo -e "${YELLOW}Performing health checks...${NC}"

# Check backend health
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}[DONE] Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs backend
fi

# Check frontend
if curl -f -s http://localhost > /dev/null; then
    echo -e "${GREEN}[DONE] Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend is not accessible${NC}"
fi

# Check monitoring services
if curl -f -s http://localhost:9090 > /dev/null; then
    echo -e "${GREEN}[DONE] Prometheus is running${NC}"
else
    echo -e "${RED}❌ Prometheus is not accessible${NC}"
fi

if curl -f -s http://localhost:3001 > /dev/null; then
    echo -e "${GREEN}[DONE] Grafana is running${NC}"
else
    echo -e "${RED}❌ Grafana is not accessible${NC}"
fi

# Display service URLs
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================================="
echo -e "${GREEN}Service URLs:${NC}"
echo "• Application: https://localhost"
echo "• API Documentation: https://localhost/docs"
echo "• Prometheus: http://localhost:9090"
echo "• Grafana: http://localhost:3001 (admin/admin123)"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "• Change default passwords in production"
echo "• Configure proper SSL certificates"
echo "• Set up external backup storage"
echo "• Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo -e "${GREEN}[DONE] Production deployment ready!${NC}"