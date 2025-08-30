#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Enhanced Single File Agent: DevOps Engineer
Section 6 Implementation - Docker Configuration & Testing Infrastructure

Comprehensive DevOps automation with production-ready Docker configurations
and complete testing infrastructure generation.

Example Usage:
    uv run sfa/sfa_devops_engineer_enhanced.py --project-path /path/to/project --generate docker
    uv run sfa/sfa_devops_engineer_enhanced.py --project-path /path/to/project --generate testing
    uv run sfa/sfa_devops_engineer_enhanced.py --project-path /path/to/project --generate all --verbose
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import yaml
import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: Anthropic not installed. Running in simulation mode.")

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize console
console = Console()

@dataclass
class ProjectAnalysis:
    """Analysis of the project structure"""
    language: str  # python, javascript, typescript
    framework: str  # fastapi, express, django, etc.
    has_database: bool
    database_type: Optional[str]  # postgresql, mysql, mongodb
    has_redis: bool
    has_frontend: bool
    frontend_framework: Optional[str]  # react, vue, angular
    services: List[str]  # List of services identified
    dependencies: Dict[str, List[str]]  # Language -> dependencies
    api_endpoints: List[str]  # Detected API endpoints
    environment_vars: List[str]  # Required environment variables

class EnhancedDevOpsEngineer:
    """Enhanced DevOps Engineer with Section 6 Implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None
        self.generated_files = {}
        
    def analyze_project(self, project_path: Path) -> ProjectAnalysis:
        """Analyze project structure to determine configuration needs"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=False,
            database_type=None,
            has_redis=False,
            has_frontend=False,
            frontend_framework=None,
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        # Check for Python project
        if (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists():
            analysis.language = "python"
            analysis.dependencies["python"] = self._parse_python_deps(project_path)
            
            # Detect framework
            deps_text = " ".join(analysis.dependencies["python"]).lower()
            if "fastapi" in deps_text:
                analysis.framework = "fastapi"
            elif "django" in deps_text:
                analysis.framework = "django"
            elif "flask" in deps_text:
                analysis.framework = "flask"
                
        # Check for Node.js project
        elif (project_path / "package.json").exists():
            analysis.language = "javascript"
            pkg_json = json.loads((project_path / "package.json").read_text())
            analysis.dependencies["javascript"] = list(pkg_json.get("dependencies", {}).keys())
            
            # Detect framework
            deps = analysis.dependencies["javascript"]
            if "express" in deps:
                analysis.framework = "express"
            elif "fastify" in deps:
                analysis.framework = "fastify"
            elif "@nestjs/core" in deps:
                analysis.framework = "nestjs"
                
        # Check for database
        all_deps = " ".join([" ".join(deps) for deps in analysis.dependencies.values()]).lower()
        if "postgres" in all_deps or "psycopg" in all_deps or "pg" in all_deps:
            analysis.has_database = True
            analysis.database_type = "postgresql"
        elif "mysql" in all_deps or "pymysql" in all_deps:
            analysis.has_database = True
            analysis.database_type = "mysql"
        elif "mongodb" in all_deps or "pymongo" in all_deps:
            analysis.has_database = True
            analysis.database_type = "mongodb"
            
        # Check for Redis
        if "redis" in all_deps:
            analysis.has_redis = True
            
        # Check for frontend
        if (project_path / "frontend").exists() or (project_path / "client").exists():
            analysis.has_frontend = True
            frontend_path = project_path / "frontend" if (project_path / "frontend").exists() else project_path / "client"
            
            if (frontend_path / "package.json").exists():
                pkg_json = json.loads((frontend_path / "package.json").read_text())
                deps = list(pkg_json.get("dependencies", {}).keys())
                if "react" in deps:
                    analysis.frontend_framework = "react"
                elif "vue" in deps:
                    analysis.frontend_framework = "vue"
                elif "@angular/core" in deps:
                    analysis.frontend_framework = "angular"
                    
        # Identify services
        if analysis.framework:
            analysis.services.append(f"{analysis.framework}-api")
        if analysis.has_database:
            analysis.services.append(analysis.database_type)
        if analysis.has_redis:
            analysis.services.append("redis")
        if analysis.has_frontend:
            analysis.services.append(f"{analysis.frontend_framework or 'frontend'}-app")
            
        # Detect API endpoints (simplified)
        analysis.api_endpoints = self._detect_api_endpoints(project_path, analysis.framework)
        
        # Detect environment variables
        analysis.environment_vars = self._detect_env_vars(project_path)
        
        return analysis
    
    def _parse_python_deps(self, project_path: Path) -> List[str]:
        """Parse Python dependencies"""
        deps = []
        
        if (project_path / "requirements.txt").exists():
            content = (project_path / "requirements.txt").read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before any version specifier)
                    pkg = re.split(r'[<>=!]', line)[0].strip()
                    if pkg:
                        deps.append(pkg)
                        
        if (project_path / "pyproject.toml").exists():
            # Simple TOML parsing for dependencies
            content = (project_path / "pyproject.toml").read_text()
            in_deps = False
            for line in content.splitlines():
                if "[tool.poetry.dependencies]" in line or "[project.dependencies]" in line:
                    in_deps = True
                elif line.startswith("[") and in_deps:
                    in_deps = False
                elif in_deps and "=" in line:
                    pkg = line.split("=")[0].strip().strip('"')
                    if pkg and pkg != "python":
                        deps.append(pkg)
                        
        return deps
    
    def _detect_api_endpoints(self, project_path: Path, framework: str) -> List[str]:
        """Detect API endpoints from code"""
        endpoints = []
        
        # Search for route definitions based on framework
        patterns = {
            "fastapi": [r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)', r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)'],
            "flask": [r'@app\.route\(["\']([^"\']+)'],
            "express": [r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)'],
            "django": [r'path\(["\']([^"\']+)']
        }
        
        if framework in patterns:
            # Search Python/JS files
            extensions = [".py"] if framework in ["fastapi", "flask", "django"] else [".js", ".ts"]
            
            for ext in extensions:
                for file_path in project_path.rglob(f"*{ext}"):
                    if "node_modules" not in str(file_path) and ".venv" not in str(file_path):
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            for pattern in patterns[framework]:
                                matches = re.findall(pattern, content)
                                for match in matches:
                                    endpoint = match[1] if isinstance(match, tuple) else match
                                    if endpoint and not endpoint.startswith("http"):
                                        endpoints.append(endpoint)
                        except:
                            pass
                            
        return list(set(endpoints))[:20]  # Return unique endpoints, max 20
    
    def _detect_env_vars(self, project_path: Path) -> List[str]:
        """Detect environment variables used in the project"""
        env_vars = set()
        
        # Check .env.example or .env files
        for env_file in [".env.example", ".env", ".env.sample"]:
            env_path = project_path / env_file
            if env_path.exists():
                content = env_path.read_text()
                for line in content.splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        var_name = line.split("=")[0].strip()
                        if var_name:
                            env_vars.add(var_name)
                            
        # Search for os.getenv or process.env usage
        patterns = [
            r'os\.getenv\(["\']([^"\']+)',
            r'os\.environ\[["\']([^"\']+)',
            r'process\.env\.([A-Z_]+)',
            r'process\.env\[["\']([^"\']+)'
        ]
        
        for file_path in project_path.rglob("*"):
            if file_path.suffix in [".py", ".js", ".ts"] and "node_modules" not in str(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        env_vars.update(matches)
                except:
                    pass
                    
        return sorted(list(env_vars))
    
    def generate_dockerfile(self, analysis: ProjectAnalysis, service: str = "main") -> str:
        """Generate production-ready Dockerfile"""
        
        if analysis.language == "python":
            if analysis.framework == "fastapi":
                return self._dockerfile_python_fastapi(analysis)
            elif analysis.framework == "django":
                return self._dockerfile_python_django(analysis)
            else:
                return self._dockerfile_python_generic(analysis)
        elif analysis.language == "javascript":
            if analysis.frontend_framework:
                return self._dockerfile_node_frontend(analysis)
            else:
                return self._dockerfile_node_backend(analysis)
        else:
            return self._dockerfile_generic()
    
    def _dockerfile_python_fastapi(self, analysis: ProjectAnalysis) -> str:
        """Generate Dockerfile for FastAPI application"""
        return """# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _dockerfile_python_django(self, analysis: ProjectAnalysis) -> str:
        """Generate Dockerfile for Django application"""
        return """# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python manage.py check || exit 1

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 4 project.wsgi:application"]
"""
    
    def _dockerfile_python_generic(self, analysis: ProjectAnalysis) -> str:
        """Generate generic Python Dockerfile"""
        return """# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
"""
    
    def _dockerfile_node_backend(self, analysis: ProjectAnalysis) -> str:
        """Generate Dockerfile for Node.js backend"""
        return """# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Runtime stage
FROM node:18-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \\
    adduser -S nodejs -u 1001

# Copy dependencies
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy application code
COPY --chown=nodejs:nodejs . .

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})" || exit 1

