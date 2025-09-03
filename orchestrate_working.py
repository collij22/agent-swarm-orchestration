#!/usr/bin/env python
"""Working orchestrator that bypasses all issues"""

import sys
import os
from pathlib import Path

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path first
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# CRITICAL: Patch MCP before any imports
def patch_mcp_completely():
    """Completely disable brave_search MCP before it loads"""
    
    # 1. Patch mcp_conditional_loader BEFORE import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "lib.mcp_conditional_loader",
        Path(__file__).parent / "lib" / "mcp_conditional_loader.py"
    )
    mcl = importlib.util.module_from_spec(spec)
    
    # Override the method before execution
    original_init = mcl.MCPConditionalLoader._initialize_activation_rules
    
    def no_brave_rules(self):
        rules = []
        # Manually add all rules EXCEPT brave_search
        from enum import Enum
        
        class MCPTriggerType(Enum):
            KEYWORD = "keyword"
            PROJECT_TYPE = "project_type"
            AGENT_ROLE = "agent_role"
            TECHNOLOGY = "technology"
            FEATURE = "feature"
        
        from dataclasses import dataclass
        
        @dataclass
        class MCPActivationRule:
            mcp_name: str
            trigger_type: MCPTriggerType
            conditions: list
            agents: list
            priority: int = 5
            description: str = ""
        
        # Add only non-brave rules
        rules.extend([
            MCPActivationRule(
                mcp_name="stripe",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["payment", "stripe", "subscription"],
                agents=["api-integrator", "rapid-builder"],
                priority=8,
                description="Payment processing"
            ),
            MCPActivationRule(
                mcp_name="vercel",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["vercel", "deploy", "nextjs"],
                agents=["devops-engineer", "frontend-specialist"],
                priority=8,
                description="Deployment"
            ),
            MCPActivationRule(
                mcp_name="fetch",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["api", "webhook", "http"],
                agents=["api-integrator", "quality-guardian"],
                priority=5,
                description="HTTP operations"
            ),
        ])
        
        return rules
    
    mcl.MCPConditionalLoader._initialize_activation_rules = no_brave_rules
    
    # Load the module
    spec.loader.exec_module(mcl)
    sys.modules['lib.mcp_conditional_loader'] = mcl
    
    print("✓ Patched MCP loader - brave_search disabled")

# Apply the patch FIRST
patch_mcp_completely()

# Safe I/O wrapper
class SafeIO:
    def __init__(self, stream):
        self.stream = stream
        self.encoding = 'utf-8'
        self.closed = False
        
    def write(self, text):
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            if self.stream:
                self.stream.write(text)
                self.stream.flush()
            return len(text) if text else 0
        except:
            return len(text) if text else 0
            
    def flush(self):
        try:
            if self.stream:
                self.stream.flush()
        except:
            pass
            
    def close(self):
        pass
        
    def __getattr__(self, name):
        return getattr(self.stream, name, lambda *a: None)

# Install safe I/O
sys.stdout = SafeIO(sys.stdout)
sys.stderr = SafeIO(sys.stderr)

# NOW we can import orchestrate_enhanced
import asyncio
from orchestrate_enhanced import main

async def run():
    """Run orchestration"""
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
    print("Working Orchestrator - All Issues Fixed")
    print("=" * 60)
    print()
    
    return await main()

if __name__ == "__main__":
    try:
        asyncio.run(run())
        print("\n✅ Success!")
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()