#!/usr/bin/env python3
"""
Test Suite for Enhanced DevOps Engineer (Section 6 Implementation)
Tests Docker configuration and testing infrastructure generation
"""

import pytest
import os
import sys
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sfa.sfa_devops_engineer_enhanced import (
    EnhancedDevOpsEngineer,
    ProjectAnalysis
)

class TestProjectAnalysis:
    """Test project analysis functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_analyze_python_fastapi_project(self, temp_project):
        """Test analysis of Python FastAPI project"""
        # Create Python project structure
        (temp_project / "requirements.txt").write_text("""
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pytest==7.4.3
""")
        
        (temp_project / "main.py").write_text("""
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}
    
@app.post("/api/users")
def create_user(user: dict):
    return user
""")
        
        agent = EnhancedDevOpsEngineer()
        analysis = agent.analyze_project(temp_project)
        
        assert analysis.language == "python"
        assert analysis.framework == "fastapi"
        assert analysis.has_database is True
        assert analysis.database_type == "postgresql"
        assert analysis.has_redis is True
        assert "/health" in analysis.api_endpoints
        assert "/api/users" in analysis.api_endpoints
    
    def test_analyze_node_express_project(self, temp_project):
        """Test analysis of Node.js Express project"""
        # Create Node.js project structure
        package_json = {
            "name": "test-app",
            "dependencies": {
                "express": "^4.18.2",
                "mongoose": "^7.0.0",
                "redis": "^4.6.0",
                "jsonwebtoken": "^9.0.0"
            }
        }
        (temp_project / "package.json").write_text(json.dumps(package_json))
        
        (temp_project / "app.js").write_text("""
const express = require('express');
const app = express();

app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.post('/api/login', (req, res) => {
    res.json({ token: 'test' });
});
""")
        
        agent = EnhancedDevOpsEngineer()
        analysis = agent.analyze_project(temp_project)
        
        assert analysis.language == "javascript"
        assert analysis.framework == "express"
        assert analysis.has_database is True
        assert analysis.database_type == "mongodb"
        assert analysis.has_redis is True
    
    def test_analyze_project_with_frontend(self, temp_project):
        """Test analysis of project with frontend"""
        # Create backend
        (temp_project / "requirements.txt").write_text("fastapi==0.104.1")
        
        # Create frontend
        frontend_dir = temp_project / "frontend"
        frontend_dir.mkdir()
        
        package_json = {
            "name": "frontend",
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            }
        }
        (frontend_dir / "package.json").write_text(json.dumps(package_json))
        
        agent = EnhancedDevOpsEngineer()
        analysis = agent.analyze_project(temp_project)
        
        assert analysis.has_frontend is True
        assert analysis.frontend_framework == "react"
        assert "frontend-app" not in analysis.services  # react-app should be in services
    
    def test_detect_environment_variables(self, temp_project):
        """Test environment variable detection"""
        # Create .env.example
        (temp_project / ".env.example").write_text("""
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=changeme
API_KEY=
""")
        
        # Create Python file with env usage
        (temp_project / "config.py").write_text("""
