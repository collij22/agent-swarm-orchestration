#!/usr/bin/env python3
"""
Enhanced Mock Anthropic API Handler for Testing (Section 7 Implementation)

Provides realistic simulated API responses with actual file creation,
requirement tracking, and controlled failure simulation for robust testing.
"""

import json
import time
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import random
import shutil
import tempfile

@dataclass
class MockMessage:
    """Mock message response"""
    content: List[Any]
    id: str = None
    type: str = "message"
    role: str = "assistant"
    model: str = "claude-sonnet-4-20250514"
    stop_reason: str = "end_turn"
    stop_sequence: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = f"msg_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

@dataclass
class MockTextBlock:
    """Mock text content block"""
    text: str
    type: str = "text"

@dataclass
class MockToolUseBlock:
    """Mock tool use block"""
    id: str
    name: str
    input: Dict[str, Any]
    type: str = "tool_use"

@dataclass
class RequirementTracker:
    """Track requirement completion in mock mode"""
    total_requirements: int = 0
    completed_requirements: int = 0
    partial_requirements: int = 0
    failed_requirements: int = 0
    requirement_details: Dict[str, str] = field(default_factory=dict)
    
    def add_requirement(self, req_id: str, status: str = "pending"):
        """Add a requirement to track"""
        self.total_requirements += 1
        self.requirement_details[req_id] = status
    
    def complete_requirement(self, req_id: str):
        """Mark requirement as complete"""
        if req_id in self.requirement_details:
            self.requirement_details[req_id] = "completed"
            self.completed_requirements += 1
    
    def partial_requirement(self, req_id: str):
        """Mark requirement as partially complete"""
        if req_id in self.requirement_details:
            self.requirement_details[req_id] = "partial"
            self.partial_requirements += 1
    
    def fail_requirement(self, req_id: str, reason: str):
        """Mark requirement as failed"""
        if req_id in self.requirement_details:
            self.requirement_details[req_id] = f"failed: {reason}"
            self.failed_requirements += 1
    
    def get_completion_percentage(self) -> float:
        """Get overall completion percentage"""
        if self.total_requirements == 0:
            return 0.0
        return (self.completed_requirements / self.total_requirements) * 100
    
    def get_summary(self) -> Dict:
        """Get requirement tracking summary"""
        return {
            "total": self.total_requirements,
            "completed": self.completed_requirements,
            "partial": self.partial_requirements,
            "failed": self.failed_requirements,
            "percentage": round(self.get_completion_percentage(), 2),
            "details": self.requirement_details
        }

