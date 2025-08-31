## Comprehensive Agent and Documentation Updates Plan

### 1. **CLAUDE.md Updates** (Global Instructions)

Add new section after "Important Instruction Reminders":

```markdown
## 🚨 Critical Implementation Standards

### IMPORTANT: Actual File Creation Requirements
- **ALWAYS create actual source files** with working code, not just scaffolding
- **NEVER leave placeholder imports** (e.g., main.tsx must exist if imported)
- **ALWAYS include entry point files** (index.tsx, main.tsx, App.tsx for React)
- **ALWAYS create package-lock.json** after npm install for reproducible builds

### IMPORTANT: Data Seeding Requirements  
- **ALWAYS create at least 3 dummy entries** for each resource type
- **Products**: Include name, description, price, stock, and image URLs
- **Users**: Create test user with credentials (email: test@example.com, password: password123)
- **Orders**: Include at least 1 completed order for testing

### IMPORTANT: Field Consistency Standards
- **ALWAYS match field names** between frontend and backend exactly
- **Use consistent date fields**: created_at, updated_at (not order_date, etc.)
- **Verify serialization**: Test all API endpoints return proper JSON
```

### 2. **Frontend-Specialist Agent Updates**

Add to agent instructions:
```
IMPORTANT: Always create these essential files:
- src/main.tsx (Vite entry point)
- src/App.tsx (Root component with routing)
- src/pages/*.tsx (All page components)
- tsconfig.node.json (Vite TypeScript config)
- index.html (with proper script tag)

IMPORTANT: Authentication flow must:
- Include all required fields (username, email, first_name, last_name)
- Reload navigation after login/logout (window.location.reload())
- Store user object in localStorage for navigation display
```

### 3. **Rapid-Builder Agent Updates**

Add to agent instructions:
```
IMPORTANT: Backend must include:
- Complete requirements.txt with ALL dependencies
- Working /orders endpoint for checkout flow
- Simplified endpoints for complex models (e.g., /products-simple)
- Error handling for all database operations

IMPORTANT: Always verify Docker build:
- Test container starts successfully
- All dependencies are installed
- Database migrations run automatically
- Health check endpoint responds
```

### 4. **Database-Expert Agent Updates**

Add to agent instructions:
```
IMPORTANT: Database setup must:
- Create seed data script with at least 3 entries per table
- Use consistent field naming (created_at, updated_at)
- Include all required fields in OrderItem model
- Set up proper relationships with cascade options

IMPORTANT: Always create initial data:
- 3+ products with realistic data and image URLs
- 1 test user account for authentication testing
- 1+ sample orders for order history testing
```

### 5. **Quality-Guardian Agent Updates** 

Add MAJOR improvements:
```
IMPORTANT: E2E Validation Requirements:
- Test complete user flow: Register → Login → Browse → Add to Cart → Checkout → View Orders
- Verify all API endpoints return valid JSON
- Check Docker containers start and connect properly
- Test with actual HTTP requests, not just unit tests

IMPORTANT: Validation Checklist:
- [ ] Frontend builds without errors (npm run build)
- [ ] Backend starts without import errors
- [ ] Database has seed data
- [ ] Authentication flow works E2E
- [ ] All CRUD operations function
- [ ] Docker Compose brings up all services
```

### 6. **DevOps-Engineer Agent Updates**

Add to agent instructions:
```
IMPORTANT: Docker validation:
- Use 'npm install' not 'npm ci' if package-lock.json missing
- Copy ALL source files to container
- Ensure database is seeded on first run
- Add health checks for all services
- Test inter-service connectivity

IMPORTANT: Always include:
- docker-compose.yml with proper service dependencies
- .dockerignore to exclude node_modules
- Environment variable templates (.env.example)
- Volume mounts for development
```

### 7. **API-Integrator Agent Updates**

Add to agent instructions:
```
IMPORTANT: API Integration must:
- Return consistent field names across all endpoints
- Handle serialization for complex models
- Include simplified endpoints when needed
- Test all endpoints with curl before completion

IMPORTANT: Response validation:
- All endpoints must return valid JSON
- Error responses must include detail field
- Pagination must work if implemented
- Authentication headers must be validated
```

### 8. **New Testing Protocol Section in CLAUDE.md**

Add new section:
```markdown
## 🔍 Mandatory Testing Protocol

### Before Marking Any Task Complete:
1. **Build Test**: Frontend and backend must build without errors
2. **Start Test**: All services must start successfully
3. **API Test**: All endpoints must return valid responses
4. **Auth Test**: User can register, login, and see protected content
5. **Data Test**: At least one full CRUD cycle must work
6. **Docker Test**: docker-compose up must bring up all services

### Minimum Viable Deliverable:
- User can access the application
- At least one dummy entry is visible
- Basic navigation works
- No blank pages or console errors
- Docker containers stay running for 5+ minutes
```

### 9. **Update Mock Testing in CLAUDE.md**

Enhance the Mock Testing section:
```markdown
### IMPORTANT: Mock Mode Must Still Create Real Files
- Even in mock mode, create actual source files
- Validate file structure matches production requirements
- Test Docker builds even in mock mode
- Ensure seed data is created regardless of mode
```

This comprehensive update plan addresses all the issues we encountered and ensures future deliverables will be more complete and functional out of the box.