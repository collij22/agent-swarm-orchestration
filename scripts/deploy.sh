#!/bin/bash

# DevPortfolio Production Deployment Script
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || error "Docker is required but not installed."
    command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is required but not installed."
    command -v curl >/dev/null 2>&1 || error "curl is required but not installed."
    
    success "Prerequisites check passed"
}

# Validate environment variables
validate_environment() {
    log "Validating environment variables..."
    
    required_vars=(
        "SECRET_KEY"
        "DATABASE_URL"
        "REDIS_URL"
        "OPENAI_API_KEY"
        "GITHUB_CLIENT_ID"
        "GITHUB_CLIENT_SECRET"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables: ${missing_vars[*]}"
    fi
    
    success "Environment validation passed"
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    if [[ ! -d "ssl" ]]; then
        mkdir -p ssl
    fi
    
    if [[ ! -f "ssl/fullchain.pem" || ! -f "ssl/privkey.pem" ]]; then
        warn "SSL certificates not found. Please ensure certificates are in ssl/ directory"
        warn "For Let's Encrypt: certbot certonly --webroot -w /var/www/html -d devportfolio.com"
    else
        success "SSL certificates found"
    fi
}

# Database migration
run_migrations() {
    log "Running database migrations..."
    
    docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
"
    
    success "Database migrations completed"
}

# Health check
health_check() {
    log "Performing health checks..."
    
    max_attempts=30
    attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost/health >/dev/null 2>&1; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
}

# Backup current deployment
backup_current() {
    log "Creating backup of current deployment..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backups/deployment_$timestamp"
    
    mkdir -p "$backup_dir"
    
    # Backup database
    docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres devportfolio > "$backup_dir/database.sql"
    
    # Backup uploaded files
    if [[ -d "uploads" ]]; then
        cp -r uploads "$backup_dir/"
    fi
    
    success "Backup created at $backup_dir"
}

# Deploy application
deploy() {
    log "Starting deployment for $ENVIRONMENT environment..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest images
    log "Pulling latest Docker images..."
    docker-compose -f docker-compose.prod.yml pull
    
    # Stop current services
    log "Stopping current services..."
    docker-compose -f docker-compose.prod.yml down
    
    # Start new services
    log "Starting new services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    success "Deployment completed"
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old Docker images and containers..."
    
    docker system prune -f
    docker image prune -f
    
    success "Cleanup completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Ensure monitoring directories exist
    mkdir -p logs/nginx logs/app
    
    # Start monitoring services if not already running
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q prometheus; then
        docker-compose -f docker-compose.prod.yml up -d prometheus grafana
    fi
    
    success "Monitoring setup completed"
}

# Main deployment flow
main() {
    log "Starting DevPortfolio deployment to $ENVIRONMENT..."
    
    check_prerequisites
    validate_environment
    setup_ssl
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        backup_current
    fi
    
    deploy
    run_migrations
    setup_monitoring
    health_check
    cleanup
    
    success "Deployment to $ENVIRONMENT completed successfully!"
    
    log "Application URLs:"
    log "  Frontend: https://devportfolio.com"
    log "  API: https://devportfolio.com/api"
    log "  Admin: https://devportfolio.com/admin"
    log "  Monitoring: http://localhost:3000 (Grafana)"
    log "  Metrics: http://localhost:9090 (Prometheus)"
}

# Handle script interruption
trap 'error "Deployment interrupted"' INT TERM

# Run main function
main "$@"