@dataclass
class FileSystemSimulator:
    """Simulate file system operations in mock mode"""
    base_path: Path = None
    created_files: List[str] = field(default_factory=list)
    created_directories: List[str] = field(default_factory=list)
    file_contents: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.base_path is None:
            # Create temporary directory for mock files
            self.base_path = Path(tempfile.mkdtemp(prefix="mock_agent_"))
    
    def write_file(self, file_path: str, content: str) -> bool:
        """Simulate file writing"""
        try:
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Actually write the file for realistic testing
            full_path.write_text(content, encoding='utf-8')
            
            # Track the operation
            self.created_files.append(file_path)
            self.file_contents[file_path] = content
            
            if str(full_path.parent) not in self.created_directories:
                self.created_directories.append(str(full_path.parent.relative_to(self.base_path)))
            
            return True
        except Exception as e:
            print(f"Mock file write failed: {e}")
            return False
    
    def read_file(self, file_path: str) -> Optional[str]:
        """Simulate file reading"""
        full_path = self.base_path / file_path
        if full_path.exists():
            return full_path.read_text(encoding='utf-8')
        return self.file_contents.get(file_path)
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in simulation"""
        full_path = self.base_path / file_path
        return full_path.exists() or file_path in self.created_files
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.base_path and self.base_path.exists():
            shutil.rmtree(self.base_path)
    
    def get_summary(self) -> Dict:
        """Get file system operation summary"""
        return {
            "base_path": str(self.base_path),
            "files_created": len(self.created_files),
            "directories_created": len(self.created_directories),
            "total_size": sum(len(c) for c in self.file_contents.values()),
            "file_list": self.created_files[:20]  # First 20 files
        }

class EnhancedMockAnthropicClient:
    """Enhanced Mock Anthropic client with realistic execution and validation"""
    
    def __init__(self, 
                 record_mode: bool = False,
                 replay_file: Optional[str] = None,
                 deterministic: bool = True,
                 enable_file_creation: bool = True,
                 failure_rate: float = 0.0,
                 progress_tracking: bool = True):
        """
        Args:
            record_mode: If True, records real API calls to file
            replay_file: Path to file with recorded responses to replay
            deterministic: If True, returns predictable responses
            enable_file_creation: If True, actually creates files in temp directory
            failure_rate: Probability of simulating failures (0.0 to 1.0)
            progress_tracking: If True, tracks and reports progress
        """
        self.record_mode = record_mode
        self.replay_file = replay_file
        self.deterministic = deterministic
        self.enable_file_creation = enable_file_creation
        self.failure_rate = failure_rate
        self.progress_tracking = progress_tracking
        
        self.call_count = 0
        self.recorded_calls = []
        self.replay_data = []
        
        # Enhanced tracking
        self.requirement_tracker = RequirementTracker()
        self.file_system = FileSystemSimulator() if enable_file_creation else None
        self.progress_steps = []
        self.simulated_failures = []
        
        if replay_file and Path(replay_file).exists():
            with open(replay_file, 'r') as f:
                self.replay_data = json.load(f)
        
        # Enhanced agent behaviors with realistic patterns
        self.agent_responses = {
            "project-architect": self._enhanced_architect_response,
            "requirements-analyst": self._enhanced_requirements_response,
            "rapid-builder": self._enhanced_builder_response,
            "quality-guardian": self._enhanced_quality_response,
            "ai-specialist": self._enhanced_ai_response,
            "devops-engineer": self._enhanced_devops_response,
            "frontend-specialist": self._enhanced_frontend_response,
            "database-expert": self._enhanced_database_response
        }
        
        # Track costs
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.estimated_cost = 0.0
        
        # Tool execution counts
        self.tool_executions = {}
    
    @property
    def messages(self):
        """Mock messages API"""
        return self
    
    def create(self, **kwargs) -> MockMessage:
        """Enhanced mock message creation with realistic behavior"""
        self.call_count += 1
        
        # Track progress
        if self.progress_tracking:
            self.progress_steps.append({
                "call": self.call_count,
                "timestamp": datetime.now().isoformat(),
                "model": kwargs.get('model', 'claude-sonnet-4-20250514')
            })
        
        # Extract parameters
        model = kwargs.get('model', 'claude-sonnet-4-20250514')
        messages = kwargs.get('messages', [])
        tools = kwargs.get('tools', [])
        max_tokens = kwargs.get('max_tokens', 4096)
        
        # Simulate random failures if configured
        if self.failure_rate > 0 and random.random() < self.failure_rate:
            return self._simulate_failure(messages)
        
        # If replaying, return recorded response
        if self.replay_data and self.call_count <= len(self.replay_data):
            response_data = self.replay_data[self.call_count - 1]
            return self._reconstruct_response(response_data)
        
        # Generate enhanced mock response based on context
        agent_name = self._detect_agent(messages)
        # Enhanced agent detection based on prompt content
        if messages:
            content = messages[0].get('content', '')
            # Check if the content contains agent prompts we can match
            if 'analyze project requirements' in str(content).lower():
                agent_name = "requirements-analyst"
            elif 'create architecture documentation' in str(content).lower():
                agent_name = "project-architect"
        response = self._generate_enhanced_response(agent_name, messages, tools)
        
        # Track usage
        self._track_usage(messages, response)
        
        # Record if in record mode
        if self.record_mode:
            self.recorded_calls.append({
                'request': kwargs,
                'response': self._serialize_response(response),
                'timestamp': datetime.now().isoformat()
            })
        
        return response
    
    def _detect_agent(self, messages: List[Dict]) -> str:
        """Enhanced agent detection with more patterns"""
        if not messages:
            return "unknown"
        
        first_message = messages[0].get('content', '')
        if isinstance(first_message, list):
            first_message = str(first_message)
        
        content_lower = first_message.lower()
        
        # Enhanced pattern matching
        patterns = {
            "project-architect": ["architect", "design", "system", "architecture"],
            "rapid-builder": ["rapid", "builder", "scaffold", "implement", "create"],
            "quality-guardian": ["quality", "test", "security", "audit", "validate"],
            "ai-specialist": ["ai", "ml", "llm", "openai", "anthropic", "categorization"],
            "devops-engineer": ["devops", "deploy", "docker", "ci/cd", "pipeline"],
            "frontend-specialist": ["frontend", "react", "ui", "component", "tailwind"],
            "database-expert": ["database", "schema", "sql", "migration", "query"],
            "requirements-analyst": ["requirements", "analyze", "scope", "features"]
        }
        
        for agent, keywords in patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                return agent
        
        return "unknown"
    
    def _generate_enhanced_response(self, agent_name: str, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Generate enhanced realistic response for agent"""
        
        # Check if this is a tool response
        if messages and isinstance(messages[-1].get('content'), list):
            last_content = messages[-1]['content']
            if last_content and isinstance(last_content[0], dict) and last_content[0].get('type') == 'tool_result':
                # Process tool result and decide next action
                tool_result = last_content[0].get('content', '')
                
                # Simulate requirement completion based on tool result
                if "successfully" in tool_result.lower():
                    if self.requirement_tracker.total_requirements > 0:
                        req_id = f"req_{self.call_count}"
                        self.requirement_tracker.complete_requirement(req_id)
                
                # Decide if more tools needed or complete
                if self.call_count < 5 and tools:  # Continue with more tools
                    return self._continue_with_tools(agent_name, tools)
                else:
                    return self._complete_agent_task(agent_name)
        
        # Get agent-specific enhanced response
        if agent_name in self.agent_responses:
            return self.agent_responses[agent_name](messages, tools)
        
        # Default enhanced response
        return self._enhanced_default_response(messages, tools)
    
    def _enhanced_architect_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced mock response for project architect with realistic patterns"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        # Track requirements
        if self.requirement_tracker.total_requirements == 0:
            for i in range(5):  # Simulate 5 requirements
                self.requirement_tracker.add_requirement(f"arch_req_{i}")
        
        # Realistic tool execution with file creation
        if 'write_file' in tool_names:
            # Actually create architecture documentation
            content = """# System Architecture

## Overview
Microservices architecture with the following components:

### Services
1. **API Gateway** - Entry point for all client requests
2. **Auth Service** - JWT-based authentication
3. **User Service** - User management and profiles
4. **Data Service** - Core business logic

### Technology Stack
- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI (Python 3.11)
- Database: PostgreSQL 15
- Cache: Redis 7
- Message Queue: RabbitMQ

### Deployment
- Docker containers
- Kubernetes orchestration
- AWS/GCP cloud platform
"""
            
            if self.file_system:
                self.file_system.write_file("docs/architecture.md", content)
            
            self.requirement_tracker.complete_requirement("arch_req_0")
            
            return MockMessage(content=[
                MockTextBlock(text="I've analyzed the requirements and will now document the system architecture."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Creating comprehensive architecture documentation",
                        "file_path": "docs/architecture.md",
                        "content": content
                    }
                )
            ])
        
        # Default architect behavior
        return MockMessage(content=[
            MockTextBlock(text="I'll design a scalable microservices architecture for this project.")
        ])
    
    def _enhanced_requirements_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced requirements analyst with requirement tracking"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        # Track requirements based on project features
        if self.requirement_tracker.total_requirements == 0:
            # Add requirements based on features in the project
            base_requirements = ["auth", "api", "frontend", "database", "deployment"]
            for i, req in enumerate(base_requirements):
                self.requirement_tracker.add_requirement(f"req_{i}_{req}")
        
        if 'write_file' in tool_names:
            # Create requirements analysis document
            content = """# Requirements Analysis

## Project Requirements
1. Authentication System - JWT-based user authentication
2. API Development - RESTful APIs with proper validation
3. Frontend Interface - React-based user interface
4. Database Integration - PostgreSQL with proper schemas
5. Deployment Strategy - Docker containerization

## Technical Stack
- Backend: FastAPI (Python 3.11)
- Frontend: React + TypeScript
- Database: PostgreSQL
- Authentication: JWT tokens
- Deployment: Docker + Kubernetes

## Implementation Priority
1. High: Authentication and API foundation
2. Medium: Frontend interface and database setup
3. Low: Advanced features and optimization
"""
            
            if self.file_system:
                self.file_system.write_file("docs/requirements.md", content)
            
            # Complete first requirement
            self.requirement_tracker.complete_requirement("req_0_auth")
            
            return MockMessage(content=[
                MockTextBlock(text="Analyzing project requirements and creating documentation."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Creating comprehensive requirements analysis documentation",
                        "file_path": "docs/requirements.md",
                        "content": content
                    }
                )
            ])
        
        # Default requirements behavior
        return MockMessage(content=[
            MockTextBlock(text="Requirements analysis complete. Ready to proceed with implementation.")
        ])
    
    def _enhanced_builder_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced rapid builder with actual file creation"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        if 'write_file' in tool_names and self.call_count <= 3:
            # Create actual project files
            files_to_create = [
                ("backend/main.py", self._generate_fastapi_main()),
                ("backend/models.py", self._generate_models()),
                ("backend/requirements.txt", self._generate_requirements())
            ]
            
            if self.call_count <= len(files_to_create):
                file_path, content = files_to_create[self.call_count - 1]
                
                if self.file_system:
                    self.file_system.write_file(file_path, content)
                
                self.requirement_tracker.complete_requirement(f"build_req_{self.call_count}")
                
                return MockMessage(content=[
                    MockTextBlock(text=f"Creating {file_path} for the application."),
                    MockToolUseBlock(
                        id=f"tool_{self.call_count}",
                        name="write_file",
                        input={
                            "reasoning": f"Implementing core application file: {file_path}",
                            "file_path": file_path,
                            "content": content
                        }
                    )
                ])
        
        return MockMessage(content=[
            MockTextBlock(text="Rapid prototyping completed. Core application structure is ready.")
        ])
    
    def _enhanced_quality_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced quality guardian with validation tracking"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        # Simulate validation with mixed results
        if 'validate_requirements' in tool_names:
            # Track some partial completions
            self.requirement_tracker.partial_requirement("arch_req_1")
            self.requirement_tracker.partial_requirement("build_req_2")
            
            validation_report = {
                "total_requirements": 10,
                "completed": 7,
                "partial": 2,
                "missing": 1,
                "percentage": 70.0,
                "issues": [
                    "Missing error handling in auth service",
                    "No rate limiting configured"
                ]
            }
            
            return MockMessage(content=[
                MockTextBlock(text="Running comprehensive quality validation."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="validate_requirements",
                    input={
                        "reasoning": "Validating all project requirements and deliverables",
                        "validation_report": validation_report
                    }
                )
            ])
        
        if 'write_file' in tool_names and self.file_system:
            # Create test files
            test_content = """import pytest
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_user_creation():
    user_data = {"username": "testuser", "email": "test@example.com"}
    response = client.post("/users", json=user_data)
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
"""
            self.file_system.write_file("tests/test_api.py", test_content)
            
            return MockMessage(content=[
                MockTextBlock(text="Creating comprehensive test suite."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Implementing test coverage for critical endpoints",
                        "file_path": "tests/test_api.py",
                        "content": test_content
                    }
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="Quality validation complete. 90% test coverage achieved.")
        ])
    
    def _enhanced_ai_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced AI specialist with OpenAI integration patterns"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        if 'write_file' in tool_names and self.file_system:
            ai_client = """import openai
from typing import List, Dict
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class AIClient:
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def categorize_task(self, task: str) -> Dict:
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Categorize the following task."},
                {"role": "user", "content": task}
            ]
        )
        return {"category": response.choices[0].message.content}
"""
            self.file_system.write_file("backend/ai_client.py", ai_client)
            self.requirement_tracker.complete_requirement("ai_req_0")
            
            return MockMessage(content=[
                MockTextBlock(text="Implementing AI integration with OpenAI."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Creating AI client with retry logic and error handling",
                        "file_path": "backend/ai_client.py",
                        "content": ai_client
                    }
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="AI integration complete with GPT-4 and fallback mechanisms.")
        ])
    
    def _enhanced_devops_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced DevOps engineer with Docker and CI/CD"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        if 'write_file' in tool_names and self.file_system:
            dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
            docker_compose = """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/appdb
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  cache:
    image: redis:7-alpine

volumes:
  postgres_data:
"""
            
            if self.call_count == 1:
                self.file_system.write_file("backend/Dockerfile", dockerfile)
                file_created = ("backend/Dockerfile", dockerfile)
            else:
                self.file_system.write_file("docker-compose.yml", docker_compose)
                file_created = ("docker-compose.yml", docker_compose)
            
            self.requirement_tracker.complete_requirement(f"devops_req_{self.call_count}")
            
            return MockMessage(content=[
                MockTextBlock(text=f"Creating {file_created[0]} for containerization."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Setting up Docker configuration for deployment",
                        "file_path": file_created[0],
                        "content": file_created[1]
                    }
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="DevOps setup complete with Docker and CI/CD pipeline.")
        ])
    
    def _enhanced_frontend_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced frontend specialist with React components"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        if 'write_file' in tool_names and self.file_system:
            app_component = """import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
"""
            self.file_system.write_file("frontend/src/App.tsx", app_component)
            self.requirement_tracker.complete_requirement("frontend_req_0")
            
            return MockMessage(content=[
                MockTextBlock(text="Creating React application structure."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Setting up React with TypeScript and routing",
                        "file_path": "frontend/src/App.tsx",
                        "content": app_component
                    }
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="Frontend scaffolding complete with React + TypeScript.")
        ])
    
    def _enhanced_database_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced database expert with schema design"""
        tool_names = [t['name'] for t in tools] if tools else []
        
        if 'write_file' in tool_names and self.file_system:
            schema = """-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
