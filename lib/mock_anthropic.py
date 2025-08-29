#!/usr/bin/env python3
"""
Mock Anthropic API Handler for Testing

Provides simulated API responses for testing agents without incurring costs.
Supports recording real API calls for replay and creating deterministic tests.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import random

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

class MockAnthropicClient:
    """Mock Anthropic client for testing"""
    
    def __init__(self, 
                 record_mode: bool = False,
                 replay_file: Optional[str] = None,
                 deterministic: bool = True):
        """
        Args:
            record_mode: If True, records real API calls to file
            replay_file: Path to file with recorded responses to replay
            deterministic: If True, returns predictable responses
        """
        self.record_mode = record_mode
        self.replay_file = replay_file
        self.deterministic = deterministic
        self.call_count = 0
        self.recorded_calls = []
        self.replay_data = []
        
        if replay_file and Path(replay_file).exists():
            with open(replay_file, 'r') as f:
                self.replay_data = json.load(f)
        
        # Simulated agent behaviors
        self.agent_responses = {
            "project-architect": self._architect_response,
            "rapid-builder": self._builder_response,
            "quality-guardian": self._quality_response,
            "ai-specialist": self._ai_response,
            "devops-engineer": self._devops_response
        }
        
        # Track costs
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.estimated_cost = 0.0
    
    @property
    def messages(self):
        """Mock messages API"""
        return self
    
    def create(self, **kwargs) -> MockMessage:
        """Mock message creation"""
        self.call_count += 1
        
        # Extract parameters
        model = kwargs.get('model', 'claude-sonnet-4-20250514')
        messages = kwargs.get('messages', [])
        tools = kwargs.get('tools', [])
        max_tokens = kwargs.get('max_tokens', 4096)
        
        # If replaying, return recorded response
        if self.replay_data and self.call_count <= len(self.replay_data):
            response_data = self.replay_data[self.call_count - 1]
            return self._reconstruct_response(response_data)
        
        # Generate mock response based on context
        agent_name = self._detect_agent(messages)
        response = self._generate_response(agent_name, messages, tools)
        
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
        """Detect which agent is being simulated based on messages"""
        if not messages:
            return "unknown"
        
        first_message = messages[0].get('content', '')
        
        # Simple pattern matching
        if 'architect' in first_message.lower():
            return "project-architect"
        elif 'rapid' in first_message.lower() or 'builder' in first_message.lower():
            return "rapid-builder"
        elif 'quality' in first_message.lower() or 'test' in first_message.lower():
            return "quality-guardian"
        elif 'ai' in first_message.lower() or 'ml' in first_message.lower():
            return "ai-specialist"
        elif 'devops' in first_message.lower() or 'deploy' in first_message.lower():
            return "devops-engineer"
        
        return "unknown"
    
    def _generate_response(self, agent_name: str, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Generate appropriate mock response for agent"""
        
        # Check if this is a tool response
        if messages and isinstance(messages[-1].get('content'), list):
            last_content = messages[-1]['content']
            if last_content and last_content[0].get('type') == 'tool_result':
                # Agent should continue or complete
                return MockMessage(content=[
                    MockTextBlock(text="Task completed successfully. All requirements have been addressed.")
                ])
        
        # Get agent-specific response
        if agent_name in self.agent_responses:
            return self.agent_responses[agent_name](messages, tools)
        
        # Default response
        return self._default_response(messages, tools)
    
    def _architect_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Mock response for project architect"""
        tool_names = [t['name'] for t in tools]
        
        if 'analyze_requirements' in tool_names and self.call_count == 1:
            return MockMessage(content=[
                MockTextBlock(text="Let me analyze the project requirements first."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="analyze_requirements",
                    input={
                        "reasoning": "Need to understand project scope and constraints",
                        "requirements_summary": "Web application with user authentication and data management",
                        "clarifications_needed": ["Budget constraints", "Timeline"]
                    }
                )
            ])
        elif 'design_architecture' in tool_names:
            return MockMessage(content=[
                MockTextBlock(text="Now I'll design the system architecture."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="design_architecture",
                    input={
                        "reasoning": "Creating scalable microservices architecture",
                        "components": ["API Gateway", "Auth Service", "Data Service", "Frontend"],
                        "data_flow": "Client -> Gateway -> Services -> Database",
                        "technology_stack": {
                            "frontend": "React + TypeScript",
                            "backend": "FastAPI",
                            "database": "PostgreSQL"
                        }
                    }
                )
            ])
        
        return self._default_response(messages, tools)
    
    def _builder_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Mock response for rapid builder"""
        tool_names = [t['name'] for t in tools]
        
        if 'create_scaffold' in tool_names and self.call_count == 1:
            return MockMessage(content=[
                MockTextBlock(text="I'll create the project scaffold structure."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="create_scaffold",
                    input={
                        "reasoning": "Setting up standard project structure",
                        "project_type": "web_app",
                        "structure": ["frontend/", "backend/", "database/", "tests/"]
                    }
                )
            ])
        
        return self._default_response(messages, tools)
    
    def _quality_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Mock response for quality guardian"""
        tool_names = [t['name'] for t in tools]
        
        if 'create_tests' in tool_names:
            return MockMessage(content=[
                MockTextBlock(text="I'll create comprehensive test suites."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name="create_tests",
                    input={
                        "reasoning": "Ensuring code quality with comprehensive testing",
                        "test_types": ["unit", "integration", "e2e"],
                        "coverage_target": 90
                    }
                )
            ])
        
        return self._default_response(messages, tools)
    
    def _ai_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Mock response for AI specialist"""
        return MockMessage(content=[
            MockTextBlock(text="I'll integrate AI capabilities into the system using modern LLM APIs and best practices.")
        ])
    
    def _devops_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Mock response for DevOps engineer"""
        return MockMessage(content=[
            MockTextBlock(text="I'll set up the CI/CD pipeline and deployment infrastructure.")
        ])
    
    def _default_response(self, messages: List[Dict], tools: List[Dict]) -> MockMessage:
        """Default mock response"""
        if tools:
            # Pick a random tool to demonstrate
            tool = tools[0] if self.deterministic else random.choice(tools)
            return MockMessage(content=[
                MockTextBlock(text=f"I'll use the {tool['name']} tool to proceed."),
                MockToolUseBlock(
                    id=f"tool_{self.call_count}",
                    name=tool['name'],
                    input={"reasoning": "Executing required task"}
                )
            ])
        
        return MockMessage(content=[
            MockTextBlock(text="Task has been processed successfully.")
        ])
    
    def _track_usage(self, messages: List[Dict], response: MockMessage):
        """Track token usage and costs"""
        # Rough estimation: 4 chars = 1 token
        input_chars = sum(len(str(m)) for m in messages)
        output_chars = sum(len(str(block)) for block in response.content)
        
        input_tokens = input_chars // 4
        output_tokens = output_chars // 4
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Cost calculation (using Sonnet pricing as default)
        input_cost = (input_tokens / 1_000_000) * 3.00  # $3 per 1M tokens
        output_cost = (output_tokens / 1_000_000) * 15.00  # $15 per 1M tokens
        self.estimated_cost += input_cost + output_cost
    
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
        """Get usage and cost summary"""
        return {
            'total_calls': self.call_count,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'estimated_cost': round(self.estimated_cost, 4),
            'average_input_tokens': self.total_input_tokens // max(1, self.call_count),
            'average_output_tokens': self.total_output_tokens // max(1, self.call_count)
        }

# Monkey-patch function for testing
def use_mock_client():
    """Replace real Anthropic client with mock in agent_runtime"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Import and patch
    import lib.agent_runtime as runtime
    original_init = runtime.AnthropicAgentRunner.__init__
    
    def mock_init(self, api_key=None, logger=None):
        self.api_key = "mock-key"
        self.client = MockAnthropicClient()
        self.logger = logger or runtime.get_logger()
        self.tools = {}
        self.max_retries = 3
        self.retry_delay = 2
    
    runtime.AnthropicAgentRunner.__init__ = mock_init
    return original_init

def restore_real_client(original_init):
    """Restore real Anthropic client"""
    import lib.agent_runtime as runtime
    runtime.AnthropicAgentRunner.__init__ = original_init

if __name__ == "__main__":
    # Demo the mock client
    client = MockAnthropicClient()
    
    # Simulate architect agent
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "You are a project architect. Design a system."}],
        tools=[
            {"name": "analyze_requirements", "description": "Analyze requirements"},
            {"name": "design_architecture", "description": "Design architecture"}
        ]
    )
    
    print("Mock Response:")
    for block in response.content:
        if hasattr(block, 'text'):
            print(f"Text: {block.text}")
        elif hasattr(block, 'name'):
            print(f"Tool: {block.name}")
            print(f"Input: {block.input}")
    
    print("\nUsage Summary:")
    print(client.get_usage_summary())