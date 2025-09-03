#!/usr/bin/env python
"""Run orchestration with output redirected to file"""

import sys
import os
import datetime

# Create a log file
log_filename = f"orchestrate_output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_file = open(log_filename, 'w', encoding='utf-8')

# Redirect stdout and stderr to the log file
sys.stdout = log_file
sys.stderr = log_file

print(f"Starting orchestration at {datetime.datetime.now()}")
print(f"Arguments: full_stack_api quickshop-mvp-test5")
print("="*60)

# Add the project root to path
sys.path.insert(0, r'C:\AI projects\1test')

# Disable Rich console
os.environ['DISABLE_RICH_CONSOLE'] = '1'

# Now run the orchestration
try:
    from orchestrate_enhanced import main
    import asyncio
    
    # Set the arguments
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test5',
        '--progress',
        '--summary-level', 'concise',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    # Run it
    asyncio.run(main())
    print("\nOrchestration completed successfully!")
    
except Exception as e:
    print(f"\nError running orchestration: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    log_file.close()
    
# Print to actual stdout (terminal) that log was created
import sys
sys.stdout = sys.__stdout__
print(f"\nOrchestration output saved to: {log_filename}")