"""
            self.file_system.write_file("database/schema.sql", schema)
            self.requirement_tracker.complete_requirement("db_req_0")
            
            return MockMessage(content=[
                MockTextBlock(text="Designing optimized database schema."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="write_file",
                    input={
                        "reasoning": "Creating normalized database schema with indexes",
                        "file_path": "database/schema.sql",
                        "content": schema
                    }
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="Database schema designed with proper indexing and constraints.")
        ])
    
    def _enhanced_requirements_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced requirements analyst with detailed tracking"""
        # Initialize requirements
        requirements = [
            "User authentication and authorization",
            "RESTful API endpoints",
            "Database persistence",
            "Frontend UI with React",
            "Docker containerization"
        ]
        
        for i, req in enumerate(requirements):
            self.requirement_tracker.add_requirement(f"req_{i}")
        
        return MockMessage(content=[
            MockTextBlock(text=f"Analyzed {len(requirements)} requirements. Ready for implementation.")
        ])
    
    def _enhanced_default_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Enhanced default response with realistic patterns"""
        if tools:
            tool = tools[0] if self.deterministic else random.choice(tools)
            
            # Track tool execution
            tool_name = tool['name']
            self.tool_executions[tool_name] = self.tool_executions.get(tool_name, 0) + 1
            
            # Execute tool with realistic parameters
            if tool_name == 'write_file' and self.file_system:
                file_path = f"output/file_{self.call_count}.txt"
                content = f"Generated content for call {self.call_count}"
                self.file_system.write_file(file_path, content)
                
                return MockMessage(content=[
                    MockTextBlock(text=f"Executing {tool_name} tool."),
                    MockToolUseBlock(
                        id=f"tool_{self.call_count}",
                        name=tool_name,
                        input={
                            "reasoning": "Processing task with appropriate tool",
                            "file_path": file_path,
                            "content": content
                        }
                    )
                ])
            
            return MockMessage(content=[
                MockTextBlock(text=f"Using {tool_name} to complete the task."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name=tool_name,
                    input={"reasoning": "Executing required task"}
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="Task processed successfully.")
        ])
    
    def _continue_with_tools(self, agent_name: str, tools: List[Dict]) -> MockMessage:
        """Continue execution with more tools"""
        if tools:
            tool = tools[0]
            tool_name = tool['name']
            
            # Provide proper parameters based on tool type
            if tool_name == "write_file":
                tool_input = {
                    "reasoning": "Continuing task execution",
                    "file_path": f"output/{agent_name}_output.txt",
                    "content": f"Output from {agent_name} task execution."
                }
            elif tool_name == "record_decision":
                tool_input = {
                    "reasoning": "Continuing task execution",
                    "decision": f"Continue with {agent_name} execution",
                    "rationale": "Task requires completion"
                }
            else:
                tool_input = {"reasoning": "Continuing task execution"}
                
            return MockMessage(content=[
                MockTextBlock(text=f"Continuing {agent_name} execution."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name=tool_name,
                    input=tool_input
                )
            ])
        return self._complete_agent_task(agent_name)
    
    def _complete_agent_task(self, agent_name: str) -> MockMessage:
        """Complete agent task with summary"""
        completion_messages = {
            "project-architect": "Architecture design complete with all components documented.",
            "rapid-builder": "Application scaffolding complete with core functionality.",
            "quality-guardian": f"Quality validation complete. {self.requirement_tracker.get_completion_percentage():.1f}% requirements met.",
            "ai-specialist": "AI integration complete with OpenAI and fallback mechanisms.",
            "devops-engineer": "DevOps pipeline configured with Docker and CI/CD.",
            "frontend-specialist": "Frontend application ready with React and TypeScript.",
            "database-expert": "Database schema optimized with proper indexing.",
            "requirements-analyst": f"Requirements analysis complete. {self.requirement_tracker.total_requirements} requirements identified."
        }
        
        message = completion_messages.get(agent_name, f"{agent_name} task completed successfully.")
        
        return MockMessage(content=[
            MockTextBlock(text=message)
        ])
    
    def _simulate_failure(self, messages: List[Dict]) -> MockMessage:
        """Simulate realistic agent failures for testing"""
        failure_scenarios = [
            "API rate limit exceeded. Please retry after 60 seconds.",
            "Database connection failed: Connection refused.",
            "File write permission denied: /protected/path",
            "Network timeout: Unable to reach external service.",
            "Validation error: Missing required configuration.",
            "Memory limit exceeded: Process requires more than 512MB."
        ]
        
        failure_message = random.choice(failure_scenarios)
        
        self.simulated_failures.append({
            "call": self.call_count,
            "message": failure_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Track as failed requirement
        if self.requirement_tracker.total_requirements > 0:
            req_id = f"req_fail_{self.call_count}"
            self.requirement_tracker.fail_requirement(req_id, failure_message)
        
        return MockMessage(content=[
            MockTextBlock(text=f"Error: {failure_message}")
        ])
    
    def _generate_fastapi_main(self) -> str:
        """Generate realistic FastAPI main file"""
        return """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Task Manager API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Task(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: int = 0

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    # Task creation logic here
    return task

@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    # Task retrieval logic here
    return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    def _generate_models(self) -> str:
        """Generate realistic data models"""
        return """from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String)
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="tasks")
"""
    
    def _generate_requirements(self) -> str:
        """Generate realistic requirements.txt"""
        return """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
redis==5.0.1
celery==5.3.4
tenacity==8.2.3
openai==1.3.5
"""
    
    def _track_usage(self, messages: List[Dict], response: MockMessage):
        """Enhanced usage tracking with progress indicators"""
        # Original tracking
        input_chars = sum(len(str(m)) for m in messages)
        output_chars = sum(len(str(block)) for block in response.content)
        
        input_tokens = input_chars // 4
        output_tokens = output_chars // 4
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Cost calculation
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        self.estimated_cost += input_cost + output_cost
        
        # Progress tracking
        if self.progress_tracking:
            progress = {
                "call": self.call_count,
                "tokens_used": input_tokens + output_tokens,
                "cost_incurred": round(input_cost + output_cost, 4),
                "completion": self.requirement_tracker.get_completion_percentage()
            }
            self.progress_steps.append(progress)
    
    def _serialize_response(self, response: MockMessage) -> Dict:
        """Serialize response for recording"""
        return {
            'content': [
                {'text': block.text, 'type': 'text'} if hasattr(block, 'text')
                else {'id': block.id, 'name': block.name, 'input': block.input, 'type': 'tool_use'}
                for block in response.content
            ],
            'id': response.id,
            'model': response.model
        }
    
    def _reconstruct_response(self, data: Dict) -> MockMessage:
        """Reconstruct response from recorded data"""
        content = []
        for block in data['content']:
            if block['type'] == 'text':
                content.append(MockTextBlock(text=block['text']))
            elif block['type'] == 'tool_use':
                content.append(MockToolUseBlock(
                    id=block['id'],
                    name=block['name'],
                    input=block['input']
                ))
        
        return MockMessage(
            content=content,
            id=data.get('id'),
            model=data.get('model', 'claude-sonnet-4-20250514')
        )
    
    def save_recordings(self, filepath: str):
        """Save recorded API calls to file"""
        if self.recorded_calls:
            with open(filepath, 'w') as f:
                json.dump(self.recorded_calls, f, indent=2)
            print(f"Saved {len(self.recorded_calls)} recorded calls to {filepath}")
    
    def get_usage_summary(self) -> Dict:
        """Get enhanced usage and cost summary"""
        base_summary = {
            'total_calls': self.call_count,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'estimated_cost': round(self.estimated_cost, 4),
            'average_input_tokens': self.total_input_tokens // max(1, self.call_count),
            'average_output_tokens': self.total_output_tokens // max(1, self.call_count)
        }
        
        # Add enhanced tracking
        if self.requirement_tracker:
            base_summary['requirements'] = self.requirement_tracker.get_summary()
        
        if self.file_system:
            base_summary['file_system'] = self.file_system.get_summary()
        
        if self.progress_tracking and self.progress_steps:
            base_summary['progress'] = {
                'total_steps': len(self.progress_steps),
                'completion_percentage': self.requirement_tracker.get_completion_percentage(),
                'last_step': self.progress_steps[-1] if self.progress_steps else None
            }
        
        if self.simulated_failures:
            base_summary['failures'] = {
                'count': len(self.simulated_failures),
                'rate': len(self.simulated_failures) / max(1, self.call_count),
                'last_failure': self.simulated_failures[-1] if self.simulated_failures else None
            }
        
        if self.tool_executions:
            base_summary['tool_usage'] = self.tool_executions
        
        return base_summary
    
    def cleanup(self):
        """Clean up resources"""
        if self.file_system:
            self.file_system.cleanup()

# Enhanced monkey-patch function for testing
def use_enhanced_mock_client(enable_file_creation=True, failure_rate=0.0):
    """Replace real Anthropic client with enhanced mock in agent_runtime"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Import and patch
    import lib.agent_runtime as runtime
    original_init = runtime.AnthropicAgentRunner.__init__
    
    def mock_init(self, api_key=None, logger=None):
        # Initialize all attributes first (matching real agent_runtime.py)
        self.logger = logger or runtime.get_logger()
        self.tools = {}
        self.max_retries = 5
        self.retry_delay = 2
        
        # Rate limiting
        self.api_calls_per_minute = []
        self.max_calls_per_minute = 20
        
        # Inter-agent delays
        self.min_delay_between_agents = 3
        
        # Set up enhanced mock API client
        self.api_key = "mock-key"
        self.client = EnhancedMockAnthropicClient(
            enable_file_creation=enable_file_creation,
            failure_rate=failure_rate,
            progress_tracking=True
        )
    
    runtime.AnthropicAgentRunner.__init__ = mock_init
    return original_init

def restore_real_client(original_init):
    """Restore real Anthropic client"""
    import lib.agent_runtime as runtime
    runtime.AnthropicAgentRunner.__init__ = original_init

if __name__ == "__main__":
    # Demo the enhanced mock client
    print("=" * 60)
    print("Enhanced Mock Anthropic Client Demo")
    print("=" * 60)
    
    # Create enhanced client with file creation
    client = EnhancedMockAnthropicClient(
        enable_file_creation=True,
        failure_rate=0.1,  # 10% failure rate
        progress_tracking=True
    )
    
    # Simulate architect agent
    print("\n1. Testing Project Architect:")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "You are a project architect. Design a system."}],
        tools=[
            {"name": "write_file", "description": "Write file"},
            {"name": "analyze_requirements", "description": "Analyze requirements"}
        ]
    )
    
    for block in response.content:
        if hasattr(block, 'text'):
            print(f"   Text: {block.text}")
        elif hasattr(block, 'name'):
            print(f"   Tool: {block.name}")
    
    # Simulate builder agent
    print("\n2. Testing Rapid Builder:")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "You are a rapid builder. Create the application."}],
        tools=[{"name": "write_file", "description": "Write file"}]
    )
    
    for block in response.content:
        if hasattr(block, 'text'):
            print(f"   Text: {block.text}")
        elif hasattr(block, 'name'):
            print(f"   Tool: {block.name}")
    
    # Get comprehensive summary
    print("\n3. Usage and Progress Summary:")
    summary = client.get_usage_summary()
    
    print(f"\nAPI Calls: {summary['total_calls']}")
    print(f"Estimated Cost: ${summary['estimated_cost']}")
    
    if 'requirements' in summary:
        req_summary = summary['requirements']
        print(f"\nRequirements Tracking:")
        print(f"   Total: {req_summary['total']}")
        print(f"   Completed: {req_summary['completed']}")
        print(f"   Partial: {req_summary['partial']}")
        print(f"   Failed: {req_summary['failed']}")
        print(f"   Completion: {req_summary['percentage']}%")
    
    if 'file_system' in summary:
        fs_summary = summary['file_system']
        print(f"\nFile System Operations:")
        print(f"   Files Created: {fs_summary['files_created']}")
        print(f"   Directories: {fs_summary['directories_created']}")
        print(f"   Total Size: {fs_summary['total_size']} bytes")
        if fs_summary['file_list']:
            print(f"   Sample Files: {fs_summary['file_list'][:3]}")
    
    if 'progress' in summary:
        prog_summary = summary['progress']
        print(f"\nProgress Tracking:")
        print(f"   Steps Completed: {prog_summary['total_steps']}")
        print(f"   Overall Completion: {prog_summary['completion_percentage']}%")
    
    if 'failures' in summary:
        fail_summary = summary['failures']
        print(f"\nFailure Simulation:")
        print(f"   Failures: {fail_summary['count']}")
        print(f"   Failure Rate: {fail_summary['rate']:.1%}")
    
    # Cleanup
    print("\n4. Cleaning up temporary files...")
    client.cleanup()
    print("   Cleanup complete!")
    
    print("\n" + "=" * 60)
    print("Enhanced Mock Mode Features Demonstrated:")
    print("- Realistic file creation in temp directory")
    print("- Requirement completion tracking")
    print("- Progress indicators with percentage")
    print("- Controlled failure simulation")
    print("- Comprehensive usage metrics")
    print("=" * 60)