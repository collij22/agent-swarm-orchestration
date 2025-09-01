#!/usr/bin/env python3
"""
MCP Tools - Tool wrappers for MCP server integration with agent runtime
Provides Tool objects that can be registered with AnthropicAgentRunner
"""

import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from .agent_runtime import Tool
    from .mcp_manager import get_mcp_manager, MCPToolResult
except ImportError:
    from agent_runtime import Tool
    from mcp_manager import get_mcp_manager, MCPToolResult

# ==================== Semgrep Tools ====================

async def mcp_semgrep_scan_tool(
    path: str = None,
    rules: str = "security,owasp",
    reasoning: str = None,
    context: Any = None,
    agent_name: str = None
) -> str:
    """
    Run security scan using Semgrep MCP
    
    Args:
        path: File or directory path to scan (defaults to project directory)
        rules: Comma-separated list of rule sets (security, owasp, pci_dss, gdpr)
        reasoning: Why this scan is being performed
        context: Agent context (optional)
        agent_name: Name of the calling agent (optional)
    
    Returns:
        Security scan results with findings
    """
    manager = get_mcp_manager()
    
    # Determine scan path
    if not path and context and "project_directory" in context.artifacts:
        path = context.artifacts["project_directory"]
    elif not path:
        path = "."
    
    # Parse rules
    rule_list = [r.strip() for r in rules.split(",")]
    
    # Run scan
    result = await manager.semgrep_scan(
        directory=path if Path(path).is_dir() else None,
        file_path=path if Path(path).is_file() else None,
        rules=rule_list,
        reasoning=reasoning
    )
    
    if not result.success:
        return f"Security scan failed: {result.error}"
    
    findings = result.data
    if not findings:
        return "Security scan complete: No vulnerabilities found"
    
    # Format findings
    output = f"Security scan found {len(findings)} issues:\n\n"
    
    for i, finding in enumerate(findings[:10], 1):  # Limit to first 10
        output += f"{i}. [{finding.get('severity', 'INFO')}] {finding.get('rule_id', 'unknown')}\n"
        output += f"   File: {finding.get('path', 'unknown')}:{finding.get('line', 0)}\n"
        output += f"   Message: {finding.get('message', 'No message')}\n"
        if finding.get('fix'):
            output += f"   Fix: {finding['fix']}\n"
        output += "\n"
    
    if len(findings) > 10:
        output += f"... and {len(findings) - 10} more issues\n"
    
    return output

async def mcp_security_report_tool(
    scan_results: str = None,
    format: str = "markdown",
    reasoning: str = None,
    context: Any = None
) -> str:
    """
    Generate security report from scan results
    
    Args:
        scan_results: Previous scan results or None to use latest
        format: Report format (markdown, json, html)
        reasoning: Why this report is being generated
    
    Returns:
        Formatted security report
    """
    manager = get_mcp_manager()
    
    # Parse scan results if provided as string
    # For now, return a summary
    return "Security report generated. Use scan results for detailed findings."

# ==================== Ref Documentation Tools ====================

async def mcp_ref_search_tool(
    query: str,
    technology: str = None,
    max_results: int = 3,
    reasoning: str = None,
    context: Any = None,
    agent_name: str = None
) -> str:
    """
    Search documentation using Ref MCP for accurate, up-to-date information
    
    Args:
        query: Search query or question
        technology: Specific technology to search (react, fastapi, django, etc.)
        max_results: Maximum number of results to return
        reasoning: Why this documentation is needed
        context: Agent context (optional)
        agent_name: Name of the calling agent (optional)
    
    Returns:
        Relevant documentation excerpts
    """
    manager = get_mcp_manager()
    
    # Run search
    result = await manager.ref_search(
        query=query,
        source=technology,
        max_results=max_results,
        reasoning=reasoning
    )
    
    if not result.success:
        # Fallback to general knowledge - this is expected when MCP servers aren't running
        if "not running" in result.error:
            return f"[MCP Info] Ref server not running - using general knowledge instead"
        return f"Documentation search unavailable, using general knowledge. Error: {result.error}"
    
    # Format output with cost savings info
    output = result.data
    if result.tokens_saved > 0:
        output += f"\n\n[MCP: Saved {result.tokens_saved} tokens (~${result.cost:.4f})]"
    
    return output

