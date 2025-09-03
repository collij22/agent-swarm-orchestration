#!/usr/bin/env python3
"""
ENFORCE FILE WRITING - Force agents to actually write files
===========================================================

Solution: Add strong instructions and validation to ensure agents
actually call write_file instead of just talking about it.
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

def create_enforcing_prompt(files_to_create: List[str], attempt_number: int = 1) -> str:
    """Create a prompt that strongly enforces file creation"""
    
    base_severity = {
        1: "IMPORTANT",
        2: "CRITICAL", 
        3: "MANDATORY - FAILURE TO COMPLY WILL RESULT IN TASK FAILURE"
    }
    
    severity = base_severity.get(attempt_number, base_severity[3])
    
    if attempt_number == 1:
        prompt = f"""
You are a requirements analyst. You MUST create the following files:

{chr(10).join(f"{i+1}. {file}" for i, file in enumerate(files_to_create))}

{severity}: You MUST actually call the write_file tool for EACH file above!

⚠️ DO NOT just say you'll create files - ACTUALLY CALL write_file!
⚠️ DO NOT just describe what the files should contain - WRITE THEM!
⚠️ DO NOT end your response without calling write_file for EACH file!

CORRECT BEHAVIOR:
1. Analyze requirements
2. Call write_file for {files_to_create[0]} with full content
3. Call write_file for {files_to_create[1]} with full content
4. Call write_file for {files_to_create[2]} with full content

INCORRECT BEHAVIOR (what you keep doing wrong):
- Just talking about creating files
- Describing what files should contain
- Ending without calling write_file

Each write_file call MUST include:
- file_path: The exact filename from the list above
- content: The COMPLETE content for that file (not placeholders!)

Example:
```
write_file(
    file_path="API_SPEC.md",
    content="# API Specification\\n\\nComplete content here..."
)
```

Remember: You MUST call write_file for ALL {len(files_to_create)} files!
"""
    
    elif attempt_number == 2:
        prompt = f"""
{severity}! You FAILED to create the required files in your last attempt!

You were asked to create these files but you didn't:
{chr(10).join(f"❌ {file}" for file in files_to_create)}

THIS IS YOUR SECOND ATTEMPT. You MUST:
1. Call write_file for EACH file listed above
2. Include ACTUAL CONTENT (not placeholders)
3. NOT end your response until ALL files are created

The write_file tool is available and working. You just need to USE IT!

Stop talking about what you'll do and DO IT! Call write_file NOW for each file:
"""
    
    else:  # attempt 3+
        prompt = f"""
{severity}!

FINAL ATTEMPT: You have repeatedly failed to create files.

EXECUTE THESE COMMANDS NOW:

1. write_file(file_path="{files_to_create[0]}", content="[Full API documentation content here]")
2. write_file(file_path="{files_to_create[1]}", content="[Full requirements content here]") 
3. write_file(file_path="{files_to_create[2]}", content="[Full database schema JSON here]")

DO NOT RESPOND WITH ANYTHING ELSE. JUST EXECUTE THE write_file COMMANDS!
"""
    
    return prompt

def verify_files_created(output_dir: Path, expected_files: List[str]) -> Tuple[List[str], List[str]]:
    """Check which files were actually created"""
    created = []
    missing = []
    
    for file_name in expected_files:
        file_path = output_dir / file_name
        if file_path.exists() and file_path.stat().st_size > 100:  # Must have real content
            created.append(file_name)
        else:
            missing.append(file_name)
    
    return created, missing

def main():
    """Main execution with enforced file writing"""
    print("=" * 80)
    print("ENFORCE FILE WRITING - Testing Strong Instructions")
    print("=" * 80)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return 1
    
    print(f"✅ API Key configured: {api_key[:20]}...")
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-enforced")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Files we want created
    expected_files = ["API_SPEC.md", "REQUIREMENTS.md", "DATABASE_SCHEMA.json"]
    
    # Initialize runner and register tools
    runner = AnthropicAgentRunner(api_key=api_key)
    
    # Register standard tools
    for tool in create_standard_tools():
        runner.register_tool(tool)
    
    print(f"🔧 Registered {len(runner.tools)} tools: {list(runner.tools.keys())}")
    
    # Create context
    context = AgentContext(
        project_requirements={
            "project_name": "QuickShop MVP",
            "description": "E-commerce platform with enforced file creation"
        },
        completed_tasks=[],
        artifacts={
            "output_dir": str(output_dir),
            "project_directory": str(output_dir)
        },
        decisions=[],
        current_phase="requirements"
    )
    
    # Try up to 3 times with increasingly strong prompts
    max_attempts = 3
    all_files_created = False
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🚀 Attempt {attempt}/{max_attempts}: Executing requirements-analyst agent...")
        
        # Check what files still need to be created
        created, missing = verify_files_created(output_dir, expected_files)
        
        if not missing:
            print("✅ All files already exist!")
            all_files_created = True
            break
        
        print(f"📋 Files to create: {missing}")
        
        # Create enforcing prompt
        prompt = create_enforcing_prompt(missing, attempt)
        
        try:
            # Execute agent
            success, response, updated_context = runner.run_agent(
                agent_name="requirements-analyst",
                agent_prompt=prompt,
                context=context,
                model=ModelType.SONNET,
                max_iterations=10
            )
            
            # Update context
            context = updated_context
            
            # Check what was created
            created, missing = verify_files_created(output_dir, expected_files)
            
            if created:
                print(f"✅ Created {len(created)} files: {created}")
            
            if missing:
                print(f"❌ Still missing {len(missing)} files: {missing}")
                
                if attempt < max_attempts:
                    print(f"⚠️ Agent failed to create all files. Trying again with stronger instructions...")
            else:
                print("🎉 SUCCESS: All files created!")
                all_files_created = True
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Final report
    print("\n" + "=" * 80)
    print("ENFORCEMENT REPORT")
    print("=" * 80)
    
    # Check final state
    created, missing = verify_files_created(output_dir, expected_files)
    
    print(f"📊 Files requested: {len(expected_files)}")
    print(f"✅ Files created: {len(created)}")
    print(f"❌ Files missing: {len(missing)}")
    
    if created:
        print("\n✅ Successfully created:")
        for file in created:
            file_path = output_dir / file
            size = file_path.stat().st_size
            print(f"  - {file} ({size} bytes)")
    
    if missing:
        print("\n❌ Failed to create:")
        for file in missing:
            print(f"  - {file}")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "attempts": attempt,
        "expected_files": expected_files,
        "created_files": created,
        "missing_files": missing,
        "success": all_files_created
    }
    
    report_file = output_dir / "enforcement_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to {report_file}")
    
    if all_files_created:
        print("\n✅ SUCCESS: Enforcement worked! All files were created.")
    else:
        print("\n⚠️ WARNING: Even with enforcement, some files were not created.")
        print("This suggests a deeper issue with the agent's tool usage.")
    
    print("=" * 80)
    
    return 0 if all_files_created else 1

if __name__ == "__main__":
    exit(main())