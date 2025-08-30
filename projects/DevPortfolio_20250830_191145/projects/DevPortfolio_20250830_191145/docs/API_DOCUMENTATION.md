# DevPortfolio API Documentation

## Overview
Base URL: `/api/v1`

## Authentication
All endpoints require JWT authentication unless specified.

### Authentication Endpoints

#### `POST /auth/login`
Authenticate and receive JWT token

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response**:
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer"
}
```

## Projects Endpoints

### `GET /projects`
Retrieve list of projects

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10)
- `tags`: Comma-separated technology tags

**Response**:
```json
{
  "projects": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "technologies": ["React", "FastAPI"],
      "github_link": "https://github.com/example",
      "demo_link": "https://example.com"
    }
  ],
  "total": 50,
  "page": 1
}
```

### `GET /projects/{project_id}`
Get detailed project information

## Blog Endpoints

### `GET /blog/posts`
Retrieve blog posts

**Query Parameters**:
- `category`: Filter by category
- `tag`: Filter by tag
- `search`: Search query

### `POST /blog/posts`
Create a new blog post (Admin only)

**Request Body**:
```json
{
  "title": "string",
  "content": "markdown_content",
  "tags": ["tech", "tutorial"],
  "category": "string"
}
```

## AI Writing Assistant

### `POST /ai/suggest`
Get AI-powered content suggestions

**Request Body**:
```json
{
  "text": "Initial draft content",
  "context": "blog_post"
}
```

**Response**:
```json
{
  "suggestions": [
    "Improved sentence",
    "Grammar correction",
    "SEO optimization tip"
  ]
}
```

## Error Handling
All endpoints return standardized error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error description"
}
```

## Rate Limiting
- Max 100 requests/minute per endpoint
- Exceeding limit returns 429 Too Many Requests

## Versioning
Current API Version: v1
Backwards-compatible changes will be made in the same version.
Major version changes will be announced.