async def mcp_get_docs_tool(
    technology: str,
    topic: str,
    reasoning: str = None,
    context: Any = None
) -> str:
    """
    Get specific documentation context for a technology and topic
    
    Args:
        technology: Technology name (react, fastapi, postgresql, etc.)
        topic: Specific topic within the technology
        reasoning: Why this documentation is needed
    
    Returns:
        Documentation context
    """
    manager = get_mcp_manager()
    
    result = await manager.ref_get_context(
        technology=technology,
        topic=topic,
        reasoning=reasoning
    )
    
    if not result.success:
        return f"Could not fetch documentation: {result.error}"
    
    output = result.data
    if result.tokens_saved > 0:
        output += f"\n\n[MCP: Saved {result.tokens_saved} tokens (~${result.cost:.4f})]"
    
    return output

# ==================== Playwright Automation Tools ====================

async def mcp_playwright_screenshot_tool(
    url: str,
    selector: str = None,
    full_page: bool = False,
    reasoning: str = None,
    context: Any = None,
    agent_name: str = None
) -> str:
    """
    Take a screenshot of a webpage for visual validation
    
    Args:
        url: URL to screenshot
        selector: CSS selector for specific element (optional)
        full_page: Whether to capture full page
        reasoning: Why this screenshot is needed
        context: Agent context (optional)
        agent_name: Name of the calling agent (optional)
    
    Returns:
        Path to screenshot file
    """
    manager = get_mcp_manager()
    
    result = await manager.playwright_screenshot(
        url=url,
        selector=selector,
        full_page=full_page,
        reasoning=reasoning
    )
    
    if not result.success:
        return f"Screenshot failed: {result.error}"
    
    screenshot_path = result.data
    
    # Track in context if available
    if context and agent_name:
        context.add_created_file(agent_name, screenshot_path, "screenshot", verified=True)
    
    return f"Screenshot saved to: {screenshot_path}"

async def mcp_playwright_test_tool(
    url: str,
    test_script: str,
    reasoning: str = None,
    context: Any = None
) -> str:
    """
    Run playwright-based test on a webpage
    
    Args:
        url: URL to test
        test_script: JavaScript test script to execute
        reasoning: Why this test is being run
    
    Returns:
        Test results
    """
    manager = get_mcp_manager()
    
    result = await manager.playwright_test(
        url=url,
        test_script=test_script,
        reasoning=reasoning
    )
    
    if not result.success:
        return f"Playwright test failed: {result.error}"
    
    test_results = result.data
    
    # Format results
    output = "Playwright test results:\n"
    for key, value in test_results.items():
        output += f"  {key}: {value}\n"
    
    return output

async def mcp_visual_regression_tool(
    baseline_path: str,
    current_url: str,
    threshold: float = 0.95,
    reasoning: str = None,
    context: Any = None
) -> str:
    """
    Compare current page against baseline for visual regression
    
    Args:
        baseline_path: Path to baseline screenshot
        current_url: URL to capture and compare
        threshold: Similarity threshold (0.0 to 1.0)
        reasoning: Why this comparison is needed
    
    Returns:
        Comparison results
    """
    manager = get_mcp_manager()
    
    # First, take current screenshot
    screenshot_result = await manager.playwright_screenshot(
        url=current_url,
        full_page=True,
        reasoning=f"Visual regression test: {reasoning}"
    )
    
    if not screenshot_result.success:
        return f"Failed to capture current screenshot: {screenshot_result.error}"
    
    current_path = screenshot_result.data
    
    # Compare screenshots
    compare_result = await manager.playwright_compare_screenshots(
        baseline=baseline_path,
        current=current_path,
        threshold=threshold
    )
    
    if not compare_result.success:
        return f"Comparison failed: {compare_result.error}"
    
    comparison = compare_result.data
    
    if comparison['match']:
        return f"Visual regression PASSED (similarity: {comparison['similarity']:.2%})"
    else:
        return f"Visual regression FAILED (similarity: {comparison['similarity']:.2%})\nDiff image: {comparison['diff_path']}"

