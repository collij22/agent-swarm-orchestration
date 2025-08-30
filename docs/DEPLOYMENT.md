# DevPortfolio Deployment Guide

## Overview

This guide covers deploying DevPortfolio to production using a multi-platform approach:
- **Frontend**: Vercel (Next.js with edge caching)
- **Backend**: Railway/DigitalOcean (FastAPI with Docker)
- **Database**: PostgreSQL with Redis cache
- **CDN**: CloudFlare for global delivery
- **Monitoring**: Prometheus + Grafana

## Prerequisites

### Required Software
- Docker & Docker Compose
- Node.js 18+ and npm
- Git
- curl (for health checks)

### Required Accounts
- GitHub (for repository and OAuth)
- Vercel (for frontend hosting)
- Railway or DigitalOcean (for backend hosting)
- CloudFlare (for CDN and DNS)
- OpenAI (for AI features)

## Environment Setup

### 1. Environment Variables

Create `.env.production` file:

```bash
# Core Configuration
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database & Cache
DATABASE_URL=postgresql://user:pass@host:5432/devportfolio
REDIS_URL=redis://host:6379

# External APIs
OPENAI_API_KEY=sk-your-openai-key
GITHUB_CLIENT_ID=your-github-oauth-id
GITHUB_CLIENT_SECRET=your-github-oauth-secret
GOOGLE_CLIENT_ID=your-google-oauth-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret

# Frontend URLs
FRONTEND_URL=https://devportfolio.com
CORS_ORIGINS=https://devportfolio.com,https://www.devportfolio.com

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password
SENTRY_DSN=https://your-sentry-dsn

# Notifications
SLACK_WEBHOOK=https://hooks.slack.com/your-webhook
```

### 2. SSL Certificates

For production deployment with custom domain:

```bash
# Using Let's Encrypt (recommended)
sudo certbot certonly --webroot -w /var/www/html -d devportfolio.com -d www.devportfolio.com

# Copy certificates to project
mkdir -p ssl
sudo cp /etc/letsencrypt/live/devportfolio.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/devportfolio.com/privkey.pem ssl/
```

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/devportfolio.git
cd devportfolio

# Set environment variables
source .env.production

# Run deployment script
./scripts/deploy.sh production
```

### Method 2: Manual Deployment

#### Backend Deployment (Railway)

1. **Setup Railway Project**
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   ```

2. **Configure Services**
   ```bash
   railway add --service postgres
   railway add --service redis
   railway deploy
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set SECRET_KEY="your-secret-key"
   railway variables set OPENAI_API_KEY="your-openai-key"
   # ... set all required variables
   ```

#### Frontend Deployment (Vercel)

1. **Setup Vercel Project**
   ```bash
   cd frontend
   npm install -g vercel
   vercel login
   vercel --prod
   ```

2. **Configure Environment Variables**
   ```bash
   vercel env add NEXT_PUBLIC_API_URL production
   vercel env add NEXT_PUBLIC_FRONTEND_URL production
   ```

3. **Setup Custom Domain**
   - Add domain in Vercel dashboard
   - Configure DNS in CloudFlare

### Method 3: Self-Hosted Docker

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
"

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

## Post-Deployment Setup

### 1. Domain Configuration

**CloudFlare DNS Settings:**
```
Type    Name    Content                 TTL
A       @       your-server-ip          Auto
A       www     your-server-ip          Auto
CNAME   api     backend.railway.app     Auto
```

**CloudFlare Page Rules:**
- `devportfolio.com/*`  ->  Always Use HTTPS
- `www.devportfolio.com/*`  ->  Forwarding URL to `https://devportfolio.com/$1`

### 2. Monitoring Setup

Access monitoring dashboards:
- **Grafana**: `http://your-server:3000` (admin/your-password)
- **Prometheus**: `http://your-server:9090`

Import dashboard:
1. Login to Grafana
2. Import `monitoring/grafana/provisioning/dashboards/devportfolio-dashboard.json`

### 3. SSL Certificate Renewal

Setup automatic renewal:
```bash
# Add to crontab
0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook "docker-compose -f /path/to/docker-compose.prod.yml restart nginx"
```

## CI/CD Pipeline

