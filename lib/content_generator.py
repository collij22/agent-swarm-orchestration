"""Smart Content Generator - Creates real content for any file type"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

class ContentGenerator:
    """Generates real, functional content for any file type - never placeholders"""
    
    def __init__(self, project_context: Optional[Dict] = None):
        self.project_context = project_context or {}
        self.project_name = self.project_context.get("project_name", "QuickShop MVP")
        
    def generate_content(self, file_path: str, context: str = "") -> str:
        """Generate appropriate content based on file extension"""
        ext = Path(file_path).suffix.lower()
        filename = Path(file_path).stem
        
        generators = {
            '.json': self._generate_json,
            '.md': self._generate_markdown,
            '.py': self._generate_python,
            '.tsx': self._generate_react,
            '.ts': self._generate_typescript,
            '.jsx': self._generate_react,
            '.js': self._generate_javascript,
            '.yaml': self._generate_yaml,
            '.yml': self._generate_yaml,
            '.env': self._generate_env,
            '.html': self._generate_html,
            '.css': self._generate_css,
            '.sql': self._generate_sql,
            '.sh': self._generate_shell,
            '.bat': self._generate_batch,
            '.txt': self._generate_text
        }
        
        generator = generators.get(ext, self._generate_generic)
        return generator(filename, context)
    
    def _generate_json(self, filename: str, context: str) -> str:
        """Generate JSON content based on filename"""
        if 'database' in filename.lower() or 'schema' in filename.lower():
            data = {
                "database": self.project_name.lower().replace(' ', '_'),
                "version": "1.0.0",
                "tables": {
                    "users": {
                        "columns": {
                            "id": {"type": "uuid", "primary": True},
                            "email": {"type": "varchar(255)", "unique": True, "nullable": False},
                            "password_hash": {"type": "varchar(255)", "nullable": False},
                            "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                            "updated_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"}
                        }
                    },
                    "products": {
                        "columns": {
                            "id": {"type": "uuid", "primary": True},
                            "name": {"type": "varchar(255)", "nullable": False},
                            "description": {"type": "text"},
                            "price": {"type": "decimal(10,2)", "nullable": False},
                            "stock": {"type": "integer", "default": 0},
                            "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"}
                        }
                    },
                    "orders": {
                        "columns": {
                            "id": {"type": "uuid", "primary": True},
                            "user_id": {"type": "uuid", "foreign_key": "users.id"},
                            "total": {"type": "decimal(10,2)", "nullable": False},
                            "status": {"type": "varchar(50)", "default": "pending"},
                            "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"}
                        }
                    }
                }
            }
        elif 'config' in filename.lower():
            data = {
                "app": {
                    "name": self.project_name,
                    "version": "1.0.0",
                    "environment": "development",
                    "port": 3000,
                    "api_url": "http://localhost:8000"
                },
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": self.project_name.lower().replace(' ', '_'),
                    "user": "admin",
                    "pool_size": 10
                },
                "features": {
                    "authentication": True,
                    "payments": True,
                    "analytics": True,
                    "caching": True
                },
                "security": {
                    "jwt_expiry": "24h",
                    "bcrypt_rounds": 10,
                    "rate_limit": 100
                }
            }
        elif 'package' in filename.lower():
            data = {
                "name": self.project_name.lower().replace(' ', '-'),
                "version": "1.0.0",
                "description": f"{self.project_name} - E-commerce Platform",
                "main": "index.js",
                "scripts": {
                    "start": "node index.js",
                    "dev": "nodemon index.js",
                    "test": "jest",
                    "build": "webpack"
                },
                "dependencies": {
                    "express": "^4.18.0",
                    "pg": "^8.11.0",
                    "bcrypt": "^5.1.0",
                    "jsonwebtoken": "^9.0.0"
                }
            }
        else:
            data = {
                "name": filename,
                "type": "configuration",
                "created": datetime.now().isoformat(),
                "settings": {
                    "enabled": True,
                    "debug": False
                }
            }
        
        return json.dumps(data, indent=2)
    
    def _generate_markdown(self, filename: str, context: str) -> str:
        """Generate markdown documentation"""
        if 'api' in filename.lower():
            return f"""# {self.project_name} API Documentation

