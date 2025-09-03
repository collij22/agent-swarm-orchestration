#!/usr/bin/env python3
"""
SIMPLE ROBUST ORCHESTRATOR - Simplified version with tool interception
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our libraries
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools, ModelType

class ToolInterceptor:
    """Intercepts and fixes tool calls with missing parameters"""
    
    def __init__(self):
        self.intercepted_calls = []
        self.fixed_calls = []
    
    def intercept_write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fix write_file calls with missing content"""
        if "content" not in params or not params.get("content"):
            file_path = params.get("file_path", "unknown.txt")
            ext = Path(file_path).suffix.lower()
            
            # Generate appropriate placeholder content
            if ext == '.py':
                content = '"""TODO: Implement this module"""\n\nraise NotImplementedError("Implementation needed")'
            elif ext == '.md':
                content = '# TODO: Add Documentation\n\nThis file needs proper content.'
            elif ext == '.json':
                content = '{\n  "error": "TODO: Add actual content",\n  "placeholder": true\n}'
            else:
                content = 'TODO: Add content for this file'
            
            params["content"] = f"# WARNING: Auto-generated - agent didn't provide content\n# {datetime.now()}\n\n{content}"
            
            self.fixed_calls.append(file_path)
            print(f"🔧 Fixed missing content for {file_path}")
        
        self.intercepted_calls.append(params.get("file_path", "unknown"))
        return params

def main():
    """Main execution"""
    print("=" * 80)
    print("SIMPLE ROBUST ORCHESTRATOR - Tool Interception Test")
    print("=" * 80)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return 1
    
    print(f"✅ API Key configured: {api_key[:20]}...")
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-simple-robust")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Initialize components
    interceptor = ToolInterceptor()
    runner = AnthropicAgentRunner(api_key=api_key)
    
    # Create context
    context = AgentContext(
        project_requirements={
            "project_name": "QuickShop MVP",
            "description": "E-commerce platform test"
        },
        completed_tasks=[],
        artifacts={
            "output_dir": str(output_dir),
            "project_directory": str(output_dir)
        },
        decisions=[],
        current_phase="requirements"
    )
    
    # Enhanced prompt with clear instructions
    prompt = """
You are a requirements analyst. Create an API specification document.

CRITICAL: When using write_file, you MUST include BOTH parameters:

CORRECT ✅:
write_file(
    file_path="API_SPEC.md",
    content="# API Specification\\n\\nActual content here..."
)

WRONG ❌:
write_file(file_path="API_SPEC.md")  # Missing content!

Create API_SPEC.md with complete REST API documentation including:
- Authentication endpoints
- Product endpoints  
- Order endpoints
- User endpoints

Include the FULL content in the write_file call!
"""
    
    print("\n🚀 Executing requirements-analyst agent...")
    
    # Monkey-patch the write_file_tool directly
    import lib.agent_runtime
    original_write_file = lib.agent_runtime.write_file_tool
    
    async def intercepted_write_file_tool(file_path: str, content: str = None, **kwargs):
        """Intercepted version that fixes missing content"""
        # Fix missing content
        if not content:
            ext = Path(file_path).suffix.lower()
            
            # Generate appropriate placeholder content
            if ext == '.py':
                content = '"""TODO: Implement this module"""\n\nraise NotImplementedError("Implementation needed")'
            elif ext == '.md':
                content = '# TODO: Add Documentation\n\nThis file needs proper content.'
            elif ext == '.json':
                content = '{\n  "error": "TODO: Add actual content",\n  "placeholder": true\n}'
            else:
                content = 'TODO: Add content for this file'
            
            content = f"# WARNING: Auto-generated - agent didn't provide content\n# {datetime.now()}\n\n{content}"
            interceptor.fixed_calls.append(file_path)
            print(f"🔧 Fixed missing content for {file_path}")
        
        interceptor.intercepted_calls.append(file_path)
        
        # Call original with fixed params
        return await original_write_file(file_path=file_path, content=content, **kwargs)
    
    # Replace with intercepted version
    lib.agent_runtime.write_file_tool = intercepted_write_file_tool
    
    try:
        # Execute agent
        success, response, updated_context = runner.run_agent(
            agent_name="requirements-analyst",
            agent_prompt=prompt,
            context=context
        )
        
        if success:
            print("✅ Agent completed successfully")
        else:
            print(f"❌ Agent failed: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore original function
        if 'original_write_file' in locals():
            lib.agent_runtime.write_file_tool = original_write_file
    
    # Report
    print("\n" + "=" * 80)
    print("EXECUTION REPORT")
    print("=" * 80)
    print(f"📊 Tool calls intercepted: {len(interceptor.intercepted_calls)}")
    print(f"🔧 Calls with missing content fixed: {len(interceptor.fixed_calls)}")
    
    if interceptor.fixed_calls:
        print("\nFiles that had content auto-generated:")
        for file in interceptor.fixed_calls:
            print(f"  - {file}")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "intercepted_calls": interceptor.intercepted_calls,
        "fixed_calls": interceptor.fixed_calls,
        "success": success if 'success' in locals() else False
    }
    
    report_file = output_dir / "interception_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to {report_file}")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    exit(main())