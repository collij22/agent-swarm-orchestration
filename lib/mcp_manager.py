#!/usr/bin/env python3
"""
MCP Manager - Unified interface for Model Context Protocol servers
Manages all MCP servers including conditional ones for the agent swarm
Enhanced with 7 new conditional MCPs for improved agent performance
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
from .mcp_conditional_loader import MCPConditionalLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerType(Enum):
    """Types of MCP servers supported"""
    SEMGREP = "semgrep"
    REF = "ref"
    PLAYWRIGHT = "playwright"
    # Conditional MCPs (only loaded when beneficial)
    FIRECRAWL = "firecrawl"
    STRIPE = "stripe"
    VERCEL = "vercel"
    BRAVE_SEARCH = "brave_search"
    FETCH = "fetch"

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
        
        # Initialize conditional loader
        self.conditional_loader = MCPConditionalLoader()
        self.conditional_mcps_active = set()
        
        # Load configuration
        self._load_config()
        
        # Initialize HTTP clients
        self._initialize_clients()
        
        # Add default configurations for conditional MCPs
        self._add_conditional_mcp_configs()
    
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
    
    def _add_conditional_mcp_configs(self):
        """Add default configurations for conditional MCPs"""
        conditional_configs = {
            'firecrawl': MCPServerConfig(
                name='Firecrawl MCP',
                type='firecrawl',
                url='http://localhost:3105',
                transport='http',
                config={
                    'command': 'npx',
                    'args': ['-y', '@firecrawl/mcp-server'],
                    'conditional': True,
                    'triggers': ['web_scraping', 'research', 'competitor_analysis']
                },
                enabled=False
            ),
            'stripe': MCPServerConfig(
                name='Stripe MCP',
                type='stripe',
                url='http://localhost:3106',
                transport='http',
                config={
                    'command': 'npx',
                    'args': ['-y', '@stripe/mcp-server'],
                    'conditional': True,
                    'triggers': ['payment', 'subscription', 'billing']
                },
                enabled=False
            ),
            'vercel': MCPServerConfig(
                name='Vercel MCP',
                type='vercel',
                url='http://localhost:3107',
                transport='http',
                config={
                    'command': 'npx',
                    'args': ['-y', '@vercel/mcp-server'],
                    'conditional': True,
                    'triggers': ['deployment', 'hosting', 'serverless']
                },
                enabled=False
            ),
            'brave_search': MCPServerConfig(
                name='Brave Search MCP',
                type='brave_search',
                url='http://localhost:3108',
                transport='http',
                config={
                    'command': 'npx',
                    'args': ['-y', '@brave/mcp-search-server'],
                    'conditional': True,
                    'triggers': ['research', 'troubleshooting', 'best_practices']
                },
                enabled=False
            ),
            'fetch': MCPServerConfig(
                name='Fetch MCP',
                type='fetch',
                url='http://localhost:3110',
                transport='http',
                config={
                    'command': 'npx',
                    'args': ['-y', '@smithery/mcp-fetch'],
                    'conditional': True,
                    'triggers': ['api_testing', 'webhook', 'http_request']
                },
                enabled=False
            )
        }
        
        # Add conditional configs if not already present
        for server_id, config in conditional_configs.items():
            if server_id not in self.servers:
                self.servers[server_id] = config
                logger.info(f"Added conditional MCP config: {server_id}")
    
    async def activate_conditional_mcps(self, 
                                       agent_name: str,
                                       requirements: Dict[str, Any],
                                       project_type: str = None) -> List[str]:
        """Activate conditional MCPs based on agent context
        
        Args:
            agent_name: Name of the agent requesting MCPs
            requirements: Project requirements dictionary
            project_type: Type of project (web_app, api_service, etc.)
            
        Returns:
            List of activated MCP names
        """
        # Get recommended MCPs from conditional loader
        recommended_mcps = self.conditional_loader.should_load_mcp(
            agent_name=agent_name,
            requirements=requirements,
            project_type=project_type
        )
        
        activated = []
        
        for mcp_name in recommended_mcps:
            if mcp_name in self.servers:
                # Enable the MCP
                self.servers[mcp_name].enabled = True
                
                # Initialize client if not already done
                if mcp_name not in self.clients:
                    timeout = httpx.Timeout(
                        connect=5.0,
                        read=30.0,
                        write=10.0,
                        pool=5.0
                    )
                    
                    self.clients[mcp_name] = httpx.AsyncClient(
                        base_url=self.servers[mcp_name].url,
                        timeout=timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    # Initialize metrics
                    self.metrics['calls'][mcp_name] = 0
                    self.metrics['tokens_saved'][mcp_name] = 0
                    self.metrics['cost_saved'][mcp_name] = 0.0
                    self.metrics['errors'][mcp_name] = 0
                
                activated.append(mcp_name)
                self.conditional_mcps_active.add(mcp_name)
                logger.info(f"Activated conditional MCP '{mcp_name}' for agent '{agent_name}'")
        
        return activated
    
    def get_active_mcps(self, include_conditional: bool = True) -> List[str]:
        """Get list of currently active MCPs
        
        Args:
            include_conditional: Whether to include conditional MCPs
            
        Returns:
            List of active MCP names
        """
        active = []
        
        for server_id, server in self.servers.items():
            if server.enabled:
                if include_conditional or not server.config.get('conditional', False):
                    active.append(server_id)
        
        return active
    
    def get_mcp_recommendations(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get MCP recommendations for a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of recommended MCPs with details
        """
        return self.conditional_loader.get_mcp_recommendations(agent_name)
    
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
        
        # Check if server is healthy before attempting connection
        if not self.health_status.get('ref', False):
            # Try a quick health check first
            try:
                health_response = await self.clients['ref'].get('/health', timeout=1.0)
                self.health_status['ref'] = health_response.status_code == 200
            except:
                self.health_status['ref'] = False
                logger.debug("Ref MCP server not available, using fallback mode")
                return MCPToolResult(
                    False, 
                    None, 
                    "Ref MCP server not running. Please run: python start_mcp_servers.py"
                )
        
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
                                                     headers=headers,
                                                     timeout=5.0)
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
            
        except httpx.ConnectError as e:
            # Connection refused - server not running
            self.health_status['ref'] = False
            self.metrics['errors']['ref'] += 1
            logger.debug(f"Ref MCP connection failed: {e}")
            return MCPToolResult(
                False, 
                None, 
                "Ref MCP server not running. Please run: python start_mcp_servers.py"
            )
        except httpx.TimeoutException as e:
            # Timeout - server might be overloaded
            self.metrics['errors']['ref'] += 1
            logger.warning(f"Ref search timeout: {e}")
            return MCPToolResult(False, None, "Ref MCP server timeout")
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
    
    # ==================== Playwright MCP Tools ====================
    
    async def playwright_screenshot(self,
                                url: str,
                                selector: str = None,
                                full_page: bool = False,
                                reasoning: str = None) -> MCPToolResult:
        """Take screenshot using Playwright MCP"""
        start_time = time.time()
        
        if 'playwright' not in self.clients:
            return MCPToolResult(False, None, "Playwright MCP not configured")
        
        try:
            payload = {
                'url': url,
                'selector': selector,
                'full_page': full_page,
                'reasoning': reasoning
            }
            
            response = await self.clients['playwright'].post('/screenshot', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['playwright'] += 1
            
            return MCPToolResult(
                success=True,
                data=result.get('screenshot_path', ''),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.metrics['errors']['playwright'] += 1
            logger.error(f"Screenshot failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def playwright_test(self,
                          url: str,
                          test_script: str,
                          reasoning: str = None) -> MCPToolResult:
        """Run browser test using Playwright MCP"""
        if 'playwright' not in self.clients:
            return MCPToolResult(False, None, "Playwright MCP not configured")
        
        try:
            payload = {
                'url': url,
                'test_script': test_script,
                'reasoning': reasoning
            }
            
            response = await self.clients['playwright'].post('/test', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return MCPToolResult(
                success=True,
                data=result.get('test_results', {}),
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Playwright test failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def playwright_compare_screenshots(self,
                                         baseline: str,
                                         current: str,
                                         threshold: float = 0.95) -> MCPToolResult:
        """Compare screenshots for visual regression testing"""
        if 'playwright' not in self.clients:
            return MCPToolResult(False, None, "Playwright MCP not configured")
        
        try:
            payload = {
                'baseline': baseline,
                'current': current,
                'threshold': threshold
            }
            
            response = await self.clients['playwright'].post('/compare', json=payload)
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
    
    # ==================== Conditional MCP Tools ====================
    
    async def firecrawl_scrape(self,
                              url: str,
                              selector: str = None,
                              depth: int = 1,
                              reasoning: str = None) -> MCPToolResult:
        """Scrape web content using Firecrawl MCP"""
        if 'firecrawl' not in self.clients:
            return MCPToolResult(False, None, "Firecrawl MCP not configured or not activated")
        
        try:
            payload = {
                'url': url,
                'selector': selector,
                'depth': depth,
                'reasoning': reasoning
            }
            
            response = await self.clients['firecrawl'].post('/scrape', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['firecrawl'] += 1
            
            return MCPToolResult(
                success=True,
                data=result.get('content', ''),
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            self.metrics['errors']['firecrawl'] += 1
            logger.error(f"Firecrawl scraping failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def stripe_payment(self,
                            action: str,
                            parameters: Dict[str, Any],
                            reasoning: str = None) -> MCPToolResult:
        """Handle Stripe payment operations"""
        if 'stripe' not in self.clients:
            return MCPToolResult(False, None, "Stripe MCP not configured or not activated")
        
        try:
            payload = {
                'action': action,
                'parameters': parameters,
                'reasoning': reasoning
            }
            
            # Add Stripe API key if configured
            stripe_key = os.getenv('STRIPE_API_KEY')
            if stripe_key:
                headers = {'Authorization': f'Bearer {stripe_key}'}
            else:
                headers = {}
            
            response = await self.clients['stripe'].post('/payment', 
                                                        json=payload,
                                                        headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['stripe'] += 1
            
            return MCPToolResult(
                success=True,
                data=result.get('response', {}),
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            self.metrics['errors']['stripe'] += 1
            logger.error(f"Stripe operation failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def vercel_deploy(self,
                           project_path: str,
                           config: Dict[str, Any] = None,
                           reasoning: str = None) -> MCPToolResult:
        """Deploy to Vercel using Vercel MCP"""
        if 'vercel' not in self.clients:
            return MCPToolResult(False, None, "Vercel MCP not configured or not activated")
        
        try:
            payload = {
                'project_path': project_path,
                'config': config or {},
                'reasoning': reasoning
            }
            
            # Add Vercel token if configured
            vercel_token = os.getenv('VERCEL_TOKEN')
            if vercel_token:
                headers = {'Authorization': f'Bearer {vercel_token}'}
            else:
                headers = {}
            
            response = await self.clients['vercel'].post('/deploy', 
                                                        json=payload,
                                                        headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['vercel'] += 1
            
            return MCPToolResult(
                success=True,
                data={
                    'deployment_url': result.get('url', ''),
                    'deployment_id': result.get('id', '')
                },
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            self.metrics['errors']['vercel'] += 1
            logger.error(f"Vercel deployment failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def brave_search(self,
                          query: str,
                          count: int = 5,
                          reasoning: str = None) -> MCPToolResult:
        """Search the web using Brave Search MCP"""
        if 'brave_search' not in self.clients:
            return MCPToolResult(False, None, "Brave Search MCP not configured or not activated")
        
        try:
            payload = {
                'query': query,
                'count': count,
                'reasoning': reasoning
            }
            
            # Add Brave API key if configured
            brave_key = os.getenv('BRAVE_API_KEY')
            if brave_key:
                headers = {'X-Subscription-Token': brave_key}
            else:
                headers = {}
            
            response = await self.clients['brave_search'].post('/search', 
                                                              json=payload,
                                                              headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['brave_search'] += 1
            
            return MCPToolResult(
                success=True,
                data=result.get('results', []),
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            self.metrics['errors']['brave_search'] += 1
            logger.error(f"Brave search failed: {e}")
            return MCPToolResult(False, None, str(e))
    
    async def fetch_request(self,
                          url: str,
                          method: str = 'GET',
                          headers: Dict = None,
                          body: Any = None,
                          reasoning: str = None) -> MCPToolResult:
        """Make HTTP request using Fetch MCP"""
        if 'fetch' not in self.clients:
            return MCPToolResult(False, None, "Fetch MCP not configured or not activated")
        
        try:
            payload = {
                'url': url,
                'method': method,
                'headers': headers or {},
                'body': body,
                'reasoning': reasoning
            }
            
            response = await self.clients['fetch'].post('/request', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Track metrics
            self.metrics['calls']['fetch'] += 1
            
            return MCPToolResult(
                success=True,
                data={
                    'status': result.get('status', 0),
                    'headers': result.get('headers', {}),
                    'body': result.get('body', '')
                },
                execution_time=result.get('execution_time', 0.0)
            )
            
        except Exception as e:
            self.metrics['errors']['fetch'] += 1
            logger.error(f"Fetch request failed: {e}")
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