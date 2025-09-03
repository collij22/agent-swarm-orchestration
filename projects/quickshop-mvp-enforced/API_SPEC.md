# QuickShop MVP API Specification

## Overview
REST API for the QuickShop e-commerce platform MVP. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL
```
https://api.quickshop.com/v1
```

## Authentication
Bearer token authentication required for protected endpoints.
```
Authorization: Bearer <token>
```

## Endpoints

### Authentication
#### POST /auth/register
Register a new user account.
```json
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1234567890"
}
```
**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "token": "jwt_token"
}
```

#### POST /auth/login
Authenticate user and get access token.
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response:** `200 OK`
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "token": "jwt_token"
}
```

### Products
#### GET /products
Get paginated list of products.
**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `category` (optional)
- `search` (optional)
- `minPrice` (optional)
- `maxPrice` (optional)

**Response:** `200 OK`
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "Product Name",
      "description": "Product description",
      "price": 29.99,
      "category": "Electronics",
      "imageUrl": "https://example.com/image.jpg",
      "stock": 100,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### GET /products/{id}
Get single product by ID.
**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Product Name",
  "description": "Detailed product description",
  "price": 29.99,
  "category": "Electronics",
  "imageUrl": "https://example.com/image.jpg",
  "stock": 100,
  "specifications": {
    "brand": "BrandName",
    "model": "Model123"
  },
  "createdAt": "2024-01-01T00:00:00Z"
}
```

### Shopping Cart
#### GET /cart
Get current user's cart (requires auth).
**Response:** `200 OK`
```json
{
  "id": "uuid",
  "items": [
    {
      "id": "uuid",
      "productId": "uuid",
      "product": {
        "name": "Product Name",
        "price": 29.99,
        "imageUrl": "https://example.com/image.jpg"
      },
      "quantity": 2,
      "subtotal": 59.98
    }
  ],
  "total": 59.98,
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

#### POST /cart/items
Add item to cart (requires auth).
```json
{
  "productId": "uuid",
  "quantity": 2
}
```
**Response:** `201 Created`

#### PUT /cart/items/{itemId}
Update cart item quantity (requires auth).
```json
{
  "quantity": 3
}
```
**Response:** `200 OK`

#### DELETE /cart/items/{itemId}
Remove item from cart (requires auth).
**Response:** `204 No Content`

### Orders
#### POST /orders
Create new order from cart (requires auth).
```json
{
  "shippingAddress": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zipCode": "12345",
    "country": "US"
  },
  "paymentMethod": "credit_card",
  "paymentDetails": {
    "cardToken": "stripe_token"
  }
}
```
**Response:** `201 Created`
```json
{
  "id": "uuid",
  "orderNumber": "ORD-001",
  "status": "pending",
  "total": 59.98,
  "items": [...],
  "shippingAddress": {...},
  "createdAt": "2024-01-01T00:00:00Z"
}
```

#### GET /orders
Get user's order history (requires auth).
**Response:** `200 OK`
```json
{
  "orders": [
    {
      "id": "uuid",
      "orderNumber": "ORD-001",
      "status": "delivered",
      "total": 59.98,
      "itemCount": 2,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /orders/{id}
Get single order details (requires auth).
**Response:** `200 OK`
```json
{
  "id": "uuid",
  "orderNumber": "ORD-001",
  "status": "shipped",
  "total": 59.98,
  "items": [...],
  "shippingAddress": {...},
  "trackingNumber": "1Z999AA1234567890",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-02T00:00:00Z"
}
```

### Categories
#### GET /categories
Get all product categories.
**Response:** `200 OK`
```json
{
  "categories": [
    {
      "id": "uuid",
      "name": "Electronics",
      "slug": "electronics",
      "productCount": 150
    }
  ]
}
```

## Error Responses
All error responses follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Email format is invalid"
    }
  }
}
```

## Status Codes
- `200` - OK
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Unprocessable Entity
- `500` - Internal Server Error