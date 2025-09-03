#!/usr/bin/env python3
"""
ULTIMATE INTELLIGENT ORCHESTRATOR v7.0
Complete fix with enhanced agent prompts and better error handling
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
import uuid
import traceback

# Add the parent directory to the path to import from lib
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_runtime import (
    AnthropicAgentRunner, 
    AgentContext,
    create_standard_tools,
    Tool
)

# ===================== Enhanced Write File Tool =====================

def enhanced_write_file_tool(file_path: str, content: str = None, reasoning: str = None,
                            context: AgentContext = None, agent_name: str = None) -> str:
    """Enhanced write_file with better error handling and validation"""
    
    # CRITICAL: Check if content is provided
    if not content or content.strip() == "":
        error_msg = f"""
❌ ERROR: write_file called without content!
Agent: {agent_name or 'unknown'}
File: {file_path}

REQUIRED FORMAT:
write_file(
    file_path="path/to/file.ext",
    content="ACTUAL FILE CONTENT HERE - NOT A PLACEHOLDER!"
)

The agent MUST provide the complete file content, not just describe what should be in the file.
"""
        print(error_msg)
        
        # Generate a helpful placeholder that reminds the agent
        placeholder = f"""# {Path(file_path).name}

❌ ERROR: This file was created with placeholder content because the agent didn't provide actual content.

The agent called write_file with:
- file_path: {file_path}
- content: {content if content else 'NOT PROVIDED'}

TO FIX: The agent must call write_file with BOTH parameters:
1. file_path: The path where to create the file
2. content: The ACTUAL CONTENT of the file (the code, configuration, or documentation text)

Example:
write_file(
    file_path="backend/main.py",
    content=\"\"\"
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {{"message": "Hello World"}}
\"\"\"
)
"""
        content = placeholder
    
    # Get project directory from context
    if context and "project_directory" in context.artifacts:
        project_base = Path(context.artifacts["project_directory"])
    else:
        project_base = Path.cwd() / 'projects' / 'output'
    
    # Handle file path
    if not Path(file_path).is_absolute():
        full_path = project_base / file_path
    else:
        full_path = Path(file_path)
    
    # Create parent directories
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the file
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ Created: {file_path} ({len(content)} bytes)")
        return f"Successfully created {file_path}"
    except Exception as e:
        error_msg = f"Failed to write {file_path}: {str(e)}"
        print(f"  ✗ {error_msg}")
        return error_msg

# ===================== Data Classes =====================

@dataclass
class AgentResult:
    """Store structured agent execution results"""
    agent_name: str
    success: bool
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)  
    duration: float = 0.0
    error_message: Optional[str] = None
    artifacts_produced: Dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    warnings: List[str] = field(default_factory=list)

class CommunicationHub:
    """Centralized communication and artifact management"""
    
    def __init__(self):
        self.agent_outputs: Dict[str, AgentResult] = {}
        self.shared_artifacts: Dict[str, Any] = {}
        self.file_registry: Dict[str, str] = {}
        self.agent_messages: List[Dict[str, str]] = []
        self.error_patterns: Dict[str, int] = {}  # Track error patterns
        
    def register_output(self, agent_name: str, result: AgentResult):
        """Register agent output"""
        self.agent_outputs[agent_name] = result
        
        # Track files
        for file in result.files_created:
            self.file_registry[file] = agent_name
            
        # Track error patterns
        if not result.success and result.error_message:
            if "without content parameter" in result.error_message:
                self.error_patterns["missing_content"] = self.error_patterns.get("missing_content", 0) + 1
    
    def get_agent_summary(self, agent_name: str) -> str:
        """Get formatted summary of agent output"""
        if agent_name not in self.agent_outputs:
            return f"{agent_name}: Not executed yet"
        
        result = self.agent_outputs[agent_name]
        if result.success:
            files_info = f" ({len(result.files_created)} files)" if result.files_created else ""
            return f"{agent_name}: SUCCESS{files_info}"
        else:
            return f"{agent_name}: FAILED - {result.error_message[:100] if result.error_message else 'Unknown error'}"

class FileTracker:
    """File tracking with verification"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.file_snapshots: Dict[str, Set[Path]] = {}
        
    def snapshot(self, label: str) -> Set[Path]:
        """Take a snapshot of current files"""
        current_files = self.get_current_files()
        self.file_snapshots[label] = current_files
        return current_files
        
    def get_current_files(self) -> Set[Path]:
        """Get all files in output directory"""
        files = set()
        if self.output_dir.exists():
            for item in self.output_dir.rglob('*'):
                if item.is_file():
                    files.add(item)
        return files
    
    def get_new_files(self, before_label: str, after_label: str = None) -> List[str]:
        """Get files created between two snapshots"""
        if after_label:
            after_files = self.file_snapshots.get(after_label, set())
        else:
            after_files = self.get_current_files()
            
        before_files = self.file_snapshots.get(before_label, set())
        new_files = after_files - before_files
        
        # Return relative paths
        return [str(f.relative_to(self.output_dir)) for f in new_files]
    
    def check_file_content(self, file_path: str) -> bool:
        """Check if file has real content (not just placeholder)"""
        full_path = self.output_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for placeholder indicators
                if "TODO: Add content" in content or "ERROR: This file was created with placeholder" in content:
                    return False
                return len(content.strip()) > 10  # At least some real content
        except:
            return False

