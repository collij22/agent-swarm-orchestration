#!/usr/bin/env python
"""Production-ready orchestration runner with all fixes applied"""

import sys
import os
import io
import asyncio
from pathlib import Path

# Fix encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Disable problematic MCP tools that cause 400 errors
os.environ['DISABLE_MCP_BRAVE_SEARCH'] = 'true'
os.environ['DISABLE_MCP_FETCH'] = 'true'  # Disable if also causing issues

# Create bulletproof I/O streams
class SafeStream:
    """Stream that never closes and handles all errors"""
    
    def __init__(self, base_stream=None):
        self.base = base_stream or sys.__stdout__
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.closed = False
        
    def write(self, text):
        """Write with fallback"""
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
            
        # Try base stream
        try:
            if self.base and not getattr(self.base, 'closed', False):
                result = self.base.write(text)
                self.base.flush()
                return result
        except:
            pass
            
        # Try to print to terminal directly
        try:
            sys.__stdout__.write(text)
            sys.__stdout__.flush()
        except:
            pass
            
        return len(text) if text else 0
        
    def flush(self):
        """Flush safely"""
        try:
            if self.base:
                self.base.flush()
        except:
            pass
            
    def close(self):
        """Never close"""
        pass
        
    def fileno(self):
        """Return file descriptor"""
        try:
            return self.base.fileno()
        except:
            return 1
            
    def isatty(self):
        """Check if terminal"""
        try:
            return self.base.isatty()
        except:
            return False
            
    def __getattr__(self, name):
        """Delegate other methods"""
        return getattr(self.base, name, lambda *a, **k: None)

# Install safe streams immediately
sys.stdout = SafeStream(sys.stdout)
sys.stderr = SafeStream(sys.stderr)

# Patch Rich to be more resilient
def patch_rich():
    """Make Rich handle our safe streams"""
    try:
        from rich import console as rich_console
        
        if hasattr(rich_console, 'Console'):
            original_init = rich_console.Console.__init__
            
            def safe_console_init(self, *args, **kwargs):
                kwargs['file'] = sys.stdout
                kwargs['force_terminal'] = False
                kwargs['force_jupyter'] = False
                try:
                    original_init(self, *args, **kwargs)
                except:
                    # Fallback to basic console
                    self.print = lambda *a, **k: print(*[str(x) for x in a])
                    self.log = self.print
                    
            rich_console.Console.__init__ = safe_console_init
    except ImportError:
        pass

# Apply Rich patch
patch_rich()

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Patch MCP loading to skip problematic tools
def patch_mcp_loading():
    """Disable problematic MCP tools"""
    try:
        import lib.mcp_manager as mcp_manager
        
        original_load = mcp_manager.MCPManager.load_configs
        
        def filtered_load(self):
            """Load configs but skip problematic ones"""
            result = original_load(self)
            
            # Remove brave_search if it exists
            if hasattr(self, 'conditional_configs'):
                self.conditional_configs = {
                    k: v for k, v in self.conditional_configs.items()
                    if 'brave' not in k.lower()
                }
                
            return result
            
        mcp_manager.MCPManager.load_configs = filtered_load
    except:
        pass

# Apply MCP patch
patch_mcp_loading()

# Now import orchestrate_enhanced
from orchestrate_enhanced import main

async def run_production():
    """Run production orchestration"""
    # Set arguments
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test6',
        '--progress',
        '--summary-level', 'concise',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    print("=" * 60)
    print("Production Orchestration Runner")
    print("Full Phase 1-5 Implementation Active")
    print("=" * 60)
    print()
    print("Features enabled:")
    print("- File locking and coordination")
    print("- Agent verification and validation")  
    print("- Self-healing error recovery")
    print("- Automated debugging")
    print("- Real-time progress tracking")
    print()
    
    try:
        result = await main()
        print("\n" + "=" * 60)
        print("SUCCESS: Orchestration completed!")
        print("=" * 60)
        return result
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    try:
        # Run with asyncio
        asyncio.run(run_production())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1) 
    except Exception as e:
        print(f"\n\nFATAL: {e}")
        sys.exit(1)