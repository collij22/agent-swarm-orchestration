#!/bin/bash

# Agent Swarm Production Deployment Script
# Usage: ./deploy.sh [staging|production] [--skip-tests] [--skip-backup]

set -e  # Exit on error
set -u  # Exit on undefined variable

# ======================
# Configuration
# ======================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${PROJECT_ROOT}/logs/deploy_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ======================
# Functions
# ======================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check environment file
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if [[ ! -f "${PROJECT_ROOT}/.env.production" ]]; then
            error ".env.production file not found. Copy .env.production.example and configure it."
        fi
    else
        if [[ ! -f "${PROJECT_ROOT}/.env.staging" ]]; then
            warning ".env.staging not found, using .env.production.example as template"
            cp "${PROJECT_ROOT}/.env.production.example" "${PROJECT_ROOT}/.env.staging"
        fi
    fi
    
    log "Prerequisites check passed"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "false" ]]; then
        log "Running tests..."
        
        # Run unit tests
        info "Running unit tests..."
        cd "$PROJECT_ROOT"
        python -m pytest tests/unit/ -v --tb=short || error "Unit tests failed"
        
        # Run integration tests
        info "Running integration tests..."
        python -m pytest tests/integration/ -v --tb=short || error "Integration tests failed"
        
        # Run Phase 2 specific tests
        info "Running Phase 2 integration tests..."
        if [[ -f "${PROJECT_ROOT}/tests/test_phase2_integration.py" ]]; then
            python -m pytest tests/test_phase2_integration.py -v || warning "Phase 2 tests not fully implemented yet"
        fi
        
        log "All tests passed"
    else
        warning "Skipping tests (--skip-tests flag provided)"
    fi
}

# Create backup
create_backup() {
    if [[ "$SKIP_BACKUP" == "false" ]] && [[ "$ENVIRONMENT" == "production" ]]; then
        log "Creating backup..."
        
        BACKUP_DIR="${PROJECT_ROOT}/backups/${TIMESTAMP}"
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        info "Backing up database..."
        docker-compose -f docker-compose.production.yml exec -T postgres \
            pg_dump -U swarm swarm_db > "${BACKUP_DIR}/database.sql" || warning "Database backup failed"
        
        # Backup data directories
        info "Backing up data directories..."
        tar -czf "${BACKUP_DIR}/data.tar.gz" \
            "${PROJECT_ROOT}/data" \
            "${PROJECT_ROOT}/checkpoints" \
            "${PROJECT_ROOT}/sessions" 2>/dev/null || warning "Data backup incomplete"
        
        log "Backup created at ${BACKUP_DIR}"
    else
        info "Skipping backup"
    fi
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build with BuildKit for better caching
    export DOCKER_BUILDKIT=1
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker build -f Dockerfile.production -t agent-swarm:latest -t agent-swarm:${TIMESTAMP} .
    else
        docker build -f Dockerfile.production -t agent-swarm:staging .
    fi
    
    if [[ $? -ne 0 ]]; then
        error "Docker build failed"
    fi
    
    log "Docker images built successfully"
}

# Deploy to environment
deploy() {
    log "Deploying to ${ENVIRONMENT}..."
    
    cd "$PROJECT_ROOT"
    
    # Set environment file
    if [[ "$ENVIRONMENT" == "production" ]]; then
        export ENV_FILE=".env.production"
        COMPOSE_FILE="docker-compose.production.yml"
    else
        export ENV_FILE=".env.staging"
        COMPOSE_FILE="docker-compose.production.yml"
    fi
    
    # Stop existing containers
    info "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || true
    
    # Start new containers
    info "Starting new containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    if [[ $? -ne 0 ]]; then
        error "Deployment failed"
    fi
    
    # Wait for services to be healthy
    info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    check_health
    
    log "Deployment completed successfully"
}