class DependencyGraph:
    """Manage agent dependencies"""
    
    def __init__(self):
        self.dependencies = {
            "requirements-analyst": [],
            "project-architect": ["requirements-analyst"],
            "database-expert": ["project-architect"],
            "rapid-builder": ["project-architect", "database-expert"],
            "frontend-specialist": ["project-architect"],
            "api-integrator": ["rapid-builder", "frontend-specialist"],
            "devops-engineer": ["rapid-builder", "api-integrator"],
            "quality-guardian": ["devops-engineer"]
        }
        
    def can_run(self, agent: str, completed: Set[str]) -> bool:
        """Check if agent can run based on completed dependencies"""
        return all(dep in completed for dep in self.dependencies.get(agent, []))
    
    def get_ready_agents(self, completed: Set[str], failed: Set[str], running: Set[str] = None) -> List[str]:
        """Get agents ready to run"""
        running = running or set()
        ready = []
        
        for agent in self.dependencies:
            if agent in completed or agent in failed or agent in running:
                continue
                
            if self.can_run(agent, completed):
                deps_failed = any(dep in failed for dep in self.dependencies.get(agent, []))
                if not deps_failed:
                    ready.append(agent)
                    
        return ready

# ===================== Ultimate Orchestrator =====================

class UltimateOrchestrator:
    """Ultimate orchestrator with enhanced prompts and error handling"""
    
    def __init__(self, api_key: str, output_dir: Path):
        self.api_key = api_key
        self.output_dir = output_dir
        self.runner = AnthropicAgentRunner(api_key=api_key)
        self.context = None
        self.comm_hub = CommunicationHub()
        self.file_tracker = FileTracker(output_dir)
        self.dependency_graph = DependencyGraph()
        
        # Register enhanced tools
        self.register_enhanced_tools()
            
        # Track execution
        self.completed_agents = set()
        self.failed_agents = set()
        self.running_agents = set()
        self.max_retries = 3
        
    def register_enhanced_tools(self):
        """Register tools with enhanced write_file"""
        # Get standard tools
        for tool in create_standard_tools():
            if tool.name != "write_file":
                self.runner.register_tool(tool)
        
        # Register enhanced write_file
        enhanced_tool = Tool(
            name="write_file",
            description="""Write content to a file. 
CRITICAL: You MUST provide BOTH parameters:
1. file_path: Where to create the file (e.g., "backend/main.py")
2. content: The ACTUAL CONTENT of the file - the complete code, configuration, or text

NEVER call this without content! The content parameter must contain the actual file contents, not a description of what should be in the file.""",
            parameters={
                "file_path": {"type": "string", "description": "Path to file", "required": True},
                "content": {"type": "string", "description": "ACTUAL content to write - the complete file contents", "required": True}
            },
            function=enhanced_write_file_tool
        )
        self.runner.register_tool(enhanced_tool)
        
    def initialize_context(self, requirements: Dict) -> AgentContext:
        """Initialize context with proper project directory"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={
                "output_dir": str(self.output_dir),
                "project_directory": str(self.output_dir),
                "project_base": str(self.output_dir),
                "working_directory": str(self.output_dir)
            },
            decisions=[],
            current_phase="initialization"
        )
        
        return context
    
    def build_agent_prompt(self, agent_name: str, retry_context: str = "") -> str:
        """Build enhanced agent prompt with clear instructions"""
        
        # Get dependency outputs
        dependency_summaries = []
        for dep in self.dependency_graph.dependencies.get(agent_name, []):
            summary = self.comm_hub.get_agent_summary(dep)
            dependency_summaries.append(summary)
        
        # Add error context if retrying
        error_section = ""
        if retry_context:
            error_section = f"""