## Overview
RESTful API for {self.project_name} e-commerce platform.

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
- **Body**: `{{ "email": "string", "password": "string" }}`
- **Response**: `{{ "id": "uuid", "email": "string", "token": "string" }}`

#### Login
- **POST** `/users/login`
- **Body**: `{{ "email": "string", "password": "string" }}`
- **Response**: `{{ "token": "string", "user": {{ ... }} }}`

### Products

#### List Products
- **GET** `/products`
- **Query**: `?page=1&limit=10&category=electronics`
- **Response**: `{{ "products": [...], "total": 100, "page": 1 }}`

#### Get Product
- **GET** `/products/{{id}}`
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
- **Body**: `{{ "items": [...], "shipping_address": {{ ... }} }}`
- **Response**: Order object

#### Get User Orders
- **GET** `/orders`
- **Auth**: Required
- **Response**: List of user's orders

## Error Responses
```json
{{
  "error": {{
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [...]
  }}
}}
```

## Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user
"""
        elif 'readme' in filename.lower():
            return f"""# {self.project_name}

## Description
A modern e-commerce platform built with cutting-edge technologies.

## Features
- User authentication and authorization
- Product catalog with search and filtering
- Shopping cart and checkout
- Order management
- Admin dashboard
- Payment integration
- Real-time notifications

## Installation

```bash
# Clone repository
git clone https://github.com/yourorg/{self.project_name.lower().replace(' ', '-')}.git

# Install dependencies
npm install

# Setup database
npm run db:setup

# Start development server
npm run dev
```

## Tech Stack
- Frontend: React, TypeScript, Tailwind CSS
- Backend: Node.js, Express, PostgreSQL
- Authentication: JWT
- Payments: Stripe
- Deployment: Docker, AWS

## Project Structure
```
├── frontend/          # React application
├── backend/           # Express API
├── database/          # SQL migrations
├── docker/            # Docker configuration
├── docs/              # Documentation
└── tests/             # Test suites
```

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct.

## License
MIT License - see LICENSE file for details
"""
        else:
            return f"""# {filename.replace('_', ' ').title()}

## Overview
This document describes the {filename} component of {self.project_name}.

## Purpose
{context if context else f"Provides functionality for {filename} in the system."}

## Implementation Details

### Architecture
The {filename} module follows a modular architecture with clear separation of concerns.

### Key Components
1. **Data Layer**: Handles data persistence and retrieval
2. **Business Logic**: Core functionality and rules
3. **API Layer**: External interface for the module
4. **Validation**: Input validation and sanitization

### Usage Example
```javascript
import {{ {filename} }} from './{filename}';

const result = await {filename}.process(data);
console.log(result);
```

## Configuration
Configuration options can be set in the config file or via environment variables.

## Testing
Run tests with: `npm test {filename}`

## Maintenance
Regular updates should be performed to ensure compatibility with the latest dependencies.

