#!/usr/bin/env python
"""
Final Production Orchestration Runner
With brave_search MCP disabled in source files
"""

import sys
import os
import asyncio
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Create persistent I/O streams
class PersistentStream:
    """Stream that never closes"""
    def __init__(self, base):
        self.base = base
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.closed = False
        
    def write(self, text):
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            self.base.write(text)
            self.base.flush()
            return len(text) if text else 0
        except:
            try:
                sys.__stdout__.write(text)
            except:
                pass
            return len(text) if text else 0
            
    def flush(self):
        try:
            self.base.flush()
        except:
            pass
            
    def close(self):
        pass  # Never close
        
    def __getattr__(self, name):
        return getattr(self.base, name, lambda *a: None)

# Replace stdout/stderr
sys.stdout = PersistentStream(sys.stdout)
sys.stderr = PersistentStream(sys.stderr)

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Import orchestrate_enhanced
from orchestrate_enhanced import main

async def run_orchestration():
    """Run the orchestration"""
    
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
    print("🚀 QUICKSHOP MVP ORCHESTRATION")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  • Project: Full Stack E-Commerce API")
    print("  • Output: projects/quickshop-mvp-test6")
    print("  • Agents: 15-agent swarm with Phase 1-5 enhancements")
    print("  • Features: File locking, validation, self-healing, debugging")
    print()
    print("Note: brave_search MCP has been disabled (API compatibility)")
    print()
    print("=" * 70)
    print()
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! QuickShop MVP has been generated!")
        print("=" * 70)
        print()
        print("📁 Output Location: projects/quickshop-mvp-test6")
        print()
        print("Next Steps:")
        print("1. cd projects/quickshop-mvp-test6")
        print("2. docker-compose up")
        print("3. Open http://localhost:3000 (frontend)")
        print("4. API available at http://localhost:8000")
        print()
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nTroubleshooting:")
        print("• Verify ANTHROPIC_API_KEY is set")
        print("• Check network connectivity")
        print("• Review the error details above")
        
        raise

if __name__ == "__main__":
    try:
        asyncio.run(run_orchestration())
    except KeyboardInterrupt:
        print("\n\n⚠️ Orchestration interrupted by user")
        sys.exit(1)
    except Exception:
        sys.exit(1)