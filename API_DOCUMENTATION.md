# TaskManagerAPI - Comprehensive API Guide

## Authentication Endpoints

### User Registration
- **Endpoint**: `POST /api/v1/auth/register`
- **Purpose**: Create a new user account
- **Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```
- **Success Response** (201):
```json
{
  "id": "uuid-generated-id",
  "username": "johndoe",
  "email": "john@example.com",
  "created_at": "2023-09-01T12:00:00Z"
}
```

### User Login
- **Endpoint**: `POST /api/v1/auth/login`
- **Purpose**: Authenticate user and receive JWT tokens
- **Request Body**:
```json
{
  "username": "johndoe",
  "password": "securePassword123"
}
```
- **Success Response** (200):
```json
{
  "access_token": "jwt.token.here",
  "refresh_token": "refresh.token.here",
  "token_type": "bearer"
}
```

## Task Management Endpoints

### Create Task
- **Endpoint**: `POST /api/v1/tasks`
- **Purpose**: Create a new task with AI-powered categorization
- **Request Body**:
```json
{
  "title": "Implement user authentication",
  "description": "Complete JWT-based authentication for the TaskManagerAPI"
}
```
- **Success Response** (201):
```json
{
  "id": "task-uuid",
  "title": "Implement user authentication",
  "description": "Complete JWT-based authentication for the TaskManagerAPI",
  "category": "Development",
  "priority": 4,
  "status": "todo",
  "created_at": "2023-09-01T12:00:00Z"
}
```

### List Tasks
- **Endpoint**: `GET /api/v1/tasks`
- **Purpose**: Retrieve all tasks for the authenticated user
- **Query Parameters**:
  - `status`: Filter by task status
  - `category`: Filter by task category
  - `priority`: Filter by task priority

### Update Task
- **Endpoint**: `PUT /api/v1/tasks/{task_id}`
- **Purpose**: Update an existing task
- **Request Body**:
```json
{
  "title": "Updated task title",
  "status": "in_progress"
}
```

### AI Categorization
- **Endpoint**: `POST /api/v1/tasks/{task_id}/categorize`
- **Purpose**: Re-run AI categorization for a specific task
- **Response**:
```json
{
  "category": "Software Development",
  "confidence": 0.92
}
```

## Error Handling
All endpoints return standardized error responses:
```json
{
  "error": "Descriptive error message",
  "code": "ERROR_CODE"
}
```

## Rate Limiting
- Max 100 requests per minute
- Excess requests return 429 Too Many Requests

## Best Practices
- Always include Authorization header with JWT token
- Handle token refresh before expiration
- Implement robust error handling in client applications