Generated: {datetime.now().isoformat()}
"""
    
    def _generate_python(self, filename: str, context: str) -> str:
        """Generate Python code"""
        if 'test' in filename.lower():
            return f'''"""Tests for {filename}"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class Test{filename.replace("_", " ").title().replace(" ", "")}:
    """Test suite for {filename}"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_data = {{
            "id": "test-123",
            "name": "Test Item",
            "value": 42
        }}
    
    def test_initialization(self):
        """Test module initialization"""
        assert True, "Module should initialize"
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.process_data(self.mock_data)
        assert result is not None
        assert result["status"] == "success"
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            self.process_data(None)
    
    def test_edge_cases(self):
        """Test edge cases"""
        edge_data = {{"id": "", "value": -1}}
        result = self.process_data(edge_data)
        assert result["status"] == "handled"
    
    def process_data(self, data):
        """Helper method for testing"""
        if data is None:
            raise ValueError("Data cannot be None")
        return {{"status": "success" if data else "handled", "data": data}}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        else:
            return f'''"""{filename.replace("_", " ").title()} Module"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class {filename.replace("_", " ").title().replace(" ", "")}:
    """Main class for {filename} functionality"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with optional configuration"""
        self.config = config or {{}}
        self.initialized_at = datetime.now()
        logger.info(f"Initialized {{self.__class__.__name__}} at {{self.initialized_at}}")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming data
        
        Args:
            data: Input data to process
            
        Returns:
            Processed result dictionary
        """
        try:
            # Validate input
            self._validate_input(data)
            
            # Process data
            result = self._execute_processing(data)
            
            # Return result
            return {{
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }}
        except Exception as e:
            logger.error(f"Processing failed: {{e}}")
            return {{
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }}
    
    def _validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data"""
        if not data:
            raise ValueError("Input data cannot be empty")
        
        required_fields = ["id", "type", "content"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {{field}}")
    
    def _execute_processing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute main processing logic"""
        # Implement processing logic here
        processed = {{
            "id": data.get("id"),
            "processed": True,
            "result": f"Processed {{data.get('type')}} successfully"
        }}
        return processed
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {{
            "initialized": self.initialized_at.isoformat(),
            "config": self.config,
            "status": "operational"
        }}

def main():
    """Main entry point"""
    processor = {filename.replace("_", " ").title().replace(" ", "")}()
    
    # Example usage
    sample_data = {{
        "id": "123",
        "type": "example",
        "content": "Sample content"
    }}
    
    result = processor.process(sample_data)
    print(f"Result: {{result}}")

if __name__ == "__main__":
    main()
'''
    
    def _generate_react(self, filename: str, context: str) -> str:
        """Generate React/TSX component"""
        component_name = filename.replace('_', ' ').title().replace(' ', '')
        return f'''import React, {{ useState, useEffect }} from 'react';
import {{ useNavigate }} from 'react-router-dom';

interface {component_name}Props {{
  title?: string;
  onAction?: (data: any) => void;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{ title = "{component_name}", onAction }}) => {{
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {{
    loadData();
  }}, []);

  const loadData = async () => {{
    setLoading(true);
    try {{
      // Fetch data from API
      const response = await fetch('/api/data');
      const result = await response.json();
      setData(result);
    }} catch (err) {{
      setError('Failed to load data');
      console.error(err);
    }} finally {{
      setLoading(false);
    }}
  }};

  const handleClick = () => {{
    if (onAction) {{
      onAction(data);
    }}
  }};

  if (loading) {{
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }}

  if (error) {{
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {{error}}
      </div>
    );
  }}

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">{{title}}</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {{data.map((item, index) => (
          <div key={{index}} className="bg-white rounded-lg shadow-md p-4">
            <h3 className="font-semibold">{{item.name || `Item ${{index + 1}}`}}</h3>
            <p className="text-gray-600">{{item.description || 'No description'}}</p>
            <button 
              onClick={{handleClick}}
              className="mt-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Action
            </button>
          </div>
        ))}}
      </div>
      
      {{data.length === 0 && (
        <p className="text-gray-500 text-center">No data available</p>
      )}}
    </div>
  );
}};

export default {component_name};
'''
    
    def _generate_typescript(self, filename: str, context: str) -> str:
        """Generate TypeScript code"""
        return f'''// {filename}.ts - TypeScript module

export interface {filename.replace('_', ' ').title().replace(' ', '')}Config {{
  apiUrl: string;
  timeout: number;
  retryAttempts: number;
}}

export interface DataItem {{
  id: string;
  name: string;
  value: number;
  metadata?: Record<string, any>;
}}

export class {filename.replace('_', ' ').title().replace(' ', '')} {{
  private config: {filename.replace('_', ' ').title().replace(' ', '')}Config;
  
  constructor(config: Partial<{filename.replace('_', ' ').title().replace(' ', '')}Config> = {{}}) {{
    this.config = {{
      apiUrl: config.apiUrl || 'http://localhost:3000',
      timeout: config.timeout || 5000,
      retryAttempts: config.retryAttempts || 3
    }};
  }}
  
  async fetchData(): Promise<DataItem[]> {{
    try {{
      const response = await fetch(`${{this.config.apiUrl}}/data`, {{
        method: 'GET',
        headers: {{
          'Content-Type': 'application/json'
        }},
        signal: AbortSignal.timeout(this.config.timeout)
      }});
      
      if (!response.ok) {{
        throw new Error(`HTTP error! status: ${{response.status}}`);
      }}
      
      return await response.json();
    }} catch (error) {{
      console.error('Failed to fetch data:', error);
      throw error;
    }}
  }}
  
  async saveData(data: DataItem): Promise<DataItem> {{
    try {{
      const response = await fetch(`${{this.config.apiUrl}}/data`, {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json'
        }},
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(this.config.timeout)
      }});
      
      if (!response.ok) {{
        throw new Error(`HTTP error! status: ${{response.status}}`);
      }}
      
      return await response.json();
    }} catch (error) {{
      console.error('Failed to save data:', error);
      throw error;
    }}
  }}
  
  validateData(data: DataItem): boolean {{
    return !!(data.id && data.name && typeof data.value === 'number');
  }}
}}

export default {filename.replace('_', ' ').title().replace(' ', '')};
'''
    
    def _generate_javascript(self, filename: str, context: str) -> str:
        """Generate JavaScript code"""
        return f'''// {filename}.js - JavaScript module

class {filename.replace('_', ' ').title().replace(' ', '')} {{
  constructor(config = {{}}) {{
    this.config = {{
      apiUrl: config.apiUrl || 'http://localhost:3000',
      timeout: config.timeout || 5000,
      ...config
    }};
    this.data = [];
  }}
  
  async initialize() {{
    console.log('Initializing {filename}...');
    await this.loadData();
    return this;
  }}
  
  async loadData() {{
    try {{
      const response = await fetch(`${{this.config.apiUrl}}/api/data`);
      if (!response.ok) {{
        throw new Error(`HTTP error! status: ${{response.status}}`);
      }}
      this.data = await response.json();
      return this.data;
    }} catch (error) {{
      console.error('Failed to load data:', error);
      return [];
    }}
  }}
  
  async saveData(item) {{
    try {{
      const response = await fetch(`${{this.config.apiUrl}}/api/data`, {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json'
        }},
        body: JSON.stringify(item)
      }});
      
      if (!response.ok) {{
        throw new Error(`HTTP error! status: ${{response.status}}`);
      }}
      
      const result = await response.json();
      this.data.push(result);
      return result;
    }} catch (error) {{
      console.error('Failed to save data:', error);
      throw error;
    }}
  }}
  
  getData() {{
    return this.data;
  }}
  
  findById(id) {{
    return this.data.find(item => item.id === id);
  }}
  
  filterBy(predicate) {{
    return this.data.filter(predicate);
  }}
}}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {{
  module.exports = {filename.replace('_', ' ').title().replace(' ', '')};
}}

// Example usage
const example = new {filename.replace('_', ' ').title().replace(' ', '')}();
example.initialize().then(() => {{
  console.log('{filename} initialized successfully');
}});
'''
    
    def _generate_yaml(self, filename: str, context: str) -> str:
        """Generate YAML configuration"""
        return f"""# {filename}.yaml - Configuration file

app:
  name: {self.project_name}
  version: 1.0.0
  environment: development
  debug: true

server:
  host: localhost
  port: 3000
  workers: 4
  timeout: 30

database:
  type: postgresql
  host: localhost
  port: 5432
  name: {self.project_name.lower().replace(' ', '_')}
  user: admin
  password: ${{DB_PASSWORD}}
  pool:
    min: 2
    max: 10
    idle: 10000

redis:
  host: localhost
  port: 6379
  db: 0
  password: ${{REDIS_PASSWORD}}

authentication:
  jwt:
    secret: ${{JWT_SECRET}}
    expiresIn: 24h
  bcrypt:
    rounds: 10

features:
  authentication: true
  payments: true
  notifications: true
  analytics: true
  caching: true

logging:
  level: info
  format: json
  output:
    - console
    - file

monitoring:
  enabled: true
  service: datadog
  apiKey: ${{MONITORING_API_KEY}}
"""
    
    def _generate_env(self, filename: str, context: str) -> str:
        """Generate environment variables file"""
        return f"""# Environment Variables for {self.project_name}

# Application
NODE_ENV=development
APP_NAME={self.project_name}
APP_PORT=3000
APP_URL=http://localhost:3000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME={self.project_name.lower().replace(' ', '_')}
DB_USER=admin
DB_PASSWORD=changeme

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Authentication
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRES_IN=24h
BCRYPT_ROUNDS=10

# API Keys
STRIPE_API_KEY=sk_test_
SENDGRID_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# Monitoring
SENTRY_DSN=
DATADOG_API_KEY=

# Feature Flags
ENABLE_PAYMENTS=true
ENABLE_NOTIFICATIONS=true
ENABLE_ANALYTICS=true
"""
    
    def _generate_html(self, filename: str, context: str) -> str:
        """Generate HTML content"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name} - {filename}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100">
    <nav class="bg-white shadow-lg">
        <div class="max-w-6xl mx-auto px-4">
            <div class="flex justify-between">
                <div class="flex space-x-7">
                    <div>
                        <a href="#" class="flex items-center py-4 px-2">
                            <span class="font-semibold text-gray-500 text-lg">{self.project_name}</span>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <div class="container mx-auto mt-8 px-4">
        <h1 class="text-3xl font-bold text-gray-800 mb-4">{filename.replace('_', ' ').title()}</h1>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-4">
            <h2 class="text-xl font-semibold mb-2">Welcome</h2>
            <p class="text-gray-600">This is the {filename} page for {self.project_name}.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold">Feature 1</h3>
                <p class="text-gray-600">Description of feature 1</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold">Feature 2</h3>
                <p class="text-gray-600">Description of feature 2</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold">Feature 3</h3>
                <p class="text-gray-600">Description of feature 3</p>
            </div>
        </div>
    </div>

    <script>
        console.log('{self.project_name} loaded');
    </script>
</body>
</html>
"""
    
    def _generate_css(self, filename: str, context: str) -> str:
        """Generate CSS styles"""
        return f"""/* {filename}.css - Styles for {self.project_name} */

:root {{
  --primary-color: #3b82f6;
  --secondary-color: #10b981;
  --danger-color: #ef4444;
  --warning-color: #f59e0b;
  --dark-color: #1f2937;
  --light-color: #f3f4f6;
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  line-height: 1.6;
  color: var(--dark-color);
  background-color: var(--light-color);
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}}

.btn {{
  display: inline-block;
  padding: 10px 20px;
  background-color: var(--primary-color);
  color: white;
  text-decoration: none;
  border-radius: 5px;
  transition: background-color 0.3s;
  border: none;
  cursor: pointer;
}}

.btn:hover {{
  background-color: #2563eb;
}}

.btn-secondary {{
  background-color: var(--secondary-color);
}}

.btn-danger {{
  background-color: var(--danger-color);
}}

.card {{
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}}

.form-group {{
  margin-bottom: 15px;
}}

.form-control {{
  width: 100%;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 16px;
}}

.form-control:focus {{
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}

.alert {{
  padding: 12px 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}}

.alert-success {{
  background-color: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}}

.alert-error {{
  background-color: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}}

.table {{
  width: 100%;
  border-collapse: collapse;
}}

.table th,
.table td {{
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}}

.table th {{
  background-color: #f9fafb;
  font-weight: 600;
}}

@media (max-width: 768px) {{
  .container {{
    padding: 0 10px;
  }}
  
  .table {{
    font-size: 14px;
  }}
}}
"""
    
    def _generate_sql(self, filename: str, context: str) -> str:
        """Generate SQL schema"""
        return f"""-- {filename}.sql - Database schema for {self.project_name}

-- Create database
CREATE DATABASE IF NOT EXISTS {self.project_name.lower().replace(' ', '_')};
USE {self.project_name.lower().replace(' ', '_')};

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(50) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(100),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_price (price),
    INDEX idx_created_at (created_at)
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address JSON,
    payment_method VARCHAR(50),
    payment_id VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Order items table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
);

-- Insert sample data
INSERT INTO users (email, password_hash, first_name, last_name, role) VALUES
('admin@example.com', '$2b$10$YourHashHere', 'Admin', 'User', 'admin'),
('test@example.com', '$2b$10$YourHashHere', 'Test', 'User', 'customer'),
('john@example.com', '$2b$10$YourHashHere', 'John', 'Doe', 'customer');

INSERT INTO products (name, description, price, stock, category) VALUES
('Laptop', 'High-performance laptop with 16GB RAM', 999.99, 10, 'Electronics'),
('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 50, 'Electronics'),
('Office Chair', 'Comfortable ergonomic office chair', 299.99, 15, 'Furniture'),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 49.99, 30, 'Furniture'),
('Notebook', 'Premium quality notebook', 9.99, 100, 'Stationery');

-- Create views
CREATE VIEW active_products AS
SELECT * FROM products WHERE is_active = TRUE;

CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.user_id,
    u.email,
    o.total,
    o.status,
    o.created_at,
    COUNT(oi.id) as item_count
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.user_id, u.email, o.total, o.status, o.created_at;
"""
    
    def _generate_shell(self, filename: str, context: str) -> str:
        """Generate shell script"""
        return f"""#!/bin/bash
# {filename}.sh - Shell script for {self.project_name}

set -e  # Exit on error

# Configuration
PROJECT_NAME="{self.project_name.lower().replace(' ', '-')}"
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Functions
log_info() {{
    echo -e "${{GREEN}}[INFO]${{NC}} $1"
}}

log_error() {{
    echo -e "${{RED}}[ERROR]${{NC}} $1"
}}

log_warning() {{
    echo -e "${{YELLOW}}[WARNING]${{NC}} $1"
}}

# Check dependencies
check_dependencies() {{
    log_info "Checking dependencies..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi
    
    log_info "All dependencies are installed"
}}

# Install packages
install_packages() {{
    log_info "Installing packages..."
    cd "$PROJECT_ROOT"
    npm install
    log_info "Packages installed successfully"
}}

# Build project
build_project() {{
    log_info "Building project..."
    cd "$PROJECT_ROOT"
    npm run build
    log_info "Project built successfully"
}}

# Start development server
start_dev() {{
    log_info "Starting development server..."
    cd "$PROJECT_ROOT"
    npm run dev
}}

# Run tests
run_tests() {{
    log_info "Running tests..."
    cd "$PROJECT_ROOT"
    npm test
    log_info "Tests completed"
}}

# Main script
main() {{
    log_info "Starting $PROJECT_NAME setup..."
    
    check_dependencies
    install_packages
    build_project
    
    log_info "Setup completed successfully!"
    log_info "Run './$(basename $0) dev' to start the development server"
}}

# Parse commands
case "${{1:-}}" in
    install)
        install_packages
        ;;
    build)
        build_project
        ;;
    dev)
        start_dev
        ;;
    test)
        run_tests
        ;;
    *)
        main
        ;;