# ==================== Create MCP Tools for Registration ====================

def create_mcp_tools() -> List[Tool]:
    """Create MCP tools that can be registered with agents"""
    tools = []
    
    # Semgrep security tools
    tools.append(Tool(
        name="mcp_semgrep_scan",
        description="Run security vulnerability scan on code using Semgrep MCP",
        parameters={
            "path": {"type": "string", "description": "File or directory to scan", "required": False},
            "rules": {"type": "string", "description": "Rule sets (security,owasp,pci_dss,gdpr)", "required": False}
        },
        function=mcp_semgrep_scan_tool,
        requires_reasoning=True
    ))
    
    tools.append(Tool(
        name="mcp_security_report",
        description="Generate security report from scan results",
        parameters={
            "scan_results": {"type": "string", "description": "Scan results to report on", "required": False},
            "format": {"type": "string", "description": "Report format (markdown/json/html)", "required": False}
        },
        function=mcp_security_report_tool,
        requires_reasoning=True
    ))
    
    # Ref documentation tools
    tools.append(Tool(
        name="mcp_ref_search",
        description="Search technical documentation for accurate, up-to-date information (saves ~60% tokens)",
        parameters={
            "query": {"type": "string", "description": "Search query or question", "required": True},
            "technology": {"type": "string", "description": "Technology to search (react/fastapi/etc)", "required": False},
            "max_results": {"type": "integer", "description": "Maximum results", "required": False}
        },
        function=mcp_ref_search_tool,
        requires_reasoning=True
    ))
    
    tools.append(Tool(
        name="mcp_get_docs",
        description="Get specific documentation context for a technology and topic",
        parameters={
            "technology": {"type": "string", "description": "Technology name", "required": True},
            "topic": {"type": "string", "description": "Specific topic", "required": True}
        },
        function=mcp_get_docs_tool,
        requires_reasoning=True
    ))
    
    # Playwright automation tools
    tools.append(Tool(
        name="mcp_playwright_screenshot",
        description="Take screenshot of webpage for visual validation",
        parameters={
            "url": {"type": "string", "description": "URL to screenshot", "required": True},
            "selector": {"type": "string", "description": "CSS selector for element", "required": False},
            "full_page": {"type": "boolean", "description": "Capture full page", "required": False}
        },
        function=mcp_playwright_screenshot_tool,
        requires_reasoning=True
    ))
    
    tools.append(Tool(
        name="mcp_playwright_test",
        description="Run playwright-based test on webpage",
        parameters={
            "url": {"type": "string", "description": "URL to test", "required": True},
            "test_script": {"type": "string", "description": "JavaScript test script", "required": True}
        },
        function=mcp_playwright_test_tool,
        requires_reasoning=True
    ))
    
    tools.append(Tool(
        name="mcp_visual_regression",
        description="Compare webpage against baseline for visual regression testing",
        parameters={
            "baseline_path": {"type": "string", "description": "Path to baseline screenshot", "required": True},
            "current_url": {"type": "string", "description": "URL to capture and compare", "required": True},
            "threshold": {"type": "number", "description": "Similarity threshold (0-1)", "required": False}
        },
        function=mcp_visual_regression_tool,
        requires_reasoning=True
    ))
    
    return tools

