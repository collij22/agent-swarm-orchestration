#!/usr/bin/env python
"""Patch orchestrate_enhanced.py to remove all Rich console usage"""

import re

# Read the file
with open('orchestrate_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Comment out Rich imports
content = re.sub(
    r'^(\s*from rich.*import.*)',
    r'#\1  # Disabled Rich',
    content,
    flags=re.MULTILINE
)

# Set HAS_RICH to False
content = re.sub(
    r'HAS_RICH = True',
    'HAS_RICH = False',
    content
)

# Replace console creation
content = re.sub(
    r'console = Console\(.*?\)',
    'console = None',
    content
)

# Save patched version
with open('orchestrate_enhanced_patched.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Created orchestrate_enhanced_patched.py without Rich console")
print("\nRun it with:")
print("python orchestrate_enhanced_patched.py --project-type full_stack_api --requirements projects/quickshop-mvp-test/requirements.yaml --output-dir projects/quickshop-mvp-test6 --progress --max-parallel 2 --human-log --summary-level concise")