The GitHub Actions workflow automatically:
1. Runs tests on push/PR
2. Builds and pushes Docker images
3. Deploys to staging (develop branch)
4. Deploys to production (main branch)

**Required GitHub Secrets:**
```
RAILWAY_TOKEN
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
GITHUB_TOKEN
SLACK_WEBHOOK
```

## Health Checks

### Automated Monitoring

The system includes comprehensive monitoring:
- **Application Health**: `/health` endpoint
- **Database**: Connection and query performance
- **External APIs**: OpenAI and GitHub API status
- **SSL Certificates**: Expiry monitoring
- **System Resources**: CPU, memory, disk usage

### Manual Verification

```bash
# Check backend health
curl -f https://api.devportfolio.com/health

# Check frontend
curl -f https://devportfolio.com

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Performance Optimization

### 1. CDN Configuration

**CloudFlare Settings:**
- Caching Level: Standard
- Browser Cache TTL: 1 year for static assets
- Always Online: Enabled
- Minification: CSS, HTML, JS enabled

### 2. Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published_at DESC) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_projects_featured ON projects(featured DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date DESC);
```

### 3. Redis Caching

Key caching strategies implemented:
- Blog posts: 1 hour TTL
- Project data: 6 hours TTL
- GitHub data: 30 minutes TTL
- Analytics: 5 minutes TTL

## Backup and Recovery

### Automated Backups

```bash
# Database backup (runs daily via cron)
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres devportfolio > $BACKUP_DIR/database.sql
tar -czf $BACKUP_DIR/uploads.tar.gz uploads/
```

### Recovery Process

```bash
# Restore database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d devportfolio < backup/database.sql

# Restore uploads
tar -xzf backup/uploads.tar.gz
```

## Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check resource usage
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

**2. Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check connection from backend
docker-compose -f docker-compose.prod.yml exec backend python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://...')
    print('Connected successfully')
asyncio.run(test())
"
```

**3. High Memory Usage**
```bash
# Check container memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Optimize PostgreSQL memory
# Add to docker-compose.prod.yml postgres service:
command: postgres -c shared_buffers=256MB -c effective_cache_size=1GB
```

**4. SSL Certificate Issues**
```bash
# Check certificate expiry
openssl x509 -in ssl/fullchain.pem -text -noout | grep "Not After"

# Test SSL configuration
curl -vI https://devportfolio.com
```

### Performance Issues

**1. Slow API Responses**
- Check Prometheus metrics at `:9090`
- Review slow query logs
- Verify Redis cache hit rates
- Check external API latency

**2. High CPU Usage**
- Review application logs for errors
- Check for infinite loops or inefficient queries
- Monitor background tasks
- Consider horizontal scaling

### Monitoring Alerts

Critical alerts will be sent to Slack webhook:
- Service downtime
- High error rates (>10%)
- Resource exhaustion (>85% memory/CPU)
- SSL certificate expiry (<7 days)
- Database connection failures

## Security Considerations

### 1. Network Security
- All traffic encrypted with HTTPS
- Rate limiting on API endpoints
- CORS properly configured
- Security headers implemented

### 2. Application Security
- JWT tokens with proper expiry
- SQL injection prevention
- XSS protection
- Input validation and sanitization

### 3. Infrastructure Security
- Regular dependency updates
- Container security scanning
- Secrets management
- Access control and monitoring

## Cost Optimization

**Monthly Cost Breakdown (Target: $50/month)**
- Railway/DigitalOcean: $25/month (backend + database)
- Vercel: $0/month (hobby plan)
- CloudFlare: $0/month (free plan)
- OpenAI API: $20/month (estimated usage)
- Total: $45/month (within budget)

**Cost Monitoring:**
- Set up billing alerts
- Monitor API usage
- Optimize image sizes
- Use CDN caching effectively

## Support and Maintenance

### Regular Tasks
- **Weekly**: Review monitoring dashboards and alerts
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Performance review and optimization
- **Annually**: SSL certificate renewal and security audit

### Getting Help
- Check application logs first
- Review monitoring dashboards
- Consult this documentation
- Check GitHub Issues for known problems

---

For additional support or questions, please refer to the project documentation or create an issue in the GitHub repository.