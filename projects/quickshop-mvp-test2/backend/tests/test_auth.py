"""
Authentication system tests for QuickShop MVP
Tests user registration, login, JWT token validation, and security measures
"""
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from app.core.config import settings

class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_register_new_user_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_email_fails(self, client):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User"
        }
        
        # First registration should succeed
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Second registration with same email should fail
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email_fails(self, client):
        """Test registration with invalid email format fails"""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password_fails(self, client):
        """Test registration with weak password fails"""
        user_data = {
            "email": "test@example.com",
            "password": "123",  # Too weak
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

class TestUserLogin:
    """Test user login functionality"""
    
    def test_login_valid_credentials_success(self, client):
        """Test successful login with valid credentials"""
        # Register user first
        user_data = {
            "email": "login@example.com",
            "password": "loginpassword123",
            "full_name": "Login User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Test login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Validate JWT token
        token = data["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_data["email"]
    
    def test_login_invalid_credentials_fails(self, client):
        """Test login with invalid credentials fails"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_missing_fields_fails(self, client):
        """Test login with missing fields fails"""
        response = client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422

class TestTokenValidation:
    """Test JWT token validation and protected endpoints"""
    
    def test_access_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data
    
    def test_access_protected_endpoint_without_token_fails(self, client):
        """Test accessing protected endpoint without token fails"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_invalid_token_fails(self, client):
        """Test accessing protected endpoint with invalid token fails"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
    
    def test_refresh_token_functionality(self, client):
        """Test refresh token functionality"""
        # Register and login user
        user_data = {
            "email": "refresh@example.com",
            "password": "refreshpassword123",
            "full_name": "Refresh User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

class TestSecurityMeasures:
    """Test security measures and edge cases"""
    
    def test_password_hashing(self, client, db_session):
        """Test that passwords are properly hashed"""
        user_data = {
            "email": "hash@example.com",
            "password": "plaintextpassword",
            "full_name": "Hash User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Check that password is not stored in plain text
        from app.models.user import User
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user.hashed_password != user_data["password"]
        assert len(user.hashed_password) > 50  # Hashed password should be long
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection in login"""
        malicious_data = {
            "username": "admin@example.com' OR '1'='1",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", data=malicious_data)
        # Should not succeed with SQL injection
        assert response.status_code == 401
    
    def test_rate_limiting_simulation(self, client):
        """Test rate limiting behavior (simulated)"""
        user_data = {
            "email": "ratelimit@example.com",
            "password": "password123",
            "full_name": "Rate Limit User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Attempt multiple failed logins
        login_data = {
            "username": user_data["email"],
            "password": "wrongpassword"
        }
        
        for _ in range(5):
            response = client.post("/api/v1/auth/login", data=login_data)
            assert response.status_code == 401
        
        # Note: Actual rate limiting would be implemented in middleware
        # This test validates the endpoint handles multiple requests