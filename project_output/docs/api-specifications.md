# QuickShop MVP API Specifications

## API Overview
RESTful API built with FastAPI, following OpenAPI 3.0 specification with automatic documentation generation.

**Base URL**: `http://localhost:8000/api/v1`
**Authentication**: JWT Bearer tokens
**Content-Type**: `application/json`

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Response (201 Created)**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Email already exists

### POST /auth/login
Authenticate user and receive access token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Missing required fields

### POST /auth/refresh
Refresh access token (future implementation).

### GET /auth/me
Get current user information (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Response (200 OK)**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Product Catalog Endpoints

### GET /products
Get paginated list of products with optional filtering.

**Query Parameters**:
- `page` (int, default=1): Page number
- `limit` (int, default=20, max=100): Items per page
- `category_id` (int, optional): Filter by category
- `search` (string, optional): Search in name and description
- `min_price` (decimal, optional): Minimum price filter
- `max_price` (decimal, optional): Maximum price filter
- `sort_by` (string, optional): Sort field (name, price, created_at)
- `sort_order` (string, optional): asc or desc

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "description": "High-quality wireless headphones with noise cancellation",
      "price": 199.99,
      "category": {
        "id": 1,
        "name": "Electronics"
      },
      "sku": "WH-001",
      "stock_quantity": 50,
      "image_url": "https://example.com/images/headphones.jpg",
      "is_active": true,
      "created_at": "2024-01-10T08:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "total_pages": 5
}
```

### GET /products/{product_id}
Get detailed information about a specific product.

**Response (200 OK)**:
```json
{
  "id": 1,
  "name": "Wireless Headphones",
  "description": "High-quality wireless headphones with noise cancellation. Features include 30-hour battery life, active noise cancellation, and premium sound quality.",
  "price": 199.99,
  "category": {
    "id": 1,
    "name": "Electronics",
    "description": "Electronic devices and accessories"
  },
  "sku": "WH-001",
  "stock_quantity": 50,
  "image_url": "https://example.com/images/headphones.jpg",
  "is_active": true,
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-10T08:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Product not found

### GET /categories
Get list of product categories.

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Electronics",
      "description": "Electronic devices and accessories",
      "parent_id": null,
      "is_active": true,
      "product_count": 25
    },
    {
      "id": 2,
      "name": "Headphones",
      "description": "Audio devices",
      "parent_id": 1,
      "is_active": true,
      "product_count": 8
    }
  ]
}
```

## Shopping Cart Endpoints

### GET /cart
Get current user's cart items (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Wireless Headphones",
        "price": 199.99,
        "image_url": "https://example.com/images/headphones.jpg",
        "stock_quantity": 50
      },
      "quantity": 2,
      "subtotal": 399.98,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total_items": 2,
  "total_amount": 399.98
}
```

### POST /cart/items
Add item to cart (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "product_id": 1,
  "quantity": 2
}
```

**Response (201 Created)**:
```json
{
  "message": "Item added to cart",
  "cart_item": {
    "id": 1,
    "product": {
      "id": 1,
      "name": "Wireless Headphones",
      "price": 199.99
    },
    "quantity": 2,
    "subtotal": 399.98
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid product_id or quantity
- `409 Conflict`: Insufficient stock

### PUT /cart/items/{cart_item_id}
Update cart item quantity (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "quantity": 3
}
```

**Response (200 OK)**:
```json
{
  "message": "Cart item updated",
  "cart_item": {
    "id": 1,
    "quantity": 3,
    "subtotal": 599.97
  }
}
```

### DELETE /cart/items/{cart_item_id}
Remove item from cart (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Response (200 OK)**:
```json
{
  "message": "Item removed from cart"
}
```

### DELETE /cart
Clear all items from cart (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Response (200 OK)**:
```json
{
  "message": "Cart cleared"
}
```

## Order Management Endpoints

### GET /orders
Get user's order history (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `page` (int, default=1): Page number
- `limit` (int, default=10): Items per page
- `status` (string, optional): Filter by order status

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 1,
      "status": "delivered",
      "total_amount": 399.98,
      "payment_status": "paid",
      "created_at": "2024-01-10T10:00:00Z",
      "item_count": 2
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 10
}
```

### GET /orders/{order_id}
Get detailed order information (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Response (200 OK)**:
```json
{
  "id": 1,
  "status": "delivered",
  "total_amount": 399.98,
  "shipping_address": "123 Main St, City, State 12345",
  "billing_address": "123 Main St, City, State 12345",
  "payment_status": "paid",
  "payment_method": "credit_card",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Wireless Headphones",
        "sku": "WH-001"
      },
      "quantity": 2,
      "unit_price": 199.99,
      "total_price": 399.98
    }
  ],
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-12T14:30:00Z"
}
```

### POST /orders
Create new order from cart (requires authentication).

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "shipping_address": "123 Main St, City, State 12345",
  "billing_address": "123 Main St, City, State 12345",
  "payment_method": "credit_card",
  "notes": "Please deliver after 5 PM"
}
```

**Response (201 Created)**:
```json
{
  "message": "Order created successfully",
  "order": {
    "id": 1,
    "status": "pending",
    "total_amount": 399.98,
    "payment_status": "pending",
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Empty cart or invalid address
- `409 Conflict`: Insufficient stock for some items

## Error Response Format

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute per IP
- **General API**: 100 requests per minute per user
- **Search endpoints**: 20 requests per minute per user

## Status Codes Used

- `200 OK`: Successful GET, PUT, DELETE requests
- `201 Created`: Successful POST requests
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (duplicate email, insufficient stock)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Authentication Flow

1. User registers or logs in to receive JWT token
2. Token included in `Authorization: Bearer <token>` header
3. Token expires after 1 hour (configurable)
4. Refresh token mechanism for seamless re-authentication (future)

## Data Validation

All request bodies are validated using Pydantic schemas with:
- Type checking
- Format validation (email, phone, etc.)
- Range validation (prices, quantities)
- Required field validation
- Custom business rule validation