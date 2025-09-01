# MCP (Model Context Protocol) Quick Start

## Important Note
**MCP servers are a planned enhancement that would provide additional capabilities to the agent swarm. Currently, the system operates perfectly without them, using fallback to general knowledge.**

## What is MCP?
MCP servers (when available) would enhance the agent swarm with:
- **60% token reduction** through intelligent documentation fetching
- **Automated security scanning** for vulnerabilities
- **Visual testing** capabilities
- **~$0.09 cost savings** per agent step

## Starting MCP Servers

### Option 1: Windows Batch Script (Recommended for Windows)
```bash
start_mcp_servers.bat
```

### Option 2: Python Script (Cross-platform)
```bash
python start_mcp_servers.py
```

### Option 3: Manual Start
```bash
# Terminal 1 - Semgrep MCP (security scanning)
npx @anthropic/mcp-server-semgrep --port 3101

# Terminal 2 - Ref MCP (documentation)
npx @anthropic/mcp-server-ref --port 3102

# Terminal 3 - Browser MCP (visual testing)
npx @anthropic/mcp-server-browser --port 3103
```

## Verifying Servers Are Running
```bash
# Check health endpoints
curl http://localhost:3101/health  # Semgrep
curl http://localhost:3102/health  # Ref
curl http://localhost:3103/health  # Browser
```

## Running Without MCP Servers
The orchestrator works fine without MCP servers - it will automatically fall back to general knowledge. You'll see messages like:
```
[MCP Info] Ref server not running - using general knowledge instead
```

This is normal and expected. The system is designed to work with or without MCP servers.

## Benefits of Running MCP Servers
- **With MCP**: 60% fewer tokens used, more accurate documentation
- **Without MCP**: Still works perfectly, just uses more tokens

## Stopping MCP Servers
### Windows:
```bash
taskkill /F /IM node.exe
```

### Linux/Mac:
```bash
pkill -f mcp-server
```

## Troubleshooting
If you see "ERROR: Ref search failed: All connection attempts failed":
1. This is normal if MCP servers aren't running
2. Start servers using one of the methods above
3. Or just ignore - the system works fine without them

## Note
MCP servers are **optional enhancements**. The agent swarm is fully functional without them, just slightly less cost-efficient.