## ⚠️ PREVIOUS ATTEMPT FAILED

{retry_context}

COMMON MISTAKES TO AVOID:
1. Calling write_file without the 'content' parameter
2. Providing placeholder text instead of actual code
3. Describing what should be in a file instead of writing the actual content

CORRECT EXAMPLE:
write_file(
    file_path="backend/main.py",
    content=\"\"\"from fastapi import FastAPI
    
app = FastAPI()

@app.get("/")
def root():
    return {{"message": "QuickShop API"}}
\"\"\"
)
"""
        
        prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

## 🚨 CRITICAL INSTRUCTIONS - READ CAREFULLY

1. **ALWAYS provide CONTENT when calling write_file**
   - The 'content' parameter is REQUIRED and must contain the ACTUAL FILE CONTENT
   - Do NOT just describe what should be in the file
   - Do NOT write placeholder text like "TODO" or "Add content here"
   
2. **Create REAL IMPLEMENTATION FILES**
   - Write actual working code, not stubs or placeholders
   - Include proper imports, functions, and logic
   - Files should be complete and functional

3. **File Creation Examples**:
   ```
   # CORRECT - Provides actual content:
   write_file(
       file_path="backend/models.py",
       content=\"\"\"from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Product(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    created_at: datetime
\"\"\"
   )
   
   # WRONG - Missing content:
   write_file(file_path="backend/models.py")  # ❌ NO CONTENT!
   ```

{error_section}

## Your Role
{self._get_agent_description(agent_name)}

## Dependencies Completed
{chr(10).join(dependency_summaries) if dependency_summaries else "No dependencies"}

## Project Requirements
Build a QuickShop MVP e-commerce platform with:
- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI + PostgreSQL
- Features: User auth, product catalog, shopping cart, orders, admin dashboard
- Deployment: Docker + docker-compose

## Expected Deliverables for {agent_name}
{self._get_agent_deliverables(agent_name)}

## Output Directory
All files should be created under: {self.output_dir}
Use relative paths like: "backend/main.py", "frontend/src/App.tsx", "docker-compose.yml"

REMEMBER: Every write_file call MUST include the 'content' parameter with the ACTUAL FILE CONTENTS!
Create the files now with real, working code - not placeholders!
"""
        return prompt
    
    def _get_agent_description(self, agent_name: str) -> str:
        """Get agent-specific description"""
        descriptions = {
            "requirements-analyst": "Analyze requirements and create detailed specification documents",
            "project-architect": "Design system architecture and create technical blueprints",
            "database-expert": "Design and implement PostgreSQL database schema",
            "rapid-builder": "Build the FastAPI backend with all endpoints and models",
            "frontend-specialist": "Create the React TypeScript frontend application",
            "api-integrator": "Integrate frontend with backend APIs",
            "devops-engineer": "Set up Docker containers and deployment configuration",
            "quality-guardian": "Perform testing and quality assurance"
        }
        return descriptions.get(agent_name, "Specialized development agent")
    
    def _get_agent_deliverables(self, agent_name: str) -> str:
        """Get specific deliverables with examples"""
        deliverables = {
            "requirements-analyst": """
Create these files with COMPLETE CONTENT:
1. REQUIREMENTS.md - Full requirements specification
2. API_SPEC.md - Complete API documentation with all endpoints
3. USER_STORIES.md - Detailed user stories

Example for API_SPEC.md:
```
# API Specification

## Authentication Endpoints

### POST /api/auth/register
Register a new user...
[Complete endpoint documentation]
```
""",
            "project-architect": """
Create these files with COMPLETE CONTENT:
1. ARCHITECTURE.md - System architecture documentation
2. TECH_STACK.md - Technology choices and rationale
3. PROJECT_STRUCTURE.md - Directory structure and organization
""",
            "database-expert": """
Create these files with COMPLETE SQL:
1. database/schema.sql - Complete database schema
2. database/migrations/001_initial.sql - Initial migration
3. database/seed_data.sql - Sample data for testing
""",
            "rapid-builder": """
Create these Python files with COMPLETE CODE:
1. backend/main.py - FastAPI application entry point
2. backend/models.py - Pydantic models for data validation
3. backend/database.py - Database connection and session management
4. backend/routes/auth.py - Authentication endpoints
5. backend/routes/products.py - Product management endpoints
6. backend/requirements.txt - Python dependencies
""",
            "frontend-specialist": """
Create these React/TypeScript files with COMPLETE CODE:
1. frontend/src/App.tsx - Main React application
2. frontend/src/components/Header.tsx - Navigation header
3. frontend/src/pages/HomePage.tsx - Home page component
4. frontend/src/pages/ProductList.tsx - Product listing page
5. frontend/package.json - NPM dependencies
6. frontend/tsconfig.json - TypeScript configuration
""",
            "api-integrator": """
Create integration files with COMPLETE CODE:
1. frontend/src/api/client.ts - API client configuration
2. frontend/src/api/auth.ts - Authentication API calls
3. frontend/src/api/products.ts - Product API calls
4. backend/middleware/cors.py - CORS middleware
""",
            "devops-engineer": """
Create these configuration files with COMPLETE CONTENT:
1. docker-compose.yml - Docker orchestration
2. backend/Dockerfile - Backend container configuration
3. frontend/Dockerfile - Frontend container configuration
4. .env.example - Environment variables template
5. nginx.conf - Reverse proxy configuration
""",
            "quality-guardian": """
Create test files with COMPLETE CODE:
1. tests/test_auth.py - Authentication tests
2. tests/test_products.py - Product API tests
3. TEST_REPORT.md - Test execution report
4. QUALITY_CHECKLIST.md - Quality verification checklist
"""
        }
        return deliverables.get(agent_name, "Create relevant files with complete content for your role")
    
    def execute_agent(self, agent_name: str) -> AgentResult:
        """Execute a single agent with enhanced error handling"""
        
        print(f"\n{'='*60}")
        print(f"Executing: {agent_name}")
        print(f"{'='*60}")
        
        self.running_agents.add(agent_name)
        
        # Take file snapshot before
        before_snapshot = self.file_tracker.snapshot(f"{agent_name}_before")
        
        start_time = time.time()
        last_error = None
        retry_context = ""
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"  Retry {attempt}/{self.max_retries-1}...")
                    retry_context = f"""
Previous attempt failed with error:
{last_error}

Make sure to:
1. Include the 'content' parameter in EVERY write_file call
2. Provide the ACTUAL FILE CONTENT, not descriptions
3. Write complete, working code
"""
                
                # Build prompt with retry context
                prompt = self.build_agent_prompt(agent_name, retry_context)
                
                # Execute agent
                success, response, updated_context = self.runner.run_agent(
                    agent_name=agent_name,
                    agent_prompt=prompt,
                    context=self.context
                )
                
                # Update context
                self.context = updated_context
                
                # Check if successful
                if not success:
                    raise Exception(f"Agent execution failed: {response}")
                
                # Take snapshot after
                after_snapshot = self.file_tracker.snapshot(f"{agent_name}_after")
                new_files = self.file_tracker.get_new_files(f"{agent_name}_before", f"{agent_name}_after")
                
                # Verify files have real content
                valid_files = []
                placeholder_files = []
                for file in new_files:
                    if self.file_tracker.check_file_content(file):
                        valid_files.append(file)
                    else:
                        placeholder_files.append(file)
                
                # Check if we have valid files
                if placeholder_files and attempt < self.max_retries - 1:
                    error_msg = f"Created {len(placeholder_files)} placeholder files: {', '.join(placeholder_files[:3])}"
                    print(f"  ⚠️ {error_msg}")
                    last_error = error_msg
                    continue  # Retry
                
                # Success!
                self.context.completed_tasks.append(f"{agent_name}: SUCCESS")
                
                # Create result
                agent_result = AgentResult(
                    agent_name=agent_name,
                    success=True,
                    files_created=valid_files,
                    duration=time.time() - start_time,
                    attempts=attempt + 1,
                    warnings=[f"Placeholder: {f}" for f in placeholder_files] if placeholder_files else []
                )
                
                # Register output
                self.comm_hub.register_output(agent_name, agent_result)
                
                print(f"  Status: SUCCESS")
                print(f"  Valid files created: {len(valid_files)}")
                if valid_files:
                    for f in valid_files[:5]:
                        print(f"    ✓ {f}")
                if placeholder_files:
                    print(f"  Placeholder files: {len(placeholder_files)}")
                print(f"  Duration: {agent_result.duration:.1f}s")
                print(f"  Attempts: {agent_result.attempts}")
                
                self.running_agents.discard(agent_name)
                self.completed_agents.add(agent_name)
                
                return agent_result
                
            except Exception as e:
                last_error = str(e)
                print(f"  Error (attempt {attempt+1}): {last_error[:200]}")
                
                if attempt == self.max_retries - 1:
                    # Final failure
                    self.context.completed_tasks.append(f"{agent_name}: FAILED")
                    
                    agent_result = AgentResult(
                        agent_name=agent_name,
                        success=False,
                        duration=time.time() - start_time,
                        error_message=last_error[:500],
                        attempts=self.max_retries
                    )
                    
                    self.comm_hub.register_output(agent_name, agent_result)
                    
                    print(f"  Status: FAILED after {self.max_retries} attempts")
                    
                    self.running_agents.discard(agent_name)
                    self.failed_agents.add(agent_name)
                    
                    return agent_result
        
        self.running_agents.discard(agent_name)
        self.failed_agents.add(agent_name)
        return AgentResult(agent_name=agent_name, success=False, error_message="Unknown error")
    
    def orchestrate(self) -> Dict:
        """Main orchestration logic"""
        
        print("\n" + "="*60)
        print("ULTIMATE INTELLIGENT ORCHESTRATOR v7.0")
        print("With Enhanced Prompts and Error Recovery")
        print("="*60)
        
        start_time = time.time()
        
        all_agents = list(self.dependency_graph.dependencies.keys())
        max_iterations = len(all_agents) * 3
        iteration = 0
        
        while len(self.completed_agents) + len(self.failed_agents) < len(all_agents):
            iteration += 1
            
            if iteration > max_iterations:
                print("\n❌ Maximum iterations exceeded")
                break
            
            ready = self.dependency_graph.get_ready_agents(
                self.completed_agents,
                self.failed_agents,
                self.running_agents
            )
            
            if not ready:
                if len(self.failed_agents) > 0:
                    print(f"\n⚠️ Cannot continue: {len(self.failed_agents)} agents failed")
                    for agent in self.failed_agents:
                        result = self.comm_hub.agent_outputs.get(agent)
                        if result:
                            print(f"  - {agent}: {result.error_message[:100]}")
                    break
                else:
                    print("\n⚠️ No agents ready")
                    break
            
            # Execute first ready agent
            for agent in ready[:1]:
                result = self.execute_agent(agent)
                
            # Save checkpoint
            if len(self.completed_agents) % 2 == 0 or len(self.failed_agents) > 0:
                self.save_checkpoint()
        
        # Final summary
        total_duration = time.time() - start_time
        
        print("\n" + "="*60)
        print("ORCHESTRATION COMPLETE")
        print("="*60)
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Agents Completed: {len(self.completed_agents)}/{len(all_agents)}")
        print(f"Agents Failed: {len(self.failed_agents)}")
        
        # Check for common errors
        if self.comm_hub.error_patterns.get("missing_content", 0) > 0:
            print(f"\n⚠️ Missing content errors: {self.comm_hub.error_patterns['missing_content']} times")
            print("  Agents are not providing content parameter in write_file calls")
        
        # List completed agents
        if self.completed_agents:
            print("\n✅ Completed Agents:")
            for agent in self.completed_agents:
                result = self.comm_hub.agent_outputs.get(agent)
                if result and result.files_created:
                    print(f"  - {agent}: {len(result.files_created)} valid files")
                else:
                    print(f"  - {agent}")
        
        # Verify files
        print("\n📁 File Verification:")
        all_files = self.file_tracker.get_current_files()
        valid_files = []
        placeholder_files = []
        
        for f in all_files:
            rel_path = str(f.relative_to(self.output_dir))
            if not rel_path.endswith('.json'):
                if self.file_tracker.check_file_content(rel_path):
                    valid_files.append(rel_path)
                else:
                    placeholder_files.append(rel_path)
        
        print(f"Valid files with content: {len(valid_files)}")
        for file in sorted(valid_files)[:10]:
            print(f"  ✓ {file}")
        
        if placeholder_files:
            print(f"\nPlaceholder files (need content): {len(placeholder_files)}")
            for file in sorted(placeholder_files)[:5]:
                print(f"  ⚠️ {file}")
        
        # Save final context
        self.save_final_context()
        
        return {
            "success": len(self.failed_agents) == 0,
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "total_duration": total_duration,
            "valid_files": len(valid_files),
            "placeholder_files": len(placeholder_files)
        }
    
    def save_checkpoint(self):
        """Save checkpoint"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "context": {
                "completed_tasks": self.context.completed_tasks[-20:],
                "artifacts": self.context.artifacts
            },
            "error_patterns": self.comm_hub.error_patterns,
            "files_created": len(self.file_tracker.get_current_files())
        }
        
        checkpoint_file = self.output_dir / "checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
    
    def save_final_context(self):
        """Save final context"""
        all_files = self.file_tracker.get_current_files()
        file_list = []
        for f in all_files:
            rel_path = str(f.relative_to(self.output_dir))
            file_list.append({
                "path": rel_path,
                "valid": self.file_tracker.check_file_content(rel_path)
            })
        
        final_context = {
            "timestamp": datetime.now().isoformat(),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "total_files": len(file_list),
            "files": file_list,
            "error_patterns": self.comm_hub.error_patterns,
            "agent_outputs": {
                k: asdict(v) for k, v in self.comm_hub.agent_outputs.items()
            }
        }
        
        context_file = self.output_dir / "final_context.json"
        with open(context_file, 'w') as f:
            json.dump(final_context, f, indent=2, default=str)

# ===================== Main Entry Point =====================

def main():
    """Main execution"""
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        return 1
    
    # Set up output directory
    output_dir = Path.cwd() / "projects" / "quickshop-mvp-ultimate"
    
    # Clean output directory
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    
    # Define requirements
    requirements = {
        "project_name": "QuickShop MVP",
        "description": "Modern e-commerce platform",
        "tech_stack": {
            "frontend": "React + TypeScript + Tailwind CSS",
            "backend": "FastAPI + PostgreSQL",
            "deployment": "Docker + docker-compose"
        }
    }
    
    # Create orchestrator
    orchestrator = UltimateOrchestrator(api_key, output_dir)
    
    # Initialize context
    orchestrator.context = orchestrator.initialize_context(requirements)
    
    # Run orchestration
    try:
        result = orchestrator.orchestrate()
        
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        if result["success"]:
            print("✅ All agents completed successfully!")
        else:
            print(f"⚠️ {len(result['failed_agents'])} agents failed")
        
        print(f"\n📊 Statistics:")
        print(f"  - Duration: {result['total_duration']:.1f}s")
        print(f"  - Valid Files: {result['valid_files']}")
        print(f"  - Placeholder Files: {result['placeholder_files']}")
        print(f"  - Success Rate: {len(result['completed_agents'])}/{8}")
        
        print(f"\n📁 Output Directory: {output_dir}")
        
        return 0 if result["success"] else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        return 2
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)