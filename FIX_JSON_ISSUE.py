#!/usr/bin/env python3
"""
FIX JSON ISSUE - Targeted fix for agents failing to create JSON files
=====================================================================

Problem: Agents successfully create .md files with content but fail
to include content when creating .json files.

Solution: Special handling and examples for JSON file creation.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools, ModelType

def create_json_specific_prompt(json_file_name: str) -> str:
    """Create a prompt specifically for JSON file creation"""
    
    # Pre-create example JSON content as a string
    example_json = {
        "database_name": "quickshop_db",
        "tables": {
            "users": {
                "columns": {
                    "id": "uuid PRIMARY KEY",
                    "email": "varchar(255) UNIQUE NOT NULL"
                }
            }
        }
    }
    
    # Convert to string for the example
    json_string = json.dumps(example_json, indent=2)
    
    prompt = f"""
You need to create {json_file_name} with database schema information.

CRITICAL FOR JSON FILES: The content must be a STRING containing valid JSON!

⚠️ COMMON MISTAKE: Trying to pass JSON object directly
❌ WRONG:
write_file(
    file_path="{json_file_name}",
    content: {{"key": "value"}}  # WRONG - not a string!
)

✅ CORRECT - JSON must be passed as a STRING:
write_file(
    file_path="{json_file_name}",
    content='{json_string}'  # Correct - JSON as string!
)

ALTERNATIVE CORRECT APPROACH:
write_file(
    file_path="{json_file_name}",
    content=\"\"\"{json_string}\"\"\"  # Also correct - triple quotes
)

Now create {json_file_name} with a complete database schema including:
- users table (id, email, password_hash, created_at, updated_at)
- products table (id, name, description, price, stock, created_at)
- orders table (id, user_id, total, status, created_at)
- order_items table (id, order_id, product_id, quantity, price)

Remember: The content parameter must be a STRING containing the JSON, not a JSON object!
"""
    
    return prompt

def create_enhanced_write_file():
    """Create an enhanced write_file tool that helps with JSON"""
    
    async def enhanced_write_file(file_path: str, content: Any, **kwargs):
        """Enhanced write_file that handles JSON specially"""
        
        # If content is a dict/list and file is .json, convert to string
        if isinstance(content, (dict, list)) and file_path.endswith('.json'):
            content = json.dumps(content, indent=2)
            print(f"📝 Auto-converted JSON object to string for {file_path}")
        
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)
        
        # Call the original write_file
        from lib.agent_runtime import write_file_tool
        return await write_file_tool(file_path=file_path, content=content, **kwargs)
    
    return enhanced_write_file

def verify_json_files(output_dir: Path, json_files: List[str]) -> Dict[str, Any]:
    """Verify JSON files were created and are valid"""
    results = {}
    
    for file_name in json_files:
        file_path = output_dir / file_name
        results[file_name] = {
            "exists": False,
            "valid_json": False,
            "size": 0,
            "content_preview": None
        }
        
        if file_path.exists():
            results[file_name]["exists"] = True
            results[file_name]["size"] = file_path.stat().st_size
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    json_data = json.loads(content)
                    results[file_name]["valid_json"] = True
                    results[file_name]["content_preview"] = str(json_data)[:200]
            except json.JSONDecodeError as e:
                results[file_name]["json_error"] = str(e)
    
    return results

def main():
    """Test JSON file creation with targeted fixes"""
    print("=" * 80)
    print("FIX JSON ISSUE - Targeted Solution")
    print("=" * 80)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return 1
    
    print(f"✅ API Key configured: {api_key[:20]}...")
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-json-fix")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Initialize runner
    runner = AnthropicAgentRunner(api_key=api_key)
    
    # Register tools (including enhanced write_file)
    for tool in create_standard_tools():
        runner.register_tool(tool)
    
    # Override write_file with enhanced version
    import lib.agent_runtime
    original_write_file = lib.agent_runtime.write_file_tool
    lib.agent_runtime.write_file_tool = create_enhanced_write_file()
    
    print(f"🔧 Registered {len(runner.tools)} tools with JSON enhancement")
    
    # Create context
    context = AgentContext(
        project_requirements={
            "project_name": "QuickShop MVP",
            "description": "Testing JSON file creation"
        },
        completed_tasks=[],
        artifacts={
            "output_dir": str(output_dir),
            "project_directory": str(output_dir)
        },
        decisions=[],
        current_phase="requirements"
    )
    
    # Test creating different file types
    test_files = [
        ("API_SPEC.md", "Create API specification markdown"),
        ("DATABASE_SCHEMA.json", create_json_specific_prompt("DATABASE_SCHEMA.json")),
        ("CONFIG.json", create_json_specific_prompt("CONFIG.json"))
    ]
    
    results = {}
    
    for file_name, prompt in test_files:
        print(f"\n🚀 Creating {file_name}...")
        
        try:
            success, response, updated_context = runner.run_agent(
                agent_name="requirements-analyst",
                agent_prompt=prompt,
                context=context,
                model=ModelType.SONNET
            )
            
            context = updated_context
            
            # Check if file was created
            file_path = output_dir / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✅ {file_name} created ({size} bytes)")
                results[file_name] = "success"
            else:
                print(f"❌ {file_name} not created")
                results[file_name] = "failed"
                
        except Exception as e:
            print(f"❌ Error creating {file_name}: {e}")
            results[file_name] = f"error: {e}"
    
    # Restore original write_file
    lib.agent_runtime.write_file_tool = original_write_file
    
    # Verify JSON files
    json_files = [f for f in test_files if f[0].endswith('.json')]
    json_results = verify_json_files(output_dir, [f[0] for f in json_files])
    
    # Final report
    print("\n" + "=" * 80)
    print("JSON FIX REPORT")
    print("=" * 80)
    
    print("\n📊 File Creation Results:")
    for file_name, result in results.items():
        status = "✅" if result == "success" else "❌"
        print(f"  {status} {file_name}: {result}")
    
    print("\n📋 JSON Validation Results:")
    for file_name, validation in json_results.items():
        if validation["exists"]:
            if validation["valid_json"]:
                print(f"  ✅ {file_name}: Valid JSON ({validation['size']} bytes)")
            else:
                print(f"  ⚠️ {file_name}: Invalid JSON - {validation.get('json_error', 'unknown error')}")
        else:
            print(f"  ❌ {file_name}: Not created")
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "file_results": results,
        "json_validation": json_results,
        "success": all(r == "success" for r in results.values())
    }
    
    report_file = output_dir / "json_fix_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to {report_file}")
    
    if all(validation["valid_json"] for validation in json_results.values() if validation["exists"]):
        print("\n✅ SUCCESS: JSON files created successfully with valid content!")
    else:
        print("\n⚠️ Some JSON files still have issues")
    
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    exit(main())