# Run the application
CMD ["node", "index.js"]
"""
    
    def _dockerfile_node_frontend(self, analysis: ProjectAnalysis) -> str:
        """Generate Dockerfile for Node.js frontend (React/Vue/Angular)"""
        return """# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Runtime stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
"""
    
    def _dockerfile_generic(self) -> str:
        """Generate generic Dockerfile"""
        return """FROM ubuntu:22.04

WORKDIR /app

# Install basic tools
RUN apt-get update && apt-get install -y \\
    curl \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Expose common port
EXPOSE 8080

# Default command
CMD ["/bin/bash"]
"""
    
    def generate_docker_compose(self, analysis: ProjectAnalysis) -> str:
        """Generate comprehensive docker-compose.yml"""
        services = {}
        
        # Main application service
        app_service = {
            "build": {
                "context": ".",
                "dockerfile": "Dockerfile"
            },
            "ports": ["8000:8000"] if analysis.language == "python" else ["3000:3000"],
            "environment": {
                "NODE_ENV": "${NODE_ENV:-production}" if analysis.language == "javascript" else "PYTHONUNBUFFERED=1"
            },
            "env_file": [".env"],
            "restart": "unless-stopped",
            "networks": ["app-network"]
        }
        
        # Add depends_on if we have dependencies
        depends_on = []
        
        # Add database service
        if analysis.has_database:
            if analysis.database_type == "postgresql":
                services["postgres"] = {
                    "image": "postgres:15-alpine",
                    "environment": {
                        "POSTGRES_DB": "${POSTGRES_DB:-appdb}",
                        "POSTGRES_USER": "${POSTGRES_USER:-appuser}",
                        "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-changeme}"
                    },
                    "volumes": [
                        "postgres_data:/var/lib/postgresql/data",
                        "./init.sql:/docker-entrypoint-initdb.d/init.sql:ro"
                    ],
                    "ports": ["5432:5432"],
                    "restart": "unless-stopped",
                    "networks": ["app-network"],
                    "healthcheck": {
                        "test": ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-appuser}"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                }
                depends_on.append("postgres")
                app_service["environment"]["DATABASE_URL"] = "postgresql://${POSTGRES_USER:-appuser}:${POSTGRES_PASSWORD:-changeme}@postgres:5432/${POSTGRES_DB:-appdb}"
                
            elif analysis.database_type == "mysql":
                services["mysql"] = {
                    "image": "mysql:8.0",
                    "environment": {
                        "MYSQL_DATABASE": "${MYSQL_DATABASE:-appdb}",
                        "MYSQL_USER": "${MYSQL_USER:-appuser}",
                        "MYSQL_PASSWORD": "${MYSQL_PASSWORD:-changeme}",
                        "MYSQL_ROOT_PASSWORD": "${MYSQL_ROOT_PASSWORD:-rootpass}"
                    },
                    "volumes": [
                        "mysql_data:/var/lib/mysql",
                        "./init.sql:/docker-entrypoint-initdb.d/init.sql:ro"
                    ],
                    "ports": ["3306:3306"],
                    "restart": "unless-stopped",
                    "networks": ["app-network"],
                    "healthcheck": {
                        "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                }
                depends_on.append("mysql")
                app_service["environment"]["DATABASE_URL"] = "mysql://${MYSQL_USER:-appuser}:${MYSQL_PASSWORD:-changeme}@mysql:3306/${MYSQL_DATABASE:-appdb}"
                
            elif analysis.database_type == "mongodb":
                services["mongodb"] = {
                    "image": "mongo:6.0",
                    "environment": {
                        "MONGO_INITDB_ROOT_USERNAME": "${MONGO_USERNAME:-admin}",
                        "MONGO_INITDB_ROOT_PASSWORD": "${MONGO_PASSWORD:-changeme}",
                        "MONGO_INITDB_DATABASE": "${MONGO_DATABASE:-appdb}"
                    },
                    "volumes": [
                        "mongo_data:/data/db",
                        "./init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro"
                    ],
                    "ports": ["27017:27017"],
                    "restart": "unless-stopped",
                    "networks": ["app-network"],
                    "healthcheck": {
                        "test": ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                }
                depends_on.append("mongodb")
                app_service["environment"]["MONGODB_URL"] = "mongodb://${MONGO_USERNAME:-admin}:${MONGO_PASSWORD:-changeme}@mongodb:27017/${MONGO_DATABASE:-appdb}?authSource=admin"
        
        # Add Redis service
        if analysis.has_redis:
            services["redis"] = {
                "image": "redis:7-alpine",
                "command": "redis-server --appendonly yes",
                "volumes": ["redis_data:/data"],
                "ports": ["6379:6379"],
                "restart": "unless-stopped",
                "networks": ["app-network"],
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5
                }
            }
            depends_on.append("redis")
            app_service["environment"]["REDIS_URL"] = "redis://redis:6379"
        
        # Add frontend service
        if analysis.has_frontend:
            services["frontend"] = {
                "build": {
                    "context": "./frontend",
                    "dockerfile": "Dockerfile"
                },
                "ports": ["3000:80"],
                "environment": {
                    "REACT_APP_API_URL": "${API_URL:-http://localhost:8000}"
                },
                "restart": "unless-stopped",
                "networks": ["app-network"],
                "depends_on": ["app"]
            }
        
        # Add depends_on to app service
        if depends_on:
            app_service["depends_on"] = depends_on
        
        # Add app service
        services["app"] = app_service
        
        # Create complete docker-compose structure
        compose = {
            "version": "3.8",
            "services": services,
            "networks": {
                "app-network": {
                    "driver": "bridge"
                }
            },
            "volumes": {}
        }
        
        # Add volumes
        if analysis.has_database:
            if analysis.database_type == "postgresql":
                compose["volumes"]["postgres_data"] = {}
            elif analysis.database_type == "mysql":
                compose["volumes"]["mysql_data"] = {}
            elif analysis.database_type == "mongodb":
                compose["volumes"]["mongo_data"] = {}
        
        if analysis.has_redis:
            compose["volumes"]["redis_data"] = {}
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def generate_env_template(self, analysis: ProjectAnalysis) -> str:
        """Generate .env.example template"""
        env_vars = []
        
        # Application settings
        env_vars.append("# Application Settings")
        env_vars.append("NODE_ENV=production" if analysis.language == "javascript" else "ENVIRONMENT=production")
        env_vars.append("PORT=8000" if analysis.language == "python" else "PORT=3000")
        env_vars.append("SECRET_KEY=your-secret-key-here")
        env_vars.append("")
        
        # Database settings
        if analysis.has_database:
            env_vars.append("# Database Settings")
            if analysis.database_type == "postgresql":
                env_vars.append("POSTGRES_DB=appdb")
                env_vars.append("POSTGRES_USER=appuser")
                env_vars.append("POSTGRES_PASSWORD=changeme")
                env_vars.append("DATABASE_URL=postgresql://appuser:changeme@localhost:5432/appdb")
            elif analysis.database_type == "mysql":
                env_vars.append("MYSQL_DATABASE=appdb")
                env_vars.append("MYSQL_USER=appuser")
                env_vars.append("MYSQL_PASSWORD=changeme")
                env_vars.append("MYSQL_ROOT_PASSWORD=rootpass")
                env_vars.append("DATABASE_URL=mysql://appuser:changeme@localhost:3306/appdb")
            elif analysis.database_type == "mongodb":
                env_vars.append("MONGO_USERNAME=admin")
                env_vars.append("MONGO_PASSWORD=changeme")
                env_vars.append("MONGO_DATABASE=appdb")
                env_vars.append("MONGODB_URL=mongodb://admin:changeme@localhost:27017/appdb?authSource=admin")
            env_vars.append("")
        
        # Redis settings
        if analysis.has_redis:
            env_vars.append("# Redis Settings")
            env_vars.append("REDIS_URL=redis://localhost:6379")
            env_vars.append("")
        
        # API settings
        if analysis.has_frontend:
            env_vars.append("# API Settings")
            env_vars.append("API_URL=http://localhost:8000")
            env_vars.append("CORS_ORIGINS=http://localhost:3000")
            env_vars.append("")
        
        # Add detected environment variables
        if analysis.environment_vars:
            env_vars.append("# Detected Environment Variables")
            for var in analysis.environment_vars:
                if var not in "\n".join(env_vars):
                    env_vars.append(f"{var}=")
            env_vars.append("")
        
        # Additional common settings
        env_vars.append("# Additional Settings")
        env_vars.append("LOG_LEVEL=info")
        env_vars.append("MAX_WORKERS=4")
        env_vars.append("TIMEOUT=30")
        
        return "\n".join(env_vars)
    
    def generate_nginx_config(self, analysis: ProjectAnalysis) -> str:
        """Generate nginx configuration for frontend"""
        return r"""server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy (if backend is separate)
    location /api {
        proxy_pass http://app:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""
    
    def generate_pytest_config(self, analysis: ProjectAnalysis) -> str:
        """Generate pytest.ini configuration"""
        return """[tool:pytest]
# Pytest configuration
minversion = 6.0
addopts = 
    -ra
    -q
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    auth: Authentication tests
    api: API endpoint tests
    db: Database tests

# Ignore patterns
norecursedirs = .git .tox dist build *.egg venv .venv

# Coverage settings
[coverage:run]
source = .
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*
    */.venv/*
    */migrations/*
    */config/*
    setup.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstract
"""
    
    def generate_test_fixtures(self, analysis: ProjectAnalysis) -> str:
        """Generate test fixtures for database and authentication"""
        if analysis.language == "python":
            return self._generate_python_fixtures(analysis)
        else:
            return self._generate_javascript_fixtures(analysis)
    
    def _generate_python_fixtures(self, analysis: ProjectAnalysis) -> str:
        """Generate Python test fixtures"""
        fixtures = '''"""
Test fixtures for pytest
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
'''
        
        # Add framework-specific imports
        if analysis.framework == "fastapi":
            fixtures += """
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import httpx

from main import app
from database import Base, get_db
"""
        elif analysis.framework == "django":
            fixtures += """
from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import setup_test_environment, teardown_test_environment

User = get_user_model()
"""
        
        # Database fixtures
        if analysis.has_database and analysis.database_type == "postgresql":
            fixtures += '''

# Database fixtures
@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Create database session for tests"""
    session = test_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
'''
        
        # Client fixtures
        if analysis.framework == "fastapi":
            fixtures += '''

@pytest.fixture
def client(db_session):
    """Create test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(db_session):
    """Create async test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()
'''
        
        # Authentication fixtures
        fixtures += '''

# Authentication fixtures
@pytest.fixture
def auth_headers():
    """Create authentication headers"""
    # Mock JWT token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True
    }
    # Add user to database (implementation depends on ORM)
    return user

@pytest.fixture
def admin_user(db_session):
    """Create admin user"""
    admin = {
        "id": 2,
        "email": "admin@example.com",
        "username": "admin",
        "is_active": True,
        "is_admin": True
    }
    # Add admin to database
    return admin
'''
        
        # Mock fixtures
        fixtures += '''

# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = Mock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    return redis_mock

@pytest.fixture
def mock_email_service():
    """Mock email service"""
    email_mock = Mock()
    email_mock.send = AsyncMock(return_value=True)
    return email_mock

@pytest.fixture
def mock_external_api():
    """Mock external API calls"""
    api_mock = Mock()
    api_mock.get = AsyncMock(return_value={"status": "success", "data": []})
    api_mock.post = AsyncMock(return_value={"status": "created", "id": 123})
    return api_mock
'''
        
        # Event loop fixture for async tests
        fixtures += '''

# Async support
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
'''
        
        return fixtures
    
    def _generate_javascript_fixtures(self, analysis: ProjectAnalysis) -> str:
        """Generate JavaScript test fixtures"""
        return """// Test fixtures for Jest/Mocha
const request = require('supertest');
const app = require('../app');

// Database fixtures
const setupDatabase = async () => {
    // Clear database
    await db.query('DELETE FROM users');
    // Add test data
    await db.query('INSERT INTO users (email, username) VALUES ($1, $2)', 
                   ['test@example.com', 'testuser']);
};

const teardownDatabase = async () => {
    // Clean up after tests
    await db.query('DELETE FROM users');
    await db.close();
};

// Test user fixtures
const testUser = {
    id: 1,
    email: 'test@example.com',
    username: 'testuser',
    password: 'testpass123'
};

const adminUser = {
    id: 2,
    email: 'admin@example.com',
    username: 'admin',
    password: 'adminpass123',
    role: 'admin'
};

// Auth token fixture
const generateToken = (user) => {
    return jwt.sign(
        { id: user.id, email: user.email },
        process.env.JWT_SECRET,
        { expiresIn: '1h' }
    );
};

// Mock fixtures
const mockRedis = {
    get: jest.fn().mockResolvedValue(null),
    set: jest.fn().mockResolvedValue('OK'),
    del: jest.fn().mockResolvedValue(1),
    exists: jest.fn().mockResolvedValue(0)
};

const mockEmailService = {
    send: jest.fn().mockResolvedValue(true)
};

module.exports = {
    setupDatabase,
    teardownDatabase,
    testUser,
    adminUser,
    generateToken,
    mockRedis,
    mockEmailService,
    app
};
"""
    
    def generate_api_tests(self, analysis: ProjectAnalysis) -> str:
        """Generate API endpoint tests"""
        if analysis.language == "python":
            return self._generate_python_api_tests(analysis)
        else:
            return self._generate_javascript_api_tests(analysis)
    
    def _generate_python_api_tests(self, analysis: ProjectAnalysis) -> str:
        """Generate Python API tests"""
        tests = '''"""
API Endpoint Tests
"""
import pytest
from httpx import AsyncClient
from fastapi import status

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
    
    def test_readiness_check(self, client, db_session):
        """Test readiness endpoint"""
        response = client.get("/ready")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert "database" in data
        assert "redis" in data

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123"
        }
        response = client.post("/api/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "password" not in data
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        login_data = {
            "email": test_user["email"],
            "password": "testpass123"
        }
        response = client.post("/api/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "wrong@example.com",
            "password": "wrongpass"
        }
        response = client.post("/api/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, auth_headers):
        """Test token refresh"""
        response = client.post("/api/refresh", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
    
    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post("/api/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

class TestUserEndpoints:
    """Test user management endpoints"""
    
    def test_get_current_user(self, client, auth_headers, test_user):
        """Test get current user"""
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user["email"]
    
    def test_update_user_profile(self, client, auth_headers):
        """Test update user profile"""
        update_data = {
            "username": "updateduser",
            "bio": "Updated bio"
        }
        response = client.put("/api/users/me", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == update_data["username"]
    
    def test_delete_user(self, client, auth_headers):
        """Test delete user account"""
        response = client.delete("/api/users/me", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoint"""
        response = client.get("/api/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
'''
        
        # Add CRUD tests for detected endpoints
        if analysis.api_endpoints:
            tests += '''

class TestCRUDEndpoints:
    """Test CRUD operations"""
    
    @pytest.mark.parametrize("endpoint", [
'''
            for endpoint in analysis.api_endpoints[:5]:
                tests += f'        "{endpoint}",\n'
            tests += '''    ])
    def test_list_endpoint(self, client, endpoint, auth_headers):
        """Test list endpoints"""
        response = client.get(endpoint, headers=auth_headers)
        assert response.status_code in [200, 404]  # 404 if resource doesn't exist yet
    
    def test_create_resource(self, client, auth_headers):
        """Test resource creation"""
        data = {"name": "Test Resource", "description": "Test"}
        response = client.post("/api/resources", json=data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        created = response.json()
        assert created["name"] == data["name"]
        assert "id" in created
    
    def test_update_resource(self, client, auth_headers):
        """Test resource update"""
        # First create a resource
        create_data = {"name": "Original"}
        create_response = client.post("/api/resources", json=create_data, headers=auth_headers)
        resource_id = create_response.json()["id"]
        
        # Update it
        update_data = {"name": "Updated"}
        response = client.put(f"/api/resources/{resource_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == update_data["name"]
    
    def test_delete_resource(self, client, auth_headers):
        """Test resource deletion"""
        # First create a resource
        create_data = {"name": "To Delete"}
        create_response = client.post("/api/resources", json=create_data, headers=auth_headers)
        resource_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/resources/{resource_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's gone
        get_response = client.get(f"/api/resources/{resource_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
'''
        
        # Add pagination and filtering tests
        tests += '''

class TestPaginationAndFiltering:
    """Test pagination and filtering"""
    
    def test_pagination(self, client, auth_headers):
        """Test paginated results"""
        response = client.get("/api/resources?page=1&limit=10", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) <= 10
    
    def test_filtering(self, client, auth_headers):
        """Test filtered results"""
        response = client.get("/api/resources?status=active", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All items should have active status
        for item in data.get("items", []):
            assert item.get("status") == "active"
    
    def test_sorting(self, client, auth_headers):
        """Test sorted results"""
        response = client.get("/api/resources?sort=created_at&order=desc", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        items = data.get("items", [])
        # Check if properly sorted
        for i in range(1, len(items)):
            assert items[i-1]["created_at"] >= items[i]["created_at"]

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client, auth_headers):
        """Test 404 error"""
        response = client.get("/api/nonexistent/999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()
    
    def test_400_bad_request(self, client, auth_headers):
        """Test 400 error for invalid data"""
        invalid_data = {"invalid_field": "value"}
        response = client.post("/api/resources", json=invalid_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_500_server_error(self, client, auth_headers, monkeypatch):
        """Test 500 error handling"""
        # Mock a function to raise an exception
        def mock_error(*args, **kwargs):
            raise Exception("Simulated server error")
        
        monkeypatch.setattr("app.some_function", mock_error)
        response = client.get("/api/trigger-error", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
'''
        
        return tests
    
    def _generate_javascript_api_tests(self, analysis: ProjectAnalysis) -> str:
        """Generate JavaScript API tests"""
        return """// API Endpoint Tests
const request = require('supertest');
const { app, setupDatabase, teardownDatabase, testUser, generateToken } = require('./fixtures');

describe('Health Endpoints', () => {
    test('GET /health should return healthy status', async () => {
        const response = await request(app).get('/health');
        expect(response.status).toBe(200);
        expect(response.body.status).toBe('healthy');
    });
});

describe('Authentication Endpoints', () => {
    beforeEach(setupDatabase);
    afterEach(teardownDatabase);
    
    test('POST /api/register should create new user', async () => {
        const userData = {
            email: 'newuser@example.com',
            username: 'newuser',
            password: 'securepass123'
        };
        
        const response = await request(app)
            .post('/api/register')
            .send(userData);
        
        expect(response.status).toBe(201);
        expect(response.body.email).toBe(userData.email);
        expect(response.body).not.toHaveProperty('password');
    });
    
    test('POST /api/login should return tokens', async () => {
        const response = await request(app)
            .post('/api/login')
            .send({
                email: testUser.email,
                password: testUser.password
            });
        
        expect(response.status).toBe(200);
        expect(response.body).toHaveProperty('accessToken');
        expect(response.body).toHaveProperty('refreshToken');
    });
    
    test('POST /api/login with invalid credentials should fail', async () => {
        const response = await request(app)
            .post('/api/login')
            .send({
                email: 'wrong@example.com',
                password: 'wrongpass'
            });
        
        expect(response.status).toBe(401);
    });
});

describe('Protected Endpoints', () => {
    let authToken;
    
    beforeAll(() => {
        authToken = generateToken(testUser);
    });
    
    beforeEach(setupDatabase);
    afterEach(teardownDatabase);
    
    test('GET /api/users/me should return current user', async () => {
        const response = await request(app)
            .get('/api/users/me')
            .set('Authorization', `Bearer ${authToken}`);
        
        expect(response.status).toBe(200);
        expect(response.body.email).toBe(testUser.email);
    });
    
    test('GET /api/users/me without token should fail', async () => {
        const response = await request(app).get('/api/users/me');
        expect(response.status).toBe(401);
    });
    
    test('PUT /api/users/me should update user profile', async () => {
        const updateData = {
            username: 'updateduser',
            bio: 'Updated bio'
        };
        
        const response = await request(app)
            .put('/api/users/me')
            .set('Authorization', `Bearer ${authToken}`)
            .send(updateData);
        
        expect(response.status).toBe(200);
        expect(response.body.username).toBe(updateData.username);
    });
});

describe('CRUD Operations', () => {
    let authToken;
    
    beforeAll(() => {
        authToken = generateToken(testUser);
    });
    
    test('POST /api/resources should create resource', async () => {
        const resourceData = {
            name: 'Test Resource',
            description: 'Test description'
        };
        
        const response = await request(app)
            .post('/api/resources')
            .set('Authorization', `Bearer ${authToken}`)
            .send(resourceData);
        
        expect(response.status).toBe(201);
        expect(response.body.name).toBe(resourceData.name);
        expect(response.body).toHaveProperty('id');
    });
    
    test('GET /api/resources should list resources', async () => {
        const response = await request(app)
            .get('/api/resources')
            .set('Authorization', `Bearer ${authToken}`);
        
        expect(response.status).toBe(200);
        expect(Array.isArray(response.body.items)).toBe(true);
    });
    
    test('PUT /api/resources/:id should update resource', async () => {
        // First create a resource
        const createResponse = await request(app)
            .post('/api/resources')
            .set('Authorization', `Bearer ${authToken}`)
            .send({ name: 'Original' });
        
        const resourceId = createResponse.body.id;
        
        // Update it
        const updateResponse = await request(app)
            .put(`/api/resources/${resourceId}`)
            .set('Authorization', `Bearer ${authToken}`)
            .send({ name: 'Updated' });
        
        expect(updateResponse.status).toBe(200);
        expect(updateResponse.body.name).toBe('Updated');
    });
    
    test('DELETE /api/resources/:id should delete resource', async () => {
        // First create a resource
        const createResponse = await request(app)
            .post('/api/resources')
            .set('Authorization', `Bearer ${authToken}`)
            .send({ name: 'To Delete' });
        
        const resourceId = createResponse.body.id;
        
        // Delete it
        const deleteResponse = await request(app)
            .delete(`/api/resources/${resourceId}`)
            .set('Authorization', `Bearer ${authToken}`);
        
        expect(deleteResponse.status).toBe(204);
        
        // Verify it's gone
        const getResponse = await request(app)
            .get(`/api/resources/${resourceId}`)
            .set('Authorization', `Bearer ${authToken}`);
        
        expect(getResponse.status).toBe(404);
    });
});

describe('Error Handling', () => {
    test('404 for non-existent endpoint', async () => {
        const response = await request(app).get('/api/nonexistent');
        expect(response.status).toBe(404);
    });
    
    test('422 for invalid data', async () => {
        const response = await request(app)
            .post('/api/resources')
            .send({ invalid_field: 'value' });
        
        expect(response.status).toBe(422);
    });
});
"""
    
    def generate_auth_tests(self, analysis: ProjectAnalysis) -> str:
        """Generate authentication tests"""
        if analysis.language == "python":
            return self._generate_python_auth_tests()
        else:
            return self._generate_javascript_auth_tests()
    
    def _generate_python_auth_tests(self) -> str:
        """Generate Python authentication tests"""
        return '''"""
Authentication and Authorization Tests
"""
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi import status

class TestJWTAuthentication:
    """Test JWT token handling"""
    
    def test_generate_access_token(self):
        """Test access token generation"""
        from auth import create_access_token
        
        user_data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data=user_data)
        
        # Decode token
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["sub"] == user_data["sub"]
        assert decoded["email"] == user_data["email"]
        assert "exp" in decoded
    
    def test_token_expiration(self):
        """Test token expiration"""
        from auth import create_access_token
        
        # Create token with short expiration
        token = create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Try to use expired token
        # This should fail in actual API call
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, "secret", algorithms=["HS256"])
    
    def test_refresh_token_flow(self, client, test_user):
        """Test complete refresh token flow"""
        # Login to get tokens
        login_response = client.post("/api/login", json={
            "email": test_user["email"],
            "password": "testpass123"
        })
        assert login_response.status_code == status.HTTP_200_OK
        
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_response = client.post("/api/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == status.HTTP_200_OK
        
        new_access_token = refresh_response.json()["access_token"]
        assert new_access_token != access_token  # Should be different

class TestAuthorization:
    """Test authorization and permissions"""
    
    def test_role_based_access(self, client, admin_user, test_user):
        """Test role-based access control"""
        # Get tokens for both users
        admin_token = self._get_token(client, admin_user)
        user_token = self._get_token(client, test_user)
        
        # Admin endpoint - should work for admin
        admin_response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_response.status_code == status.HTTP_200_OK
        
        # Admin endpoint - should fail for regular user
        user_response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert user_response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_resource_ownership(self, client, auth_headers):
        """Test resource ownership validation"""
        # Create a resource
        create_response = client.post(
            "/api/resources",
            json={"name": "My Resource"},
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        # Owner should be able to update
        update_response = client.put(
            f"/api/resources/{resource_id}",
            json={"name": "Updated"},
            headers=auth_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        
        # Different user shouldn't be able to update
        # (would need different user's token to test properly)
    
    def test_api_key_authentication(self, client):
        """Test API key authentication"""
        api_key = "test-api-key-123"
        
        response = client.get(
            "/api/public/data",
            headers={"X-API-Key": api_key}
        )
        
        # Should work with valid API key
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        # Should fail without API key
        no_key_response = client.get("/api/public/data")
        assert no_key_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def _get_token(self, client, user):
        """Helper to get token for user"""
        response = client.post("/api/login", json={
            "email": user["email"],
            "password": user.get("password", "testpass123")
        })
        return response.json()["access_token"]

class TestPasswordSecurity:
    """Test password security features"""
    
    def test_password_hashing(self):
        """Test password is properly hashed"""
        from auth import hash_password, verify_password
        
        password = "mysecretpassword"
        hashed = hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Should be able to verify
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_requirements(self, client):
        """Test password strength requirements"""
        weak_passwords = [
            "123",  # Too short
            "password",  # No numbers
            "12345678",  # No letters
            "pass word"  # Contains space
        ]
        
        for weak_pass in weak_passwords:
            response = client.post("/api/register", json={
                "email": "test@example.com",
                "username": "testuser",
                "password": weak_pass
            })
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "password" in response.json()["detail"].lower()
    
    def test_password_reset_flow(self, client, test_user):
        """Test password reset flow"""
        # Request password reset
        reset_request = client.post("/api/password-reset", json={
            "email": test_user["email"]
        })
        assert reset_request.status_code == status.HTTP_200_OK
        
        # In real app, would send email with reset token
        # For testing, we'll mock the token
        reset_token = "mock-reset-token-123"
        
        # Reset password with token
        new_password = "newsecurepass456"
        reset_response = client.post("/api/password-reset/confirm", json={
            "token": reset_token,
            "new_password": new_password
        })
        assert reset_response.status_code == status.HTTP_200_OK
        
        # Should be able to login with new password
        login_response = client.post("/api/login", json={
            "email": test_user["email"],
            "password": new_password
        })
        assert login_response.status_code == status.HTTP_200_OK

class TestOAuth:
    """Test OAuth integration"""
    
    @pytest.mark.skip(reason="Requires OAuth provider setup")
    def test_google_oauth_flow(self, client):
        """Test Google OAuth flow"""
        # Get OAuth URL
        oauth_response = client.get("/api/auth/google")
        assert oauth_response.status_code == status.HTTP_200_OK
        assert "url" in oauth_response.json()
        
        # In real test, would need to mock OAuth callback
        # This is just a placeholder
    
    @pytest.mark.skip(reason="Requires OAuth provider setup")
    def test_github_oauth_flow(self, client):
        """Test GitHub OAuth flow"""
        # Similar to Google OAuth test
        pass
'''
    
    def _generate_javascript_auth_tests(self) -> str:
        """Generate JavaScript authentication tests"""
        return """// Authentication Tests
const request = require('supertest');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const { app, testUser, adminUser } = require('./fixtures');

describe('JWT Authentication', () => {
    test('should generate valid access token', () => {
        const payload = { id: 1, email: 'test@example.com' };
        const token = jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '1h' });
        
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        expect(decoded.id).toBe(payload.id);
        expect(decoded.email).toBe(payload.email);
    });
    
    test('should reject expired token', () => {
        const token = jwt.sign(
            { id: 1 },
            process.env.JWT_SECRET,
            { expiresIn: '-1s' }  // Already expired
        );
        
        expect(() => {
            jwt.verify(token, process.env.JWT_SECRET);
        }).toThrow('jwt expired');
    });
});

describe('Password Security', () => {
    test('should hash passwords correctly', async () => {
        const password = 'mysecretpassword';
        const hash = await bcrypt.hash(password, 10);
        
        expect(hash).not.toBe(password);
        
        const isValid = await bcrypt.compare(password, hash);
        expect(isValid).toBe(true);
        
        const isInvalid = await bcrypt.compare('wrongpassword', hash);
        expect(isInvalid).toBe(false);
    });
    
    test('should enforce password requirements', async () => {
        const weakPasswords = [
            '123',  // Too short
            'password',  // No numbers
            '12345678'  // No letters
        ];
        
        for (const password of weakPasswords) {
            const response = await request(app)
                .post('/api/register')
                .send({
                    email: 'test@example.com',
                    username: 'testuser',
                    password
                });
            
            expect(response.status).toBe(422);
        }
    });
});

describe('Authorization', () => {
    test('should enforce role-based access', async () => {
        const adminToken = jwt.sign(adminUser, process.env.JWT_SECRET);
        const userToken = jwt.sign(testUser, process.env.JWT_SECRET);
        
        // Admin endpoint - should work for admin
        const adminResponse = await request(app)
            .get('/api/admin/users')
            .set('Authorization', `Bearer ${adminToken}`);
        expect(adminResponse.status).toBe(200);
        
        // Admin endpoint - should fail for regular user
        const userResponse = await request(app)
            .get('/api/admin/users')
            .set('Authorization', `Bearer ${userToken}`);
        expect(userResponse.status).toBe(403);
    });
});
"""
    
    def generate_makefile(self, analysis: ProjectAnalysis) -> str:
        """Generate Makefile for common operations"""
        return """# Makefile for DevOps operations

.PHONY: help build test deploy clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

# Docker operations
build: ## Build Docker images
	docker-compose build

up: ## Start services
	docker-compose up -d

down: ## Stop services
	docker-compose down

restart: ## Restart services
	docker-compose restart

logs: ## View logs
	docker-compose logs -f

shell: ## Open shell in app container
	docker-compose exec app /bin/bash

# Testing
test: ## Run tests
	docker-compose run --rm app pytest

test-coverage: ## Run tests with coverage
	docker-compose run --rm app pytest --cov=app --cov-report=html

test-unit: ## Run unit tests only
	docker-compose run --rm app pytest -m unit

test-integration: ## Run integration tests only
	docker-compose run --rm app pytest -m integration

lint: ## Run linting
	docker-compose run --rm app flake8 .
	docker-compose run --rm app black --check .
	docker-compose run --rm app mypy .

format: ## Format code
	docker-compose run --rm app black .
	docker-compose run --rm app isort .

# Database operations
db-migrate: ## Run database migrations
	docker-compose run --rm app alembic upgrade head

db-rollback: ## Rollback last migration
	docker-compose run --rm app alembic downgrade -1

db-reset: ## Reset database
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	docker-compose run --rm app alembic upgrade head

# Deployment
deploy-staging: ## Deploy to staging
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production
	./scripts/deploy.sh production

# Cleanup
clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

clean-all: ## Clean everything including images
	docker-compose down -v --rmi all
	docker system prune -af
"""
    
    def save_files(self, project_path: Path, files: Dict[str, str]):
        """Save generated files to disk"""
        for file_path, content in files.items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            console.print(f"[green]✓[/green] Created: {file_path}")
    
    def run(self, project_path: str, generate: str = "all", verbose: bool = False):
        """Main execution function"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            console.print(f"[red]Error:[/red] Project path {project_path} does not exist")
            return False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Analyze project
            task = progress.add_task("Analyzing project...", total=None)
            analysis = self.analyze_project(project_path)
            progress.update(task, completed=True)
            
            # Display analysis
            if verbose:
                console.print(Panel(
                    f"[bold]Project Analysis[/bold]\n"
                    f"Language: {analysis.language}\n"
                    f"Framework: {analysis.framework}\n"
                    f"Services: {', '.join(analysis.services)}\n"
                    f"Database: {analysis.database_type or 'None'}\n"
                    f"Redis: {'Yes' if analysis.has_redis else 'No'}\n"
                    f"Frontend: {analysis.frontend_framework or 'None'}",
                    border_style="cyan"
                ))
            
            files = {}
            
            # Generate Docker configuration
            if generate in ["docker", "all"]:
                task = progress.add_task("Generating Docker configuration...", total=None)
                
                # Generate Dockerfile
                files["Dockerfile"] = self.generate_dockerfile(analysis)
                
                # Generate docker-compose.yml
                files["docker-compose.yml"] = self.generate_docker_compose(analysis)
                
                # Generate .env.example
                files[".env.example"] = self.generate_env_template(analysis)
                
                # Generate nginx config if frontend exists
                if analysis.has_frontend:
                    files["nginx.conf"] = self.generate_nginx_config(analysis)
                
                # Generate Makefile
                files["Makefile"] = self.generate_makefile(analysis)
                
                progress.update(task, completed=True)
            
            # Generate testing infrastructure
            if generate in ["testing", "all"]:
                task = progress.add_task("Generating testing infrastructure...", total=None)
                
                # Generate pytest configuration
                if analysis.language == "python":
                    files["pytest.ini"] = self.generate_pytest_config(analysis)
                    files["tests/conftest.py"] = self.generate_test_fixtures(analysis)
                    files["tests/test_api.py"] = self.generate_api_tests(analysis)
                    files["tests/test_auth.py"] = self.generate_auth_tests(analysis)
                else:
                    files["tests/fixtures.js"] = self.generate_test_fixtures(analysis)
                    files["tests/api.test.js"] = self.generate_api_tests(analysis)
                    files["tests/auth.test.js"] = self.generate_auth_tests(analysis)
                
                progress.update(task, completed=True)
            
            # Save all files
            if files:
                task = progress.add_task("Saving files...", total=len(files))
                for i, (file_path, content) in enumerate(files.items()):
                    full_path = project_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content)
                    progress.update(task, advance=1)
                
        # Display summary
        console.print(Panel(
            f"[bold green]✅ DevOps Configuration Complete[/bold green]\n\n"
            f"Generated {len(files)} files:\n" +
            "\n".join([f"  • {f}" for f in sorted(files.keys())]) +
            "\n\n[bold]Next Steps:[/bold]\n"
            f"1. Review and customize the generated files\n"
            f"2. Copy .env.example to .env and set values\n"
            f"3. Run 'docker-compose up' to start services\n"
            f"4. Run 'make test' to execute tests",
            border_style="green"
        ))
        
        return True

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Enhanced DevOps Engineer - Section 6 Implementation")
    parser.add_argument("--project-path", "-p", default=".", help="Path to project (default: current directory)")
    parser.add_argument("--generate", "-g", choices=["docker", "testing", "all"], default="all",
                       help="What to generate (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    
    args = parser.parse_args()
    
    # Create agent
    agent = EnhancedDevOpsEngineer(api_key=args.api_key)
    
    # Run generation
    success = agent.run(
        project_path=args.project_path,
        generate=args.generate,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()