#!/usr/bin/env python3
"""
Diagnostic script to check why agents aren't creating files
"""

import json
import re
from pathlib import Path

def analyze_agent_output():
    """Analyze the agent output to understand file creation issues"""
    
    print("=" * 80)
    print("FILE CREATION DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # Check the context file
    context_file = Path("projects/quickshop-mvp-standalone/final_context.json")
    
    if not context_file.exists():
        print("[ERROR] No context file found!")
        return
    
    with open(context_file, 'r') as f:
        context = json.load(f)
    
    # Extract requirements-analyst output
    agent_output = context.get('artifacts', {}).get('requirements-analyst', '')
    
    # Find all write_file calls
    write_file_pattern = r'<write_file>.*?file_path:\s*(.*?)\n.*?</write_file>'
    matches = re.findall(write_file_pattern, agent_output, re.DOTALL)
    
    print(f"Found {len(matches)} write_file calls in agent output")
    
    if matches:
        print("\nAttempted file writes:")
        for i, file_path in enumerate(matches, 1):
            # Extract just the file path
            path_match = re.search(r'file_path:\s*(.+?)(?:\n|$)', file_path)
            if path_match:
                file_name = path_match.group(1).strip()
                print(f"  {i}. {file_name}")
    
    # Check what files actually exist
    output_dir = Path("projects/quickshop-mvp-standalone")
    actual_files = list(output_dir.rglob("*"))
    
    print(f"\nActual files in output directory: {len(actual_files) - 1}")  # -1 for the directory itself
    for file in actual_files:
        if file.is_file():
            print(f"  - {file.relative_to(output_dir)}")
    
    # Analyze the problem
    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("-" * 80)
    
    if len(matches) > 0 and len(actual_files) <= 2:
        print("[X] PROBLEM: Agents are generating write_file calls but files aren't being created!")
        print()
        print("Likely causes:")
        print("1. Tool handler not parsing XML-style tool calls (<write_file>...</write_file>)")
        print("2. Tool execution is disabled or broken")
        print("3. File paths are invalid or permissions issue")
        print("4. Agent runtime not registering tools properly")
        print()
        print("SOLUTION:")
        print("The agent runtime expects JSON tool calls, not XML. The agents are using")
        print("the wrong format for tool invocation!")
    
    # Check if tools are registered
    print("\n" + "=" * 80)
    print("CHECKING TOOL REGISTRATION:")
    print("-" * 80)
    
    # Look for tool registration in agent_runtime.py
    runtime_file = Path("lib/agent_runtime.py")
    if runtime_file.exists():
        with open(runtime_file, 'r', encoding='utf-8') as f:
            runtime_content = f.read()
            
        if 'register_standard_tools' in runtime_content:
            print("✓ register_standard_tools method exists")
        else:
            print("✗ register_standard_tools method NOT found!")
            
        if 'write_file' in runtime_content:
            print("✓ write_file tool referenced in runtime")
        else:
            print("✗ write_file tool NOT referenced!")
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("-" * 80)
    print("The agents are using XML-style tool calls but the runtime expects JSON.")
    print("We need to either:")
    print("1. Fix the agent prompts to use JSON tool format")
    print("2. Add XML parsing to the tool handler")
    print("3. Use a different runner that supports the agent's output format")

if __name__ == "__main__":
    analyze_agent_output()