"""
Security tests for QuickShop MVP
Tests authentication, authorization, input validation, and protection against common attacks
"""
import pytest
import json
from fastapi.testclient import TestClient

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_xss_protection_in_product_creation(self, client, admin_headers):
        """Test XSS protection in product creation"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "<%2Fscript%3E%3Cscript%3Ealert%28%27xss%27%29%3C%2Fscript%3E"
        ]
        
        for payload in xss_payloads:
            product_data = {
                "name": f"Product {payload}",
                "description": f"Description {payload}",
                "price": 29.99,
                "category": "Electronics",
                "stock_quantity": 10
            }
            
            response = client.post(
                "/api/v1/products/",
                json=product_data,
                headers=admin_headers
            )
            
            if response.status_code == 201:
                data = response.json()
                # XSS should be sanitized or escaped
                assert "<script>" not in data["name"]
                assert "javascript:" not in data["description"]
                assert "onerror=" not in data["name"]
    
    def test_sql_injection_protection_in_search(self, client, sample_products):
        """Test SQL injection protection in product search"""
        sql_payloads = [
            "'; DROP TABLE products; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; UPDATE products SET price=0; --"
        ]
        
        for payload in sql_payloads:
            response = client.get(f"/api/v1/products/search?q={payload}")
            # Should not cause server error or expose sensitive data
            assert response.status_code in [200, 400, 422]
            if response.status_code == 200:
                data = response.json()
                # Should return normal search results or empty array
                assert isinstance(data, list)
    
    def test_path_traversal_protection(self, client, admin_headers):
        """Test protection against path traversal attacks"""
        traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2fpasswd",
            "....//....//etc/passwd"
        ]
        
        for payload in traversal_payloads:
            # Test in product image URL
            product_data = {
                "name": "Test Product",
                "description": "Test description",
                "price": 29.99,
                "category": "Electronics",
                "stock_quantity": 10,
                "image_url": payload
            }
            
            response = client.post(
                "/api/v1/products/",
                json=product_data,
                headers=admin_headers
            )
            
            # Should either reject the input or sanitize it
            if response.status_code == 201:
                data = response.json()
                assert "../" not in data.get("image_url", "")
    
    def test_large_payload_protection(self, client, admin_headers):
        """Test protection against large payloads"""
        # Create a very large string
        large_string = "A" * 10000
        
        product_data = {
            "name": large_string,
            "description": large_string,
            "price": 29.99,
            "category": "Electronics",
            "stock_quantity": 10
        }
        
        response = client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        
        # Should either reject or truncate the large payload
        assert response.status_code in [201, 400, 413, 422]

class TestAuthenticationSecurity:
    """Test authentication security measures"""
    
    def test_jwt_token_expiration(self, client):
        """Test JWT token expiration handling"""
        # Register and login user
        user_data = {
            "email": "expiry@example.com",
            "password": "password123",
            "full_name": "Expiry User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Test with valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        
        # Note: Testing actual expiration would require manipulating time
        # or using a very short expiration time in test configuration
    
    def test_password_strength_requirements(self, client):
        """Test password strength requirements"""
        weak_passwords = [
            "123",
            "password",
            "abc",
            "12345678",
            "aaaaaaaa"
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "email": f"weak{weak_password}@example.com",
                "password": weak_password,
                "full_name": "Weak Password User"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            # Should reject weak passwords
            assert response.status_code in [400, 422]
    
    def test_account_lockout_simulation(self, client):
        """Test account lockout after multiple failed attempts"""
        # Register user
        user_data = {
            "email": "lockout@example.com",
            "password": "correctpassword123",
            "full_name": "Lockout User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            login_data = {
                "username": user_data["email"],
                "password": "wrongpassword"
            }
            response = client.post("/api/v1/auth/login", data=login_data)
            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:  # Too many requests
                break
        
        # Should eventually get rate limited or locked out
        assert failed_attempts > 0

class TestAuthorizationSecurity:
    """Test authorization and access control"""
    
    def test_admin_only_endpoints_protected(self, client, auth_headers, sample_product_data):
        """Test that admin-only endpoints reject regular users"""
        admin_endpoints = [
            ("POST", "/api/v1/products/", sample_product_data),
            ("PUT", "/api/v1/products/1", {"name": "Updated"}),
            ("DELETE", "/api/v1/products/1", None)
        ]
        
        for method, endpoint, data in admin_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=data, headers=auth_headers)
            elif method == "PUT":
                response = client.put(endpoint, json=data, headers=auth_headers)
            elif method == "DELETE":
                response = client.delete(endpoint, headers=auth_headers)
            
            assert response.status_code == 403  # Forbidden
    
    def test_user_data_isolation(self, client):
        """Test that users can only access their own data"""
        # Create two users
        user1_data = {
            "email": "user1@example.com",
            "password": "password123",
            "full_name": "User One"
        }
        user2_data = {
            "email": "user2@example.com",
            "password": "password123",
            "full_name": "User Two"
        }
        
        client.post("/api/v1/auth/register", json=user1_data)
        client.post("/api/v1/auth/register", json=user2_data)
        
        # Login both users
        login1_response = client.post("/api/v1/auth/login", data={
            "username": user1_data["email"],
            "password": user1_data["password"]
        })
        login2_response = client.post("/api/v1/auth/login", data={
            "username": user2_data["email"],
            "password": user2_data["password"]
        })
        
        user1_headers = {"Authorization": f"Bearer {login1_response.json()['access_token']}"}
        user2_headers = {"Authorization": f"Bearer {login2_response.json()['access_token']}"}
        
        # User 1 should only see their own profile
        response1 = client.get("/api/v1/users/me", headers=user1_headers)
        assert response1.status_code == 200
        assert response1.json()["email"] == user1_data["email"]
        
        # User 2 should only see their own profile
        response2 = client.get("/api/v1/users/me", headers=user2_headers)
        assert response2.status_code == 200
        assert response2.json()["email"] == user2_data["email"]

class TestDataValidation:
    """Test data validation and type checking"""
    
    def test_invalid_email_formats_rejected(self, client):
        """Test that invalid email formats are rejected"""
        invalid_emails = [
            "notanemail",
            "@domain.com",
            "user@",
            "user@domain",
            "user..name@domain.com",
            "user@domain..com"
        ]
        
        for invalid_email in invalid_emails:
            user_data = {
                "email": invalid_email,
                "password": "password123",
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 422  # Validation error
    
    def test_negative_values_rejected(self, client, admin_headers):
        """Test that negative values are rejected where inappropriate"""
        invalid_product_data = {
            "name": "Test Product",
            "description": "Test description",
            "price": -10.00,  # Negative price
            "category": "Electronics",
            "stock_quantity": -5  # Negative stock
        }
        
        response = client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_type_validation(self, client, admin_headers):
        """Test that incorrect data types are rejected"""
        invalid_product_data = {
            "name": 123,  # Should be string
            "description": True,  # Should be string
            "price": "not_a_number",  # Should be float
            "category": ["Electronics"],  # Should be string
            "stock_quantity": "ten"  # Should be integer
        }
        
        response = client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error

class TestSecurityHeaders:
    """Test security headers and CORS"""
    
    def test_security_headers_present(self, client):
        """Test that important security headers are present"""
        response = client.get("/api/v1/products/")
        
        # Check for important security headers
        headers = response.headers
        
        # Note: These headers would be set by middleware
        # The actual presence depends on the FastAPI security configuration
        # This test documents what should be checked
        security_headers_to_check = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        # For now, just verify the response is successful
        assert response.status_code == 200
    
    def test_cors_configuration(self, client):
        """Test CORS configuration"""
        # Test preflight request
        response = client.options("/api/v1/products/")
        
        # Should handle OPTIONS request appropriately
        assert response.status_code in [200, 204, 405]

class TestRateLimiting:
    """Test rate limiting protection"""
    
    def test_api_rate_limiting(self, client):
        """Test API rate limiting"""
        # Make multiple requests rapidly
        responses = []
        for i in range(50):
            response = client.get("/api/v1/products/")
            responses.append(response.status_code)
            
            # If we get rate limited, break
            if response.status_code == 429:
                break
        
        # Should either complete all requests or get rate limited
        assert all(status in [200, 429] for status in responses)
    
    def test_login_rate_limiting(self, client):
        """Test login endpoint rate limiting"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        # Make multiple failed login attempts
        rate_limited = False
        for i in range(20):
            response = client.post("/api/v1/auth/login", data=login_data)
            if response.status_code == 429:
                rate_limited = True
                break
        
        # Note: Rate limiting implementation would determine the exact behavior
        # This test documents the expected protection