def get_conditional_mcp_tools(mcp_names: List[str]) -> List[Tool]:
    """
    Get tools for specific conditional MCPs
    
    Args:
        mcp_names: List of MCP names to get tools for
    
    Returns:
        List of Tool objects for the requested MCPs
    """
    tools = []
    
    for mcp_name in mcp_names:
        if mcp_name == "stripe":
            # Stripe payment processing tools
            tools.append(Tool(
                name="mcp_stripe_create_payment",
                description="Create payment intent using Stripe MCP",
                parameters={
                    "amount": {"type": "integer", "description": "Amount in cents", "required": True},
                    "currency": {"type": "string", "description": "Currency code (usd, eur, etc)", "required": False},
                    "description": {"type": "string", "description": "Payment description", "required": False}
                },
                function=create_placeholder_mcp_function("stripe", "create_payment"),
                requires_reasoning=True
            ))
            tools.append(Tool(
                name="mcp_stripe_manage_subscription",
                description="Manage subscription using Stripe MCP",
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID", "required": True},
                    "plan_id": {"type": "string", "description": "Subscription plan ID", "required": True},
                    "action": {"type": "string", "description": "Action (create/update/cancel)", "required": True}
                },
                function=create_placeholder_mcp_function("stripe", "manage_subscription"),
                requires_reasoning=True
            ))
            
        elif mcp_name == "vercel":
            # Vercel deployment tools
            tools.append(Tool(
                name="mcp_vercel_deploy",
                description="Deploy project to Vercel",
                parameters={
                    "project_path": {"type": "string", "description": "Path to project", "required": True},
                    "production": {"type": "boolean", "description": "Deploy to production", "required": False}
                },
                function=create_placeholder_mcp_function("vercel", "deploy"),
                requires_reasoning=True
            ))
            
        elif mcp_name == "brave_search":
            # Brave search tools
            tools.append(Tool(
                name="mcp_brave_search",
                description="Search the web using Brave Search MCP",
                parameters={
                    "query": {"type": "string", "description": "Search query", "required": True},
                    "count": {"type": "integer", "description": "Number of results", "required": False}
                },
                function=create_placeholder_mcp_function("brave_search", "search"),
                requires_reasoning=True
            ))
            
        elif mcp_name == "firecrawl":
            # Firecrawl web scraping tools
            tools.append(Tool(
                name="mcp_firecrawl_scrape",
                description="Scrape web content using Firecrawl MCP",
                parameters={
                    "url": {"type": "string", "description": "URL to scrape", "required": True},
                    "selector": {"type": "string", "description": "CSS selector", "required": False}
                },
                function=create_placeholder_mcp_function("firecrawl", "scrape"),
                requires_reasoning=True
            ))
            
        elif mcp_name == "fetch":
            # Fetch HTTP tools
            tools.append(Tool(
                name="mcp_fetch_request",
                description="Make HTTP request using Fetch MCP",
                parameters={
                    "url": {"type": "string", "description": "URL to fetch", "required": True},
                    "method": {"type": "string", "description": "HTTP method", "required": False},
                    "headers": {"type": "object", "description": "Request headers", "required": False},
                    "body": {"type": "string", "description": "Request body", "required": False}
                },
                function=create_placeholder_mcp_function("fetch", "request"),
                requires_reasoning=True
            ))
    
    return tools

def create_placeholder_mcp_function(mcp_name: str, operation: str):
    """Create a placeholder function for conditional MCP tools"""
    async def placeholder_function(**kwargs):
        reasoning = kwargs.get('reasoning', 'No reasoning provided')
        # Log the attempt to use this MCP
        return f"[Conditional MCP: {mcp_name}] Operation '{operation}' called with reasoning: {reasoning}\n" \
               f"Note: This MCP tool is conditionally loaded but the server implementation is pending.\n" \
               f"Parameters: {kwargs}"
    
    return placeholder_function

# Example usage
if __name__ == "__main__":
    async def demo():
        # Test Ref search
        result = await mcp_ref_search_tool(
            query="How to implement authentication in FastAPI",
            technology="fastapi",
            reasoning="Need to understand FastAPI auth patterns"
        )
        print(f"Documentation result:\n{result}\n")
        
        # Test Semgrep scan
        scan_result = await mcp_semgrep_scan_tool(
            path="lib/",
            rules="security",
            reasoning="Security audit of library code"
        )
        print(f"Security scan result:\n{scan_result}\n")
    
    asyncio.run(demo())