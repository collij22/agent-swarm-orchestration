#!/usr/bin/env python
"""Fixed orchestrator that handles I/O issues"""

import sys
import os

# Set UTF-8 encoding first
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Disable MCP if requested
if os.environ.get('DISABLE_MCP_TOOLS'):
    os.environ['DISABLE_MCP'] = '1'

# Import the main orchestrator
import orchestrate_enhanced

# Monkey-patch the logger creation to handle I/O issues
original_create_new_session = orchestrate_enhanced.create_new_session

def safe_create_new_session(session_id, enable_human_log, summary_level):
    """Create session with I/O error handling"""
    try:
        return original_create_new_session(session_id, enable_human_log, summary_level)
    except Exception as e:
        print(f"Warning: Logger initialization failed ({e}), using fallback")
        # Return a dummy logger that won't crash
        class DummyLogger:
            def log_reasoning(self, *args, **kwargs): pass
            def log_agent_start(self, *args, **kwargs): pass
            def log_agent_end(self, *args, **kwargs): pass
            def log_tool_use(self, *args, **kwargs): pass
            def log_error(self, *args, **kwargs): pass
            def close_session(self, *args, **kwargs): pass
            def get_session_data(self, *args, **kwargs): return {}
            def __getattr__(self, name): return lambda *args, **kwargs: None
        return DummyLogger()

orchestrate_enhanced.create_new_session = safe_create_new_session

# Also patch Rich console if needed
try:
    from rich.console import Console
    orchestrate_enhanced.console = None  # Disable Rich console
    orchestrate_enhanced.HAS_RICH = False
except:
    pass

# Run the orchestrator
if __name__ == "__main__":
    import asyncio
    asyncio.run(orchestrate_enhanced.main())