import os
db_url = os.getenv("DATABASE_URL")
api_key = os.environ["API_KEY"]
secret = os.getenv("SECRET_KEY", "default")
""")
        
        agent = EnhancedDevOpsEngineer()
        analysis = agent.analyze_project(temp_project)
        
        assert "DATABASE_URL" in analysis.environment_vars
        assert "REDIS_URL" in analysis.environment_vars
        assert "SECRET_KEY" in analysis.environment_vars
        assert "API_KEY" in analysis.environment_vars

class TestDockerGeneration:
    """Test Docker configuration generation"""
    
    def test_generate_fastapi_dockerfile(self):
        """Test FastAPI Dockerfile generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=True,
            has_frontend=False,
            frontend_framework=None,
            services=["fastapi-api", "postgresql", "redis"],
            dependencies={"python": ["fastapi", "uvicorn", "sqlalchemy"]},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        dockerfile = agent.generate_dockerfile(analysis)
        
        assert "FROM python:3.11-slim" in dockerfile
        assert "uvicorn" in dockerfile
        assert "HEALTHCHECK" in dockerfile
        assert "USER appuser" in dockerfile
        assert "EXPOSE 8000" in dockerfile
    
    def test_generate_node_dockerfile(self):
        """Test Node.js Dockerfile generation"""
        analysis = ProjectAnalysis(
            language="javascript",
            framework="express",
            has_database=False,
            database_type=None,
            has_redis=False,
            has_frontend=False,
            frontend_framework=None,
            services=["express-api"],
            dependencies={"javascript": ["express"]},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        dockerfile = agent.generate_dockerfile(analysis)
        
        assert "FROM node:18-alpine" in dockerfile
        assert "npm ci" in dockerfile
        assert "USER nodejs" in dockerfile
        assert "EXPOSE 3000" in dockerfile
        assert "HEALTHCHECK" in dockerfile
    
    def test_generate_docker_compose_with_all_services(self):
        """Test docker-compose.yml generation with all services"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=True,
            has_frontend=True,
            frontend_framework="react",
            services=["fastapi-api", "postgresql", "redis", "react-app"],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        compose_yaml = agent.generate_docker_compose(analysis)
        compose = yaml.safe_load(compose_yaml)
        
        assert "version" in compose
        assert compose["version"] == "3.8"
        assert "services" in compose
        
        # Check services
        assert "app" in compose["services"]
        assert "postgres" in compose["services"]
        assert "redis" in compose["services"]
        assert "frontend" in compose["services"]
        
        # Check app service configuration
        app_service = compose["services"]["app"]
        assert "build" in app_service
        assert "depends_on" in app_service
        assert "postgres" in app_service["depends_on"]
        assert "redis" in app_service["depends_on"]
        assert "DATABASE_URL" in app_service["environment"]
        assert "REDIS_URL" in app_service["environment"]
        
        # Check postgres service
        postgres = compose["services"]["postgres"]
        assert postgres["image"] == "postgres:15-alpine"
        assert "healthcheck" in postgres
        
        # Check volumes
        assert "volumes" in compose
        assert "postgres_data" in compose["volumes"]
        assert "redis_data" in compose["volumes"]
        
        # Check networks
        assert "networks" in compose
        assert "app-network" in compose["networks"]
    
    def test_generate_env_template(self):
        """Test .env.example generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=True,
            has_frontend=True,
            frontend_framework="react",
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=["JWT_SECRET", "SMTP_HOST", "AWS_ACCESS_KEY"]
        )
        
        agent = EnhancedDevOpsEngineer()
        env_template = agent.generate_env_template(analysis)
        
        assert "# Application Settings" in env_template
        assert "ENVIRONMENT=production" in env_template
        assert "SECRET_KEY=" in env_template
        
        assert "# Database Settings" in env_template
        assert "POSTGRES_DB=" in env_template
        assert "DATABASE_URL=" in env_template
        
        assert "# Redis Settings" in env_template
        assert "REDIS_URL=" in env_template
        
        assert "# API Settings" in env_template
        assert "CORS_ORIGINS=" in env_template
        
        assert "# Detected Environment Variables" in env_template
        assert "JWT_SECRET=" in env_template
        assert "SMTP_HOST=" in env_template
        assert "AWS_ACCESS_KEY=" in env_template
    
    def test_generate_nginx_config(self):
        """Test nginx configuration generation"""
        analysis = ProjectAnalysis(
            language="javascript",
            framework="express",
            has_database=False,
            database_type=None,
            has_redis=False,
            has_frontend=True,
            frontend_framework="react",
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        nginx_config = agent.generate_nginx_config(analysis)
        
        assert "server {" in nginx_config
        assert "listen 80;" in nginx_config
        assert "gzip on;" in nginx_config
        assert "location /api" in nginx_config
        assert "proxy_pass http://app:8000;" in nginx_config
        assert "try_files $uri $uri/ /index.html;" in nginx_config

class TestTestingInfrastructure:
    """Test testing infrastructure generation"""
    
    def test_generate_pytest_config(self):
        """Test pytest.ini generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=False,
            has_frontend=False,
            frontend_framework=None,
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        pytest_config = agent.generate_pytest_config(analysis)
        
        assert "[tool:pytest]" in pytest_config
        assert "--cov=app" in pytest_config
        assert "--cov-fail-under=80" in pytest_config
        assert "markers =" in pytest_config
        assert "unit: Unit tests" in pytest_config
        assert "integration: Integration tests" in pytest_config
        assert "auth: Authentication tests" in pytest_config
    
    def test_generate_python_fixtures(self):
        """Test Python test fixtures generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=True,
            has_frontend=False,
            frontend_framework=None,
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        fixtures = agent.generate_test_fixtures(analysis)
        
        assert "import pytest" in fixtures
        assert "from fastapi.testclient import TestClient" in fixtures
        assert "@pytest.fixture" in fixtures
        assert "def test_db():" in fixtures
        assert "def db_session(test_db):" in fixtures
        assert "def client(db_session):" in fixtures
        assert "def auth_headers():" in fixtures
        assert "def mock_redis():" in fixtures
    
    def test_generate_api_tests(self):
        """Test API endpoint tests generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=False,
            has_frontend=False,
            frontend_framework=None,
            services=[],
            dependencies={},
            api_endpoints=["/api/users", "/api/login", "/api/products"],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        api_tests = agent.generate_api_tests(analysis)
        
        assert "class TestHealthEndpoints:" in api_tests
        assert "def test_health_check(self, client):" in api_tests
        
        assert "class TestAuthEndpoints:" in api_tests
        assert "def test_register_user(self, client):" in api_tests
        assert "def test_login_success(self, client, test_user):" in api_tests
        
        assert "class TestCRUDEndpoints:" in api_tests
        assert "@pytest.mark.parametrize" in api_tests
        assert '"/api/users"' in api_tests
        assert '"/api/login"' in api_tests
        assert '"/api/products"' in api_tests
        
        assert "class TestPaginationAndFiltering:" in api_tests
        assert "def test_pagination(self, client, auth_headers):" in api_tests
        
        assert "class TestErrorHandling:" in api_tests
        assert "def test_404_not_found(self, client, auth_headers):" in api_tests
    
    def test_generate_auth_tests(self):
        """Test authentication tests generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=False,
            has_frontend=False,
            frontend_framework=None,
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        auth_tests = agent.generate_auth_tests(analysis)
        
        assert "class TestJWTAuthentication:" in auth_tests
        assert "def test_generate_access_token(self):" in auth_tests
        assert "def test_token_expiration(self):" in auth_tests
        assert "def test_refresh_token_flow(self, client, test_user):" in auth_tests
        
        assert "class TestAuthorization:" in auth_tests
        assert "def test_role_based_access(self, client, admin_user, test_user):" in auth_tests
        
        assert "class TestPasswordSecurity:" in auth_tests
        assert "def test_password_hashing(self):" in auth_tests
        assert "def test_password_requirements(self, client):" in auth_tests
    
    def test_generate_makefile(self):
        """Test Makefile generation"""
        analysis = ProjectAnalysis(
            language="python",
            framework="fastapi",
            has_database=True,
            database_type="postgresql",
            has_redis=True,
            has_frontend=False,
            frontend_framework=None,
            services=[],
            dependencies={},
            api_endpoints=[],
            environment_vars=[]
        )
        
        agent = EnhancedDevOpsEngineer()
        makefile = agent.generate_makefile(analysis)
        
        assert ".PHONY: help build test deploy clean" in makefile
        assert "build: ## Build Docker images" in makefile
        assert "docker-compose build" in makefile
        assert "test: ## Run tests" in makefile
        assert "docker-compose run --rm app pytest" in makefile
        assert "db-migrate: ## Run database migrations" in makefile
        assert "deploy-production: ## Deploy to production" in makefile

class TestEndToEndGeneration:
    """Test end-to-end file generation"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        
        # Create a simple FastAPI project
        project_path = Path(temp_dir)
        (project_path / "requirements.txt").write_text("""
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pytest==7.4.3
""")
        
        (project_path / "main.py").write_text("""
from fastapi import FastAPI
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/users")
def create_user(user: dict):
    return user
    
@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}
""")
        
        # Create frontend
        frontend_dir = project_path / "frontend"
        frontend_dir.mkdir()
        package_json = {
            "name": "frontend",
            "dependencies": {
                "react": "^18.2.0"
            }
        }
        (frontend_dir / "package.json").write_text(json.dumps(package_json))
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    def test_run_docker_generation(self, temp_project):
        """Test Docker configuration generation"""
        agent = EnhancedDevOpsEngineer()
        success = agent.run(
            project_path=str(temp_project),
            generate="docker",
            verbose=False
        )
        
        assert success is True
        
        # Check Docker files were created
        assert (temp_project / "Dockerfile").exists()
        assert (temp_project / "docker-compose.yml").exists()
        assert (temp_project / ".env.example").exists()
        assert (temp_project / "nginx.conf").exists()
        assert (temp_project / "Makefile").exists()
        
        # Verify docker-compose.yml content
        compose_content = (temp_project / "docker-compose.yml").read_text()
        compose = yaml.safe_load(compose_content)
        assert "services" in compose
        assert "app" in compose["services"]
        assert "postgres" in compose["services"]
        assert "redis" in compose["services"]
        assert "frontend" in compose["services"]
    
    def test_run_testing_generation(self, temp_project):
        """Test testing infrastructure generation"""
        agent = EnhancedDevOpsEngineer()
        success = agent.run(
            project_path=str(temp_project),
            generate="testing",
            verbose=False
        )
        
        assert success is True
        
        # Check test files were created
        assert (temp_project / "pytest.ini").exists()
        assert (temp_project / "tests" / "conftest.py").exists()
        assert (temp_project / "tests" / "test_api.py").exists()
        assert (temp_project / "tests" / "test_auth.py").exists()
        
        # Verify test content
        conftest = (temp_project / "tests" / "conftest.py").read_text()
        assert "@pytest.fixture" in conftest
        assert "def client(" in conftest
        assert "def test_user(" in conftest
        
        api_tests = (temp_project / "tests" / "test_api.py").read_text()
        assert "class TestHealthEndpoints:" in api_tests
        assert "def test_health_check(" in api_tests
    
    def test_run_all_generation(self, temp_project):
        """Test complete generation (docker + testing)"""
        agent = EnhancedDevOpsEngineer()
        success = agent.run(
            project_path=str(temp_project),
            generate="all",
            verbose=True
        )
        
        assert success is True
        
        # Check all files were created
        expected_files = [
            "Dockerfile",
            "docker-compose.yml",
            ".env.example",
            "nginx.conf",
            "Makefile",
            "pytest.ini",
            "tests/conftest.py",
            "tests/test_api.py",
            "tests/test_auth.py"
        ]
        
        for file_path in expected_files:
            assert (temp_project / file_path).exists(), f"Missing file: {file_path}"

class TestCLIIntegration:
    """Test CLI integration"""
    
    @patch('sys.argv', ['sfa_devops_engineer_enhanced.py', '--help'])
    def test_cli_help(self):
        """Test CLI help"""
        from sfa.sfa_devops_engineer_enhanced import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Help should exit with 0
        assert exc_info.value.code in [0, None]
    
    @patch('sys.argv', ['sfa_devops_engineer_enhanced.py', '--project-path', '.', '--generate', 'docker'])
    @patch('sfa.sfa_devops_engineer_enhanced.EnhancedDevOpsEngineer.run')
    def test_cli_docker_generation(self, mock_run):
        """Test CLI Docker generation"""
        mock_run.return_value = True
        
        from sfa.sfa_devops_engineer_enhanced import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        mock_run.assert_called_once_with(
            project_path='.',
            generate='docker',
            verbose=False
        )
    
    @patch('sys.argv', ['sfa_devops_engineer_enhanced.py', '-p', '/project', '-g', 'all', '-v'])
    @patch('sfa.sfa_devops_engineer_enhanced.EnhancedDevOpsEngineer.run')
    def test_cli_all_generation_verbose(self, mock_run):
        """Test CLI all generation with verbose"""
        mock_run.return_value = True
        
        from sfa.sfa_devops_engineer_enhanced import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        mock_run.assert_called_once_with(
            project_path='/project',
            generate='all',
            verbose=True
        )

class TestErrorHandling:
    """Test error handling"""
    
    def test_nonexistent_project_path(self):
        """Test handling of non-existent project path"""
        agent = EnhancedDevOpsEngineer()
        success = agent.run(
            project_path="/nonexistent/path",
            generate="all",
            verbose=False
        )
        
        assert success is False
    
    def test_empty_project_analysis(self):
        """Test analysis of empty project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            agent = EnhancedDevOpsEngineer()
            analysis = agent.analyze_project(Path(temp_dir))
            
            # Should still return valid analysis with defaults
            assert analysis.language in ["python", "javascript"]
            assert analysis.framework in ["fastapi", "express", "django", "flask", "fastify", "nestjs"]
            assert isinstance(analysis.services, list)
            assert isinstance(analysis.dependencies, dict)
            assert isinstance(analysis.api_endpoints, list)
            assert isinstance(analysis.environment_vars, list)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])