#!/usr/bin/env python3
"""
Update all agent prompts with mandatory verification requirements
Phase 2.2 implementation from fix_plan_01sep2240.md
"""

import os
from pathlib import Path

# The mandatory verification steps to add to all agents
VERIFICATION_SECTION = """
## MANDATORY VERIFICATION STEPS
**YOU MUST COMPLETE THESE BEFORE MARKING ANY TASK COMPLETE:**

1. **Import Resolution Verification**:
   - After creating ANY file with imports, verify ALL imports resolve
   - Python: Check all `import` and `from ... import` statements
   - JavaScript/TypeScript: Check all `import` and `require` statements
   - If import doesn't resolve, CREATE the missing module IMMEDIATELY

2. **Entry Point Creation**:
   - If package.json references "src/main.tsx", CREATE src/main.tsx with working code
   - If main.py imports modules, CREATE those modules with implementations
   - If Dockerfile references app.py, CREATE app.py with working application
   - NO placeholders - actual working code required

3. **Working Implementation**:
   - Don't leave TODO comments without implementation
   - Include at least minimal functionality that can be tested
   - Ensure code can run without immediate errors
   - Create at least ONE working example/endpoint

4. **Syntax Verification**:
   - Python: Valid Python syntax (no SyntaxError)
   - JavaScript/TypeScript: Must compile without errors
   - JSON/YAML: Must be valid and parseable
   - Run basic syntax check before completion

5. **Dependency Consistency**:
   - If you import a package, ADD it to requirements.txt/package.json
   - If you create a service, ensure configuration is complete
   - If you reference env variables, document in .env.example

**CRITICAL**: If ANY verification step fails, FIX THE ISSUE before proceeding!
"""

def update_agent_file(file_path: Path):
    """Update an agent file with verification requirements if not already present."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if verification steps already exist
    if "MANDATORY VERIFICATION STEPS" in content:
        print(f"  [ALREADY HAS] {file_path.name} already has verification requirements")
        return False
    
    # Find a good place to insert the verification section
    # Look for common section markers in the new agent format
    insert_markers = [
        "# Core Tasks",
        "## Tools Available",
        "## Core Responsibilities", 
        "## Key Capabilities",
        "## Primary Functions",
        "## Workflow",
        "## Implementation Strategy",
        "# Implementation",
        "# Strategy",
        "**IMPORTANT**"  # Insert before the IMPORTANT section if it exists
    ]
    
    insert_position = -1
    for marker in insert_markers:
        if marker in content:
            # Insert before the marker
            insert_position = content.find(marker)
            break
    
    if insert_position == -1:
        # If no marker found, append at the end but before any ---
        if "\n---" in content:
            insert_position = content.rfind("\n---")
        else:
            # Just append at the end
            content = content.rstrip() + "\n\n" + VERIFICATION_SECTION + "\n"
    else:
        # Insert before the found marker
        content = content[:insert_position] + VERIFICATION_SECTION + "\n" + content[insert_position:]
    
    # Write back the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  [UPDATED] {file_path.name} with verification requirements")
    return True

def main():
    """Update all agent files with verification requirements."""
    
    agents_dir = Path(".claude/agents")
    
    if not agents_dir.exists():
        print(f"Error: {agents_dir} directory not found!")
        return
    
    agent_files = list(agents_dir.glob("*.md"))
    
    print(f"Found {len(agent_files)} agent files")
    print("Updating agent prompts with mandatory verification requirements...\n")
    
    updated_count = 0
    for agent_file in agent_files:
        if update_agent_file(agent_file):
            updated_count += 1
    
    print(f"\n[SUCCESS] Phase 2.2 Complete: Updated {updated_count} agent files")
    print(f"[INFO] {len(agent_files) - updated_count} agents already had verification requirements")

if __name__ == "__main__":
    main()