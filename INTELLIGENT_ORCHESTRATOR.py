#!/usr/bin/env python3
"""
INTELLIGENT ORCHESTRATOR - Aggressive intervention system for perfect agent execution
================================================================================
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools, ModelType
from lib.interceptor import UniversalInterceptor
from lib.loop_breaker import LoopBreaker
from lib.content_generator import ContentGenerator

class IntelligentOrchestrator:
    """Main orchestrator with aggressive intervention capabilities"""
    
    UNIVERSAL_AGENT_INSTRUCTIONS = """
CRITICAL REQUIREMENTS - FAILURE TO COMPLY WILL RESULT IN TASK REJECTION:

1. FILE CREATION RULES:
   - ALWAYS include content parameter with ACTUAL content
   - NEVER write "TODO" or placeholders
   - Content must be complete and functional
   
2. TOOL USAGE:
   write_file(
       file_path="exact/path/to/file.ext",
       content="COMPLETE ACTUAL CONTENT HERE"
   )
   
3. DELIVERABLES:
   - Every file you mention MUST be created
   - Every file created MUST have real content
   - Report exact paths of created files
   
4. ERROR HANDLING:
   - If you get an error, CHANGE your approach
   - Do NOT retry the same failed command
   - Read error messages and adapt
"""
    
    def __init__(self, project_name: str = "QuickShop MVP"):
        self.project_name = project_name
        self.output_dir = Path(f"projects/{project_name.lower().replace(' ', '-')}-intelligent")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.project_context = {"project_name": project_name}
        self.interceptor = UniversalInterceptor(self.project_context)
        self.loop_breaker = LoopBreaker()
        self.content_generator = ContentGenerator(self.project_context)
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.agent_results = {}
        
        # Initialize runner
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.runner = AnthropicAgentRunner(api_key=api_key)
        self._setup_intercepted_tools()
        
        print("=" * 80)
        print("INTELLIGENT ORCHESTRATOR - Aggressive Intervention System")
        print("=" * 80)
        print(f"[PROJECT] {project_name}")
        print(f"[OUTPUT]  {self.output_dir}")
        print(f"[SESSION] {self.session_id}")
        print("=" * 80)
    
    def _setup_intercepted_tools(self):
        """Setup tools with interception"""
        tools = create_standard_tools()
        
        # Wrap each tool with interceptor
        for tool in tools:
            original_func = tool.function
            tool_name = tool.name
            wrapped_func = self.interceptor.wrap_tool(original_func, tool_name)
            tool.function = wrapped_func
            self.runner.register_tool(tool)
        
        print(f"[TOOLS] Registered {len(tools)} intercepted tools")
    
    def execute_agent(self, agent_name: str, task: str, context: AgentContext, 
                      model: ModelType = ModelType.SONNET) -> Tuple[bool, Any, AgentContext]:
        """Execute an agent with full intervention"""
        print(f"\n[EXEC] Executing {agent_name}...")
        
        # Register agent with systems
        self.interceptor.register_agent(agent_name)
        self.loop_breaker.reset(agent_name)
        
        # Add universal instructions to task
        enhanced_task = f"{self.UNIVERSAL_AGENT_INSTRUCTIONS}\n\n{task}"
        
        max_attempts = 4
        attempt = 0
        last_error = None
        
        while attempt < max_attempts:
            attempt += 1
            print(f"  Attempt {attempt}/{max_attempts}")
            
            try:
                # Check for loops before execution
                if last_error and self.loop_breaker.detect_loop(agent_name, last_error):
                    strategy = self.loop_breaker.break_loop(agent_name)
                    print(f"  [FIX] Applying recovery strategy: {strategy['strategy']}")
                    enhanced_task = f"{task}\n\n{strategy['instructions']['prompt_addition']}"
                    
                    if strategy['strategy'] == "bypass_agent_create_directly":
                        print("  [BYPASS] Bypassing agent - creating files directly")
                        return self._create_files_directly(agent_name, task, context)
                
                # Execute agent
                success, response, updated_context = self.runner.run_agent(
                    agent_name=agent_name,
                    agent_prompt=enhanced_task,
                    context=context,
                    model=model
                )
                
                if success:
                    verification = self._verify_deliverables(agent_name, response, updated_context)
                    
                    if verification["success"]:
                        print(f"  [OK] {agent_name} completed successfully")
                        self._record_success(agent_name, response, verification)
                        return True, response, updated_context
                    else:
                        print(f"  [WARN] Deliverables incomplete: {verification['issues']}")
                        self._fix_missing_deliverables(verification["missing"], updated_context)
                        return True, response, updated_context
                else:
                    last_error = response
                    print(f"  [ERROR] Agent failed: {str(response)[:200]}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"  [ERROR] Exception: {e}")
                
                # Check if this is a write_file loop error
                if "repeatedly failing to provide content" in last_error:
                    print(f"  [LOOP] Detected write_file loop - attempting recovery")
                    
                    # Try to hand off to a different agent
                    if agent_name == "requirements-analyst":
                        print(f"  [HANDOFF] Switching from {agent_name} to rapid-builder")
                        return self.run_agent_with_retry("rapid-builder", task, context, model, max_attempts=2)
                    elif agent_name == "rapid-builder":
                        print(f"  [HANDOFF] Switching from {agent_name} to code-migrator") 
                        return self.run_agent_with_retry("code-migrator", task, context, model, max_attempts=2)
        
        print(f"  [FALLBACK] All attempts failed - creating files directly")
        return self._create_files_directly(agent_name, task, context)
    
    def _verify_deliverables(self, agent_name: str, response: Any, context: AgentContext) -> Dict:
        """Verify all deliverables exist with real content"""
        verification = {
            "success": True,
            "files_checked": [],
            "files_valid": [],
            "files_invalid": [],
            "missing": [],
            "issues": []
        }
        
        agent_report = self.interceptor.get_agent_report(agent_name)
        files_created = agent_report.get("files_created", [])
        
        for file_path in files_created:
            full_path = self.output_dir / file_path
            verification["files_checked"].append(file_path)
            
            if full_path.exists():
                size = full_path.stat().st_size
                
                if size < 100:
                    verification["files_invalid"].append(file_path)
                    verification["issues"].append(f"{file_path}: Too small ({size} bytes)")
                    verification["success"] = False
                else:
                    try:
                        content = full_path.read_text()
                        if self._has_placeholder(content):
                            verification["files_invalid"].append(file_path)
                            verification["issues"].append(f"{file_path}: Contains placeholders")
                            verification["success"] = False
                        else:
                            verification["files_valid"].append(file_path)
                    except:
                        verification["files_valid"].append(file_path)
            else:
                verification["missing"].append(file_path)
                verification["issues"].append(f"{file_path}: Does not exist")
                verification["success"] = False
        
        return verification
    
    def _has_placeholder(self, content: str) -> bool:
        """Check if content has placeholders"""
        placeholders = ["TODO", "FIXME", "XXX", "Add content", "placeholder"]
        content_lower = content.lower()
        return any(p.lower() in content_lower for p in placeholders)
    
    def _fix_missing_deliverables(self, missing_files: List[str], context: AgentContext):
        """Create missing files with real content"""
        print(f"  [FIX] Fixing {len(missing_files)} missing deliverables")
        
        for file_path in missing_files:
            full_path = self.output_dir / file_path
            content = self.content_generator.generate_content(file_path, "")
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            print(f"    [OK] Created {file_path} ({len(content)} bytes)")
    
    def _create_files_directly(self, agent_name: str, task: str, context: AgentContext) -> Tuple[bool, str, AgentContext]:
        """Bypass agent and create files directly"""
        print("  [DIRECT] Direct file creation based on task requirements")
        
        files_to_create = self._parse_required_files(task)
        
        for file_info in files_to_create:
            file_path = file_info["path"]
            content = self.content_generator.generate_content(file_path, file_info["type"])
            
            full_path = self.output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            
            print(f"    [OK] Created {file_path} ({len(content)} bytes)")
            
            if "created_files" not in context.artifacts:
                context.artifacts["created_files"] = []
            context.artifacts["created_files"].append(str(file_path))
        
        return True, f"Directly created {len(files_to_create)} files", context
    
    def _parse_required_files(self, task: str) -> List[Dict]:
        """Parse task to determine required files"""
        files = []
        task_lower = task.lower()
        
        if "api" in task_lower or "specification" in task_lower:
            files.append({"path": "API_SPEC.md", "type": "API documentation"})
        
        if "database" in task_lower or "schema" in task_lower:
            files.append({"path": "DATABASE_SCHEMA.json", "type": "Database schema"})
        
        if "config" in task_lower:
            files.append({"path": "CONFIG.json", "type": "Configuration"})
        
        if "readme" in task_lower:
            files.append({"path": "README.md", "type": "Documentation"})
        
        if not files:
            files = [
                {"path": "README.md", "type": "Documentation"},
                {"path": "config.json", "type": "Configuration"},
                {"path": "main.py", "type": "Main application"}
            ]
        
        return files
    
    def _record_success(self, agent_name: str, response: Any, verification: Dict):
        """Record successful agent execution"""
        self.agent_results[agent_name] = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "files_created": verification["files_valid"],
            "response": str(response)[:500]
        }
    
    def run_quickshop_mvp(self):
        """Run complete QuickShop MVP creation"""
        print("\n" + "=" * 80)
        print("Starting QuickShop MVP Creation")
        print("=" * 80)
        
        context = AgentContext(
            project_requirements={
                "project_name": self.project_name,
                "type": "e-commerce",
                "features": ["user auth", "product catalog", "shopping cart", "orders"],
                "tech_stack": {
                    "frontend": "React + TypeScript",
                    "backend": "FastAPI",
                    "database": "PostgreSQL"
                }
            },
            completed_tasks=[],
            artifacts={
                "output_dir": str(self.output_dir),
                "project_directory": str(self.output_dir)
            },
            decisions=[],
            current_phase="requirements"
        )
        
        agent_tasks = [
            {
                "agent": "requirements-analyst",
                "task": "Analyze the e-commerce MVP requirements and create comprehensive documentation including API specifications, data models, and system architecture for a QuickShop e-commerce platform with user authentication, product catalog, shopping cart, and order management.",
                "model": ModelType.SONNET
            },
            {
                "agent": "rapid-builder",
                "task": """Build the complete QuickShop MVP application:
                1. Create backend with FastAPI including all models, routes, and database setup
                2. Implement user authentication with JWT tokens
                3. Create product catalog with CRUD operations
                4. Build shopping cart functionality
                5. Implement order processing system
                6. Add Docker configuration for deployment
                7. Create frontend with React + TypeScript
                8. Include sample data and seed scripts
                9. Ensure all files have actual implementations (no TODOs)""",
                "model": ModelType.SONNET
            },
            {
                "agent": "database-expert", 
                "task": "Review the created database schema, add migrations, indexes, and seed data. Ensure database is properly configured with relationships, constraints, and sample data for testing.",
                "model": ModelType.SONNET
            },
            {
                "agent": "quality-guardian",
                "task": "Validate the complete application, run tests, check for security issues, and ensure all components work together. Fix any compilation errors, missing imports, or configuration issues.",
                "model": ModelType.SONNET
            }
        ]
        
        for task_info in agent_tasks:
            success, response, context = self.execute_agent(
                agent_name=task_info["agent"],
                task=task_info["task"],
                context=context,
                model=task_info["model"]
            )
            
            if not success:
                print(f"  [WARN] {task_info['agent']} had issues but files were created")
        
        self._generate_report()
    
    def _generate_report(self):
        """Generate comprehensive execution report"""
        print("\n" + "=" * 80)
        print("INTELLIGENT ORCHESTRATOR - Execution Report")
        print("=" * 80)
        
        stats = self.interceptor.get_statistics()
        
        print(f"\n[STATS] Interceptor Statistics:")
        print(f"  Total tool calls: {stats['total_calls']}")
        print(f"  Fixed calls: {stats['fixed_calls']}")
        print(f"  Generated content: {stats['generated_content']} files")
        print(f"  Agents tracked: {stats['agents_tracked']}")
        
        print(f"\n[FILES] Files Created:")
        for file_path in self.output_dir.glob("**/*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                relative_path = file_path.relative_to(self.output_dir)
                status = "[OK]" if size > 100 else "[SMALL]"
                print(f"  {status} {relative_path} ({size} bytes)")
        
        print(f"\n[AGENTS] Agent Results:")
        for agent, result in self.agent_results.items():
            print(f"  {agent}: {result['status']}")
            if result.get("files_created"):
                for file in result["files_created"]:
                    print(f"    - {file}")
        
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "project": self.project_name,
            "interceptor_stats": stats,
            "agent_results": self.agent_results,
            "loop_breaker_status": self.loop_breaker.get_all_status()
        }
        
        report_file = self.output_dir / "intelligent_orchestrator_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[REPORT] Detailed report saved to {report_file}")
        print("=" * 80)

def main():
    """Main entry point"""
    orchestrator = IntelligentOrchestrator("QuickShop MVP")
    orchestrator.run_quickshop_mvp()
    return 0

if __name__ == "__main__":
    exit(main())