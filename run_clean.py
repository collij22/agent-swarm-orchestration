#!/usr/bin/env python
"""
Clean orchestration runner - disables all conditional MCPs
Focuses on getting the core agent swarm working
"""

import sys
import os
import asyncio
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Disable ALL conditional MCPs to avoid API issues
os.environ['DISABLE_CONDITIONAL_MCPS'] = 'true'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Patch MCP loading BEFORE any imports
def disable_all_conditional_mcps():
    """Completely disable conditional MCP loading"""
    
    # 1. Patch mcp_conditional_loader
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "lib.mcp_conditional_loader",
        Path(__file__).parent / "lib" / "mcp_conditional_loader.py"
    )
    mcl = importlib.util.module_from_spec(spec)
    
    # Override methods to return empty
    mcl.MCPConditionalLoader.should_load_mcp = lambda *a, **k: []
    mcl.MCPConditionalLoader.analyze_and_activate_mcps = lambda *a, **k: set()
    mcl.MCPConditionalLoader._initialize_activation_rules = lambda *a: []
    
    spec.loader.exec_module(mcl)
    sys.modules['lib.mcp_conditional_loader'] = mcl
    
    # 2. Patch mcp_tools to return only basic tools
    spec2 = importlib.util.spec_from_file_location(
        "lib.mcp_tools",
        Path(__file__).parent / "lib" / "mcp_tools.py"
    )
    mcp_tools = importlib.util.module_from_spec(spec2)
    
    # Override tool creation
    mcp_tools.create_mcp_tools = lambda: []
    mcp_tools.get_conditional_mcp_tools = lambda *a: []
    
    spec2.loader.exec_module(mcp_tools)
    sys.modules['lib.mcp_tools'] = mcp_tools
    
    print("✓ Disabled all conditional MCPs")

# Apply patches
disable_all_conditional_mcps()

# Safe I/O wrapper
class SafeStream:
    def __init__(self, base):
        self.base = base
        self.encoding = 'utf-8'
        self.closed = False
        
    def write(self, text):
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            self.base.write(text)
            self.base.flush()
            return len(text) if text else 0
        except:
            return len(text) if text else 0
            
    def flush(self):
        try:
            self.base.flush()
        except:
            pass
            
    def close(self):
        pass
        
    def __getattr__(self, name):
        return getattr(self.base, name, lambda *a: None)

# Install safe I/O
sys.stdout = SafeStream(sys.stdout)
sys.stderr = SafeStream(sys.stderr)

# Now import orchestrate_enhanced
from orchestrate_enhanced import main

async def run_clean():
    """Run clean orchestration without MCPs"""
    
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
    
    print("=" * 70)
    print("🚀 CLEAN ORCHESTRATION RUNNER")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  • All conditional MCPs: DISABLED")
    print("  • Core agent swarm: ENABLED")
    print("  • Phase 1-5 features: ACTIVE")
    print()
    print("This run focuses on core functionality without MCP complications.")
    print()
    print("=" * 70)
    print()
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print()
        print("QuickShop MVP has been generated in:")
        print("  📁 projects/quickshop-mvp-test6")
        print()
        print("To run the application:")
        print("  1. cd projects/quickshop-mvp-test6")
        print("  2. docker-compose up")
        print("  3. Open http://localhost:3000")
        print()
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    try:
        asyncio.run(run_clean())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception:
        sys.exit(1)