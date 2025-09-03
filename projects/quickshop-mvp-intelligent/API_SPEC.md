# QuickShop MVP API Documentation

## Overview
RESTful API for QuickShop MVP e-commerce platform.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Users

#### Register User
- **POST** `/users/register`
- **Body**: `{ "email": "string", "password": "string" }`
- **Response**: `{ "id": "uuid", "email": "string", "token": "string" }`

#### Login
- **POST** `/users/login`
- **Body**: `{ "email": "string", "password": "string" }`
- **Response**: `{ "token": "string", "user": { ... } }`

### Products

#### List Products
- **GET** `/products`
- **Query**: `?page=1&limit=10&category=electronics`
- **Response**: `{ "products": [...], "total": 100, "page": 1 }`

#### Get Product
- **GET** `/products/{id}`
- **Response**: Product object

#### Create Product (Admin)
- **POST** `/products`
- **Auth**: Required (Admin)
- **Body**: Product data
- **Response**: Created product

### Orders

#### Create Order
- **POST** `/orders`
- **Auth**: Required
- **Body**: `{ "items": [...], "shipping_address": { ... } }`
- **Response**: Order object

#### Get User Orders
- **GET** `/orders`
- **Auth**: Required
- **Response**: List of user's orders

## Error Responses
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [...]
  }
}
```

## Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user