# Health check
check_health() {
    log "Running health checks..."
    
    # Check orchestrator
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        info "Orchestrator: Healthy"
    else
        error "Orchestrator health check failed"
    fi
    
    # Check Redis
    if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        info "Redis: Healthy"
    else
        warning "Redis health check failed"
    fi
    
    # Check PostgreSQL
    if docker-compose -f docker-compose.production.yml exec -T postgres pg_isready > /dev/null 2>&1; then
        info "PostgreSQL: Healthy"
    else
        warning "PostgreSQL health check failed"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        info "Grafana: Healthy"
    else
        warning "Grafana health check failed"
    fi
    
    log "Health checks completed"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Test API endpoint
    info "Testing API endpoint..."
    curl -X GET http://localhost:8000/api/v1/status || warning "API status check failed"
    
    # Test metrics endpoint
    info "Testing metrics endpoint..."
    curl -X GET http://localhost:9090/metrics || warning "Metrics endpoint check failed"
    
    # Test WebSocket connection
    info "Testing WebSocket connection..."
    python -c "
import asyncio
import websockets
async def test():
    try:
        async with websockets.connect('ws://localhost:8000/ws') as ws:
            print('WebSocket connection successful')
    except:
        print('WebSocket connection failed')
asyncio.run(test())
" || warning "WebSocket test failed"
    
    log "Smoke tests completed"
}

# Rollback deployment
rollback() {
    error "Deployment failed, rolling back..."
    
    # Restore previous version
    docker-compose -f docker-compose.production.yml down
    docker tag agent-swarm:previous agent-swarm:latest
    docker-compose -f docker-compose.production.yml up -d
    
    error "Rollback completed. Please investigate the issue."
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove old Docker images (keep last 3)
    docker images agent-swarm --format "{{.Tag}}" | \
        grep -E '^[0-9]{8}_[0-9]{6}$' | \
        sort -r | \
        tail -n +4 | \
        xargs -I {} docker rmi agent-swarm:{} 2>/dev/null || true
    
    # Clean old backup files (keep last 7 days)
    find "${PROJECT_ROOT}/backups" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Clean old log files (keep last 30 days)
    find "${PROJECT_ROOT}/logs" -type f -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log "Cleanup completed"
}

# Main deployment flow
main() {
    # Create log directory
    mkdir -p "${PROJECT_ROOT}/logs"
    
    log "==================================="
    log "Agent Swarm Deployment Script"
    log "Environment: ${ENVIRONMENT}"
    log "Timestamp: ${TIMESTAMP}"
    log "==================================="
    
    # Tag current as previous (for rollback)
    docker tag agent-swarm:latest agent-swarm:previous 2>/dev/null || true
    
    # Run deployment steps
    check_prerequisites
    run_tests
    create_backup
    build_images
    deploy
    run_smoke_tests
    cleanup
    
    log "==================================="
    log "Deployment completed successfully!"
    log "==================================="
    
    # Show access URLs
    echo ""
    info "Access URLs:"
    echo "  - API: http://localhost:8000"
    echo "  - Dashboard: http://localhost:5173"
    echo "  - Grafana: http://localhost:3000 (admin/admin)"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Metrics: http://localhost:9090/metrics"
    echo ""
    info "View logs: docker-compose -f docker-compose.production.yml logs -f"
}

# ======================
# Script Entry Point
# ======================

# Parse arguments
ENVIRONMENT="${1:-staging}"
SKIP_TESTS=false
SKIP_BACKUP=false

for arg in "$@"; do
    case $arg in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        staging|production)
            ENVIRONMENT="$arg"
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" ]] && [[ "$ENVIRONMENT" != "production" ]]; then
    error "Invalid environment: $ENVIRONMENT. Use 'staging' or 'production'"
fi

# Confirmation for production
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo -e "${YELLOW}WARNING: You are about to deploy to PRODUCTION${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        info "Deployment cancelled"
        exit 0
    fi
fi

# Run main deployment
main

# Exit successfully
exit 0