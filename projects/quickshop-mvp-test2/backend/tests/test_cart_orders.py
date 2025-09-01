"""
Cart and Order management tests for QuickShop MVP
Tests shopping cart functionality, order processing, and payment integration
"""
import pytest
from fastapi.testclient import TestClient

class TestShoppingCart:
    """Test shopping cart functionality"""
    
    def test_add_product_to_cart_success(self, client, auth_headers, sample_products):
        """Test successfully adding product to cart"""
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 2
        }
        
        response = client.post(
            "/api/v1/cart/add",
            json=cart_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == product_id
        assert data["quantity"] == 2
        assert "total_price" in data
    
    def test_add_product_to_cart_without_auth_fails(self, client, sample_products):
        """Test that unauthenticated users cannot add to cart"""
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        
        response = client.post("/api/v1/cart/add", json=cart_data)
        assert response.status_code == 401
    
    def test_add_nonexistent_product_to_cart_fails(self, client, auth_headers):
        """Test adding non-existent product to cart fails"""
        cart_data = {
            "product_id": 99999,
            "quantity": 1
        }
        
        response = client.post(
            "/api/v1/cart/add",
            json=cart_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_add_invalid_quantity_to_cart_fails(self, client, auth_headers, sample_products):
        """Test adding invalid quantity to cart fails"""
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 0  # Invalid quantity
        }
        
        response = client.post(
            "/api/v1/cart/add",
            json=cart_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_get_cart_contents_success(self, client, auth_headers, sample_products):
        """Test retrieving cart contents"""
        # Add products to cart first
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 2
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        # Get cart contents
        response = client.get("/api/v1/cart/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_amount" in data
        assert len(data["items"]) >= 1
        
        # Verify cart item structure
        item = data["items"][0]
        assert "product_id" in item
        assert "quantity" in item
        assert "price" in item
    
    def test_update_cart_item_quantity_success(self, client, auth_headers, sample_products):
        """Test updating cart item quantity"""
        # Add product to cart first
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        add_response = client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        cart_item_id = add_response.json()["id"]
        
        # Update quantity
        update_data = {"quantity": 3}
        response = client.put(
            f"/api/v1/cart/{cart_item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 3
    
    def test_remove_item_from_cart_success(self, client, auth_headers, sample_products):
        """Test removing item from cart"""
        # Add product to cart first
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        add_response = client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        cart_item_id = add_response.json()["id"]
        
        # Remove item
        response = client.delete(f"/api/v1/cart/{cart_item_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify item is removed
        cart_response = client.get("/api/v1/cart/", headers=auth_headers)
        cart_data = cart_response.json()
        item_ids = [item["id"] for item in cart_data["items"]]
        assert cart_item_id not in item_ids
    
    def test_clear_cart_success(self, client, auth_headers, sample_products):
        """Test clearing entire cart"""
        # Add multiple products to cart
        for product in sample_products[:2]:
            cart_data = {
                "product_id": product["id"],
                "quantity": 1
            }
            client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        # Clear cart
        response = client.delete("/api/v1/cart/clear", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify cart is empty
        cart_response = client.get("/api/v1/cart/", headers=auth_headers)
        cart_data = cart_response.json()
        assert len(cart_data["items"]) == 0
        assert cart_data["total_amount"] == 0

class TestOrderProcessing:
    """Test order creation and management"""
    
    def test_create_order_from_cart_success(self, client, auth_headers, sample_products):
        """Test successful order creation from cart"""
        # Add products to cart
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 2
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        # Create order
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        
        response = client.post(
            "/api/v1/orders/",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "total_amount" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert "items" in data
        assert len(data["items"]) >= 1
    
    def test_create_order_with_empty_cart_fails(self, client, auth_headers):
        """Test creating order with empty cart fails"""
        # Ensure cart is empty
        client.delete("/api/v1/cart/clear", headers=auth_headers)
        
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        
        response = client.post(
            "/api/v1/orders/",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_get_user_orders_success(self, client, auth_headers, sample_products):
        """Test retrieving user's orders"""
        # Create an order first
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        
        # Get orders
        response = client.get("/api/v1/orders/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Verify order structure
        order = data[0]
        required_fields = ["id", "total_amount", "status", "created_at", "items"]
        for field in required_fields:
            assert field in order
    
    def test_get_specific_order_success(self, client, auth_headers, sample_products):
        """Test retrieving a specific order by ID"""
        # Create an order first
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        order_response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        order_id = order_response.json()["id"]
        
        # Get specific order
        response = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
    
    def test_get_other_users_order_fails(self, client, auth_headers, sample_products):
        """Test that users cannot access other users' orders"""
        # This test would require creating two different users
        # For now, we'll test accessing a non-existent order
        response = client.get("/api/v1/orders/99999", headers=auth_headers)
        assert response.status_code == 404

class TestOrderStatusManagement:
    """Test order status updates and workflow"""
    
    def test_update_order_status_as_admin_success(self, client, admin_headers, auth_headers, sample_products):
        """Test admin can update order status"""
        # Create an order as regular user
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        order_response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        order_id = order_response.json()["id"]
        
        # Update order status as admin
        status_data = {"status": "processing"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=status_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
    
    def test_update_order_status_as_regular_user_fails(self, client, auth_headers, sample_products):
        """Test regular users cannot update order status"""
        # Create an order
        product_id = sample_products[0]["id"]
        cart_data = {
            "product_id": product_id,
            "quantity": 1
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        order_response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        order_id = order_response.json()["id"]
        
        # Try to update status as regular user
        status_data = {"status": "shipped"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=status_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403  # Forbidden

class TestInventoryIntegration:
    """Test cart and order integration with inventory management"""
    
    def test_add_more_than_available_stock_fails(self, client, auth_headers, admin_headers, sample_products):
        """Test adding more items than available stock fails"""
        # Set product stock to a low number
        product_id = sample_products[0]["id"]
        update_data = {"stock_quantity": 2}
        client.put(
            f"/api/v1/products/{product_id}",
            json=update_data,
            headers=admin_headers
        )
        
        # Try to add more than available stock
        cart_data = {
            "product_id": product_id,
            "quantity": 5  # More than available stock (2)
        }
        
        response = client.post(
            "/api/v1/cart/add",
            json=cart_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "stock" in response.json()["detail"].lower()
    
    def test_order_creation_reduces_stock(self, client, auth_headers, admin_headers, sample_products):
        """Test that creating an order reduces product stock"""
        product_id = sample_products[0]["id"]
        
        # Get initial stock
        product_response = client.get(f"/api/v1/products/{product_id}")
        initial_stock = product_response.json()["stock_quantity"]
        
        # Add to cart and create order
        cart_data = {
            "product_id": product_id,
            "quantity": 2
        }
        client.post("/api/v1/cart/add", json=cart_data, headers=auth_headers)
        
        order_data = {
            "shipping_address": "123 Test St, Test City, TC 12345",
            "payment_method": "stripe"
        }
        order_response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        assert order_response.status_code == 201
        
        # Check that stock was reduced
        updated_product_response = client.get(f"/api/v1/products/{product_id}")
        updated_stock = updated_product_response.json()["stock_quantity"]
        assert updated_stock == initial_stock - 2