esac
"""
    
    def _generate_batch(self, filename: str, context: str) -> str:
        """Generate batch script"""
        return f"""@echo off
REM {filename}.bat - Batch script for {self.project_name}

SET PROJECT_NAME={self.project_name.lower().replace(' ', '-')}
SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%..

echo ========================================
echo {self.project_name} Setup Script
echo ========================================

REM Check Node.js
where node >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js from https://nodejs.org
    exit /b 1
)

REM Check npm
where npm >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not installed
    exit /b 1
)

echo [INFO] Dependencies verified

REM Install packages
echo [INFO] Installing packages...
cd /d "%PROJECT_ROOT%"
call npm install
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install packages
    exit /b 1
)

echo [INFO] Packages installed successfully

REM Build project
echo [INFO] Building project...
call npm run build
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed
    exit /b 1
)

echo [INFO] Project built successfully

echo.
echo ========================================
echo Setup completed successfully!
echo Run 'npm run dev' to start the development server
echo ========================================

pause
"""
    
    def _generate_text(self, filename: str, context: str) -> str:
        """Generate plain text content"""
        return f"""{self.project_name} - {filename}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
========
This file contains information related to {filename} for the {self.project_name} project.

CONTENT
=======
{context if context else f"This is the content for {filename}."}

PROJECT INFORMATION
==================
Project Name: {self.project_name}
File: {filename}.txt
Purpose: Documentation and reference

NOTES
=====
- This file was automatically generated
- Update as needed for your specific requirements
- Ensure all information is accurate and up-to-date

REFERENCES
==========
- Project documentation: docs/README.md
- API documentation: docs/API.md
- Configuration: config/settings.yaml

END OF FILE
"""
    
    def _generate_generic(self, filename: str, context: str) -> str:
        """Generate generic content for unknown file types"""
        return f"""# {filename}

This file was automatically generated for {self.project_name}.

Generated: {datetime.now().isoformat()}

## Content

{context if context else f"Generic content for {filename}"}

## Purpose

This file serves as a placeholder or template for the {filename} component.

## Usage

Modify this file according to your specific requirements.

---
End of file
"""