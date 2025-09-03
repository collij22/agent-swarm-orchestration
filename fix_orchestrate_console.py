#!/usr/bin/env python
"""Fix orchestrate_enhanced.py console issues"""

import re

# Read the file
with open('orchestrate_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add safe_print function after imports
safe_print_func = '''
def safe_print(message, style=None):
    """Safe print that handles closed stdout"""
    try:
        if HAS_RICH and console and hasattr(console, 'file') and console.file and not console.file.closed:
            if isinstance(message, (Panel, Table)):
                console.print(message)
            elif style:
                console.print(f"[{style}]{message}[/{style}]")
            else:
                console.print(message)
        else:
            # Strip rich markup for plain print
            plain_msg = str(message)
            plain_msg = re.sub(r'\[.*?\]', '', plain_msg)
            print(plain_msg)
    except Exception:
        try:
            plain_msg = str(message)
            plain_msg = re.sub(r'\[.*?\]', '', plain_msg)
            print(plain_msg)
        except:
            pass  # Can't print at all
'''

# Find where to insert the safe_print function (after console initialization)
insert_pos = content.find('console = None')
if insert_pos != -1:
    # Find the end of the console initialization block
    next_class_pos = content.find('class EnhancedOrchestrator:', insert_pos)
    if next_class_pos != -1:
        # Insert before the class
        content = content[:next_class_pos] + safe_print_func + '\n\n' + content[next_class_pos:]

# Replace console.print calls with safe_print
content = re.sub(r'console\.print\((.*?)\)(\s*#.*)?$', r'safe_print(\1)', content, flags=re.MULTILINE)

# Handle multi-line console.print calls
content = re.sub(
    r'console\.print\(Panel\(([\s\S]*?)\)\)',
    r'safe_print(Panel(\1))',
    content
)

# Fix error handling in main function
content = re.sub(
    r'if HAS_RICH:\s*console\.print\((.*?)\)\s*else:\s*print\((.*?)\)',
    r'safe_print(\1)',
    content
)

# Write the fixed file
with open('orchestrate_enhanced_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Created orchestrate_enhanced_fixed.py with console fixes")