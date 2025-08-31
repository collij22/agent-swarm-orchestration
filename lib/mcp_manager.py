#!/usr/bin/env python3
"""
MCP Manager - Unified interface for Model Context Protocol servers
Manages Semgrep, Ref, and Browser MCP servers for the agent swarm
"""

import os
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import httpx
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerType(Enum):
    """Types of MCP servers supported"""
    SEMGREP = "semgrep"
    REF = "ref"
    BROWSER = "browser"

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    type: str
    url: str
    transport: str
    config: Dict[str, Any]
    enabled: bool = True

@dataclass
class MCPToolResult:
    """Result from an MCP tool call"""
    success: bool
    data: Any
    error: Optional[str] = None
    cost: float = 0.0
    tokens_saved: int = 0
    execution_time: float = 0.0

class MCPManager:
    """Manages all MCP server connections and tool calls"""
    
    def __init__(self, config_path: str = None):
        """Initialize MCP Manager with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / '.claude' / 'mcp' / 'config.json'
        
        self.config_path = Path(config_path)
        self.servers: Dict[str, MCPServerConfig] = {}
        self.clients: Dict[str, httpx.AsyncClient] = {}
        self.health_status: Dict[str, bool] = {}
        self.metrics: Dict[str, Dict] = {
            'calls': {},
            'tokens_saved': {},
            'cost_saved': {},
            'errors': {}
        }
        
        # Load configuration
        self._load_config()
        
        # Initialize HTTP clients
        self._initialize_clients()
    
    def _load_config(self):
        """Load MCP configuration from file"""
        if not self.config_path.exists():
            logger.warning(f"MCP config not found at {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Parse server configurations
            for server_id, server_config in config.get('mcpServers', {}).items():
                self.servers[server_id] = MCPServerConfig(
                    name=server_config['name'],
                    type=server_config['type'],
                    url=server_config['url'],
                    transport=server_config['transport'],
                    config=server_config['config'],
                    enabled=server_config.get('enabled', True)
                )
            
            self.global_config = config.get('global', {})
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
    
    def _initialize_clients(self):
        """Initialize HTTP clients for each server"""
        for server_id, server in self.servers.items():
            if not server.enabled:
                continue
            
            # Create HTTP client with timeout
            timeout = httpx.Timeout(
                connect=5.0,
                read=30.0,
                write=10.0,
                pool=5.0
            )
            
            self.clients[server_id] = httpx.AsyncClient(
                base_url=server.url,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            # Initialize metrics
            self.metrics['calls'][server_id] = 0
            self.metrics['tokens_saved'][server_id] = 0
            self.metrics['cost_saved'][server_id] = 0.0
            self.metrics['errors'][server_id] = 0
    
    async def health_check(self, server_id: str = None) -> Dict[str, bool]:
        """Check health of MCP servers"""
        if server_id:
            servers_to_check = [server_id] if server_id in self.servers else []
        else:
            servers_to_check = list(self.servers.keys())
        
        health_results = {}
        
        for sid in servers_to_check:
            if sid not in self.clients:
                health_results[sid] = False
                continue
            
            try:
                response = await self.clients[sid].get('/health')
                health_results[sid] = response.status_code == 200
                self.health_status[sid] = health_results[sid]
            except Exception as e:
                logger.warning(f"Health check failed for {sid}: {e}")
                health_results[sid] = False
                self.health_status[sid] = False
        
        return health_results
    
    # ==================== Semgrep MCP Tools ====================
    
    async def semgrep_scan(self, 
                          file_path: str = None,
                          directory: str = None,
                          rules: List[str] = None,
                          reasoning: str = None) -> MCPToolResult:
        """Run Semgrep security scan on code"""
        start_time = time.time()
        
        if 'semgrep' not in self.clients:
            return MCPToolResult(False, None, "Semgrep MCP not configured")
        
        try:
            payload = {
                'file_path': file_path,
                'directory': directory or '.',
                'rules': rules or ['security', 'owasp'],
                'reasoning': reasoning
            }
            
            response = await self.clients['semgrep'].post('/scan', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['semgrep'] += 1
            
            return MCPToolResult(
                success=True,
                data=result.get('findings', []),
                tokens_saved=result.get('tokens_saved', 0),
                cost=0.0,  # Semgrep is free
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.metrics['errors']['semgrep'] += 1
            logger.error(f"Semgrep scan failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def semgrep_generate_report(self, 
                                     findings: List[Dict],
                                     format: str = "markdown") -> MCPToolResult:
        """Generate security report from Semgrep findings"""
        if 'semgrep' not in self.clients:
            return MCPToolResult(False, None, "Semgrep MCP not configured")
        
        try:
            payload = {
                'findings': findings,
                'format': format
            }
            
            response = await self.clients['semgrep'].post('/report', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return MCPToolResult(
                success=True,
                data=result.get('report', ''),
                cost=0.0
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    # ==================== Ref MCP Tools ====================
    
    @lru_cache(maxsize=100)
    async def ref_search(self,
                        query: str,
                        source: str = None,
                        max_results: int = 3,
                        reasoning: str = None) -> MCPToolResult:
        """Search documentation using Ref MCP"""
        start_time = time.time()
        
        if 'ref' not in self.clients:
            return MCPToolResult(False, None, "Ref MCP not configured")
        
        try:
            payload = {
                'query': query,
                'source': source,
                'max_results': max_results,
                'reasoning': reasoning
            }
            
            # Add API key if configured
            api_key = os.getenv('REF_MCP_API_KEY')
            if api_key:
                headers = {'Authorization': f'Bearer {api_key}'}
            else:
                headers = {}
            
            response = await self.clients['ref'].post('/search', 
                                                     json=payload,
                                                     headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Calculate cost savings (average 60% token reduction)
            tokens_before = len(query) * 10  # Estimate
            tokens_after = len(str(result.get('content', '')))
            tokens_saved = max(0, tokens_before - tokens_after)
            cost_saved = tokens_saved * 0.00003  # ~$0.03 per 1K tokens
            
            # Track metrics
            self.metrics['calls']['ref'] += 1
            self.metrics['tokens_saved']['ref'] += tokens_saved
            self.metrics['cost_saved']['ref'] += cost_saved
            
            return MCPToolResult(
                success=True,
                data=result.get('content', ''),
                tokens_saved=tokens_saved,
                cost=cost_saved,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.metrics['errors']['ref'] += 1
            logger.error(f"Ref search failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def ref_get_context(self,
                            technology: str,
                            topic: str,
                            reasoning: str = None) -> MCPToolResult:
        """Get specific documentation context"""
        if 'ref' not in self.clients:
            return MCPToolResult(False, None, "Ref MCP not configured")
        
        try:
            payload = {
                'technology': technology,
                'topic': topic,
                'reasoning': reasoning
            }
            
            response = await self.clients['ref'].post('/context', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Track token savings
            tokens_saved = result.get('tokens_saved', 0)
            cost_saved = tokens_saved * 0.00003
            
            self.metrics['tokens_saved']['ref'] += tokens_saved
            self.metrics['cost_saved']['ref'] += cost_saved
            
            return MCPToolResult(
                success=True,
                data=result.get('context', ''),
                tokens_saved=tokens_saved,
                cost=cost_saved
            )
            
        except Exception as e:
            logger.error(f"Context fetch failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    # ==================== Browser MCP Tools ====================
    
    async def browser_screenshot(self,
                                url: str,
                                selector: str = None,
                                full_page: bool = False,
                                reasoning: str = None) -> MCPToolResult:
        """Take screenshot using Browser MCP"""
        start_time = time.time()
        
        if 'browser' not in self.clients:
            return MCPToolResult(False, None, "Browser MCP not configured")
        
        try:
            payload = {
                'url': url,
                'selector': selector,
                'full_page': full_page,
                'reasoning': reasoning
            }
            
            response = await self.clients['browser'].post('/screenshot', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['browser'] += 1
            
            return MCPToolResult(
                success=True,
                data=result.get('screenshot_path', ''),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.metrics['errors']['browser'] += 1
            logger.error(f"Screenshot failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def browser_test(self,
                          url: str,
                          test_script: str,
                          reasoning: str = None) -> MCPToolResult:
        """Run browser test using Browser MCP"""
        if 'browser' not in self.clients:
            return MCPToolResult(False, None, "Browser MCP not configured")
        
        try:
            payload = {
                'url': url,
                'test_script': test_script,
                'reasoning': reasoning
            }
            
            response = await self.clients['browser'].post('/test', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return MCPToolResult(
                success=True,
                data=result.get('test_results', {}),
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Browser test failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def browser_compare_screenshots(self,
                                         baseline: str,
                                         current: str,
                                         threshold: float = 0.95) -> MCPToolResult:
        """Compare screenshots for visual regression testing"""
        if 'browser' not in self.clients:
            return MCPToolResult(False, None, "Browser MCP not configured")
        
        try:
            payload = {
                'baseline': baseline,
                'current': current,
                'threshold': threshold
            }
            
            response = await self.clients['browser'].post('/compare', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return MCPToolResult(
                success=True,
                data={
                    'match': result.get('match', False),
                    'similarity': result.get('similarity', 0.0),
                    'diff_path': result.get('diff_path', '')
                }
            )
            
        except Exception as e:
            logger.error(f"Screenshot comparison failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    # ==================== Utility Methods ====================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics for all MCP servers"""
        total_tokens_saved = sum(self.metrics['tokens_saved'].values())
        total_cost_saved = sum(self.metrics['cost_saved'].values())
        total_calls = sum(self.metrics['calls'].values())
        
        return {
            'total_calls': total_calls,
            'total_tokens_saved': total_tokens_saved,
            'total_cost_saved': total_cost_saved,
            'server_metrics': {
                server_id: {
                    'calls': self.metrics['calls'].get(server_id, 0),
                    'tokens_saved': self.metrics['tokens_saved'].get(server_id, 0),
                    'cost_saved': self.metrics['cost_saved'].get(server_id, 0),
                    'errors': self.metrics['errors'].get(server_id, 0),
                    'health': self.health_status.get(server_id, False)
                }
                for server_id in self.servers.keys()
            }
        }
    
    def reset_metrics(self):
        """Reset usage metrics"""
        for metric_type in self.metrics.values():
            for key in metric_type.keys():
                if isinstance(metric_type[key], (int, float)):
                    metric_type[key] = 0
    
    async def close(self):
        """Close all HTTP clients"""
        for client in self.clients.values():
            await client.aclose()

# Singleton instance
_mcp_manager = None

def get_mcp_manager() -> MCPManager:
    """Get or create the singleton MCP manager"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager

# Example usage
if __name__ == "__main__":
    async def demo():
        manager = get_mcp_manager()
        
        # Check health
        health = await manager.health_check()
        print(f"Health status: {health}")
        
        # Example Ref search
        result = await manager.ref_search(
            query="How to create a React component with TypeScript",
            source="react",
            reasoning="Need to understand React + TypeScript patterns"
        )
        if result.success:
            print(f"Documentation found: {result.data[:200]}...")
            print(f"Tokens saved: {result.tokens_saved}")
            print(f"Cost saved: ${result.cost:.4f}")
        
        # Get metrics
        metrics = manager.get_metrics()
        print(f"Total metrics: {metrics}")
        
        await manager.close()
    
    asyncio.run(demo())