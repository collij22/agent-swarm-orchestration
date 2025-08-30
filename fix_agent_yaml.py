#!/usr/bin/env python3
"""Fix YAML frontmatter in agent markdown files"""

import os
import re
from pathlib import Path

def fix_agent_file(filepath):
    """Fix YAML frontmatter in a single agent file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has frontmatter
    if not content.startswith('---'):
        print(f"  Skipping {filepath.name} - no frontmatter")
        return False
    
    # Split frontmatter and content
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"  Skipping {filepath.name} - invalid structure")
        return False
    
    frontmatter = parts[1].strip()
    body = parts[2]
    
    # Parse and fix frontmatter
    lines = frontmatter.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.startswith('description:'):
            # Extract description value
            desc_match = re.match(r'description:\s*(.*)', line)
            if desc_match:
                desc_value = desc_match.group(1).strip()
                # Remove any existing quotes
                desc_value = desc_value.strip('"').strip("'")
                # Clean up escaped characters and newlines
                desc_value = desc_value.replace('\\n', ' ').replace('\\', '')
                # Remove example blocks if present
                desc_value = re.sub(r'<example>.*?</example>', '', desc_value, flags=re.DOTALL)
                desc_value = re.sub(r'<commentary>.*?</commentary>', '', desc_value, flags=re.DOTALL)
                # Clean up extra spaces
                desc_value = ' '.join(desc_value.split())
                # Truncate if too long
                if len(desc_value) > 200:
                    desc_value = desc_value[:197] + '...'
                # Add quotes for safety
                fixed_lines.append(f'description: "{desc_value}"')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Reconstruct file
    fixed_content = '---\n' + '\n'.join(fixed_lines) + '\n---' + body
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"  Fixed {filepath.name}")
    return True

def main():
    agent_dir = Path('.claude/agents')
    
    print("Fixing YAML frontmatter in agent files...")
    
    for agent_file in agent_dir.glob('*.md'):
        try:
            fix_agent_file(agent_file)
        except Exception as e:
            print(f"  Error fixing {agent_file.name}: {e}")
    
    print("\nAll agent files processed!")

if __name__ == '__main__':
    main()