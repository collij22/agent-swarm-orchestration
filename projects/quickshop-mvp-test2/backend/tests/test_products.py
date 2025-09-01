"""
Product management tests for QuickShop MVP
Tests CRUD operations, search functionality, and authorization
"""
import pytest
from fastapi.testclient import TestClient

class TestProductCRUD:
    """Test product CRUD operations"""
    
    def test_create_product_as_admin_success(self, client, admin_headers, sample_product_data):
        """Test successful product creation by admin"""
        response = client.post(
            "/api/v1/products/", 
            json=sample_product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_product_data["name"]
        assert data["price"] == sample_product_data["price"]
        assert data["stock_quantity"] == sample_product_data["stock_quantity"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_product_as_regular_user_fails(self, client, auth_headers, sample_product_data):
        """Test that regular users cannot create products"""
        response = client.post(
            "/api/v1/products/", 
            json=sample_product_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403  # Forbidden
    
    def test_create_product_without_auth_fails(self, client, sample_product_data):
        """Test that unauthenticated users cannot create products"""
        response = client.post("/api/v1/products/", json=sample_product_data)
        assert response.status_code == 401  # Unauthorized
    
    def test_get_all_products_success(self, client, sample_products):
        """Test retrieving all products (public endpoint)"""
        response = client.get("/api/v1/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least the sample products
        
        # Verify product structure
        product = data[0]
        required_fields = ["id", "name", "description", "price", "category", "stock_quantity"]
        for field in required_fields:
            assert field in product
    
    def test_get_product_by_id_success(self, client, sample_products):
        """Test retrieving a specific product by ID"""
        product_id = sample_products[0]["id"]
        response = client.get(f"/api/v1/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == sample_products[0]["name"]
    
    def test_get_nonexistent_product_fails(self, client):
        """Test retrieving non-existent product returns 404"""
        response = client.get("/api/v1/products/99999")
        assert response.status_code == 404
    
    def test_update_product_as_admin_success(self, client, admin_headers, sample_products):
        """Test successful product update by admin"""
        product_id = sample_products[0]["id"]
        update_data = {
            "name": "Updated Product Name",
            "price": 39.99,
            "stock_quantity": 50
        }
        
        response = client.put(
            f"/api/v1/products/{product_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
        assert data["stock_quantity"] == update_data["stock_quantity"]
    
    def test_update_product_as_regular_user_fails(self, client, auth_headers, sample_products):
        """Test that regular users cannot update products"""
        product_id = sample_products[0]["id"]
        update_data = {"name": "Unauthorized Update"}
        
        response = client.put(
            f"/api/v1/products/{product_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403  # Forbidden
    
    def test_delete_product_as_admin_success(self, client, admin_headers, sample_products):
        """Test successful product deletion by admin"""
        product_id = sample_products[0]["id"]
        
        response = client.delete(
            f"/api/v1/products/{product_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 204  # No content
        
        # Verify product is deleted
        get_response = client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 404
    
    def test_delete_product_as_regular_user_fails(self, client, auth_headers, sample_products):
        """Test that regular users cannot delete products"""
        product_id = sample_products[0]["id"]
        
        response = client.delete(
            f"/api/v1/products/{product_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403  # Forbidden

class TestProductSearch:
    """Test product search and filtering functionality"""
    
    def test_search_products_by_name(self, client, sample_products):
        """Test searching products by name"""
        search_term = "Test Product 1"
        response = client.get(f"/api/v1/products/search?q={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Verify search results contain the search term
        found_product = next((p for p in data if search_term in p["name"]), None)
        assert found_product is not None
    
    def test_filter_products_by_category(self, client, sample_products):
        """Test filtering products by category"""
        category = "Electronics"
        response = client.get(f"/api/v1/products/?category={category}")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned products should be in the specified category
        for product in data:
            assert product["category"] == category
    
    def test_filter_products_by_price_range(self, client, sample_products):
        """Test filtering products by price range"""
        min_price = 20
        max_price = 40
        response = client.get(f"/api/v1/products/?min_price={min_price}&max_price={max_price}")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned products should be within price range
        for product in data:
            assert min_price <= product["price"] <= max_price
    
    def test_pagination_works(self, client, sample_products):
        """Test product listing pagination"""
        response = client.get("/api/v1/products/?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2  # Should return at most 2 products

class TestProductValidation:
    """Test product data validation"""
    
    def test_create_product_with_invalid_data_fails(self, client, admin_headers):
        """Test creating product with invalid data fails validation"""
        invalid_data = {
            "name": "",  # Empty name
            "price": -10,  # Negative price
            "stock_quantity": -5  # Negative stock
        }
        
        response = client.post(
            "/api/v1/products/", 
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_product_with_missing_required_fields_fails(self, client, admin_headers):
        """Test creating product with missing required fields fails"""
        incomplete_data = {
            "name": "Test Product"
            # Missing required fields like price, description, etc.
        }
        
        response = client.post(
            "/api/v1/products/", 
            json=incomplete_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_product_with_xss_attempt_sanitized(self, client, admin_headers):
        """Test that XSS attempts in product data are sanitized"""
        xss_data = {
            "name": "<script>alert('xss')</script>Malicious Product",
            "description": "<img src=x onerror=alert('xss')>",
            "price": 29.99,
            "category": "Electronics",
            "stock_quantity": 10
        }
        
        response = client.post(
            "/api/v1/products/", 
            json=xss_data,
            headers=admin_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # XSS should be sanitized or escaped
            assert "<script>" not in data["name"]
            assert "onerror=" not in data["description"]

class TestInventoryManagement:
    """Test inventory-related functionality"""
    
    def test_stock_quantity_updates_correctly(self, client, admin_headers, sample_products):
        """Test that stock quantity updates work correctly"""
        product_id = sample_products[0]["id"]
        original_stock = sample_products[0]["stock_quantity"]
        new_stock = original_stock - 10
        
        update_data = {"stock_quantity": new_stock}
        response = client.put(
            f"/api/v1/products/{product_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock_quantity"] == new_stock
    
    def test_out_of_stock_products_identifiable(self, client, admin_headers, sample_products):
        """Test that out-of-stock products can be identified"""
        product_id = sample_products[0]["id"]
        
        # Set stock to 0
        update_data = {"stock_quantity": 0}
        response = client.put(
            f"/api/v1/products/{product_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        
        # Get product and verify stock is 0
        get_response = client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["stock_quantity"] == 0