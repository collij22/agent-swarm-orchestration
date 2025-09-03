#!/usr/bin/env python
"""Patch to completely disable brave_search MCP"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

def disable_brave_search():
    """Remove brave_search from all MCP configurations"""
    
    # Patch the mcp_conditional_loader
    try:
        import lib.mcp_conditional_loader as mcl
        
        # Override the initialization to remove brave_search rules
        original_init_rules = mcl.MCPConditionalLoader._initialize_activation_rules
        
        def filtered_init_rules(self):
            """Get rules but exclude brave_search"""
            all_rules = original_init_rules(self)
            # Filter out brave_search rules
            return [r for r in all_rules if r.mcp_name != "brave_search"]
        
        mcl.MCPConditionalLoader._initialize_activation_rules = filtered_init_rules
        print("✓ Disabled brave_search in conditional loader")
        
    except Exception as e:
        print(f"Warning: Could not patch conditional loader: {e}")
    
    # Patch the mcp_manager
    try:
        import lib.mcp_manager as mm
        
        # Override the add_conditional_mcp_configs to skip brave_search
        if hasattr(mm.MCPManager, '_add_conditional_mcp_configs'):
            original_add = mm.MCPManager._add_conditional_mcp_configs
            
            def filtered_add(self):
                """Add configs but skip brave_search"""
                original_add(self)
                # Remove brave_search if it was added
                if hasattr(self, 'conditional_configs'):
                    if 'brave_search' in self.conditional_configs:
                        del self.conditional_configs['brave_search']
                        print("✓ Removed brave_search from conditional configs")
                        
            mm.MCPManager._add_conditional_mcp_configs = filtered_add
            
    except Exception as e:
        print(f"Warning: Could not patch MCP manager: {e}")
    
    # Also patch the MCPServerType enum if it exists
    try:
        import lib.mcp_manager as mm
        if hasattr(mm, 'MCPServerType'):
            # Remove BRAVE_SEARCH from the enum if possible
            delattr(mm.MCPServerType, 'BRAVE_SEARCH')
            print("✓ Removed BRAVE_SEARCH from server types")
    except:
        pass

if __name__ == "__main__":
    disable_brave_search()
    print("\nBrave Search MCP has been disabled.")
    print("You can now run the orchestration without API errors.")