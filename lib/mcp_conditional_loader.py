#!/usr/bin/env python3
"""
MCP Conditional Loader - Intelligent MCP activation based on project context
Only loads MCPs when they provide clear value for the specific task
"""

import json
import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPTriggerType(Enum):
    """Types of triggers that can activate an MCP"""
    KEYWORD = "keyword"          # Requirement contains specific keywords
    PROJECT_TYPE = "project_type"  # Specific project types
    AGENT_ROLE = "agent_role"    # Specific agent requesting
    TECHNOLOGY = "technology"     # Technology stack mentions
    FEATURE = "feature"          # Feature requirements

@dataclass
class MCPActivationRule:
    """Rule for activating an MCP"""
    mcp_name: str
    trigger_type: MCPTriggerType
    conditions: List[str]
    agents: List[str]  # Which agents can use this MCP
    priority: int = 5  # 1-10, higher = more likely to activate
    description: str = ""

class MCPConditionalLoader:
    """Loads MCP tools only when beneficial for the task"""
    
    def __init__(self):
        """Initialize the conditional loader with activation rules"""
        self.activation_rules = self._initialize_activation_rules()
        self.active_mcps: Set[str] = set()
        self.mcp_usage_stats: Dict[str, Dict] = {}
        
    def _initialize_activation_rules(self) -> List[MCPActivationRule]:
        """Define activation rules for each conditional MCP"""
        return [
            # Stripe MCP Rules
            MCPActivationRule(
                mcp_name="stripe",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["payment", "stripe", "subscription", "billing", "invoice", "checkout", "customer"],
                agents=["api-integrator", "rapid-builder"],
                priority=8,
                description="Payment processing integration"
            ),
            MCPActivationRule(
                mcp_name="stripe",
                trigger_type=MCPTriggerType.PROJECT_TYPE,
                conditions=["ecommerce", "saas", "marketplace"],
                agents=["api-integrator"],
                priority=7
            ),
            
            # Vercel MCP Rules
            MCPActivationRule(
                mcp_name="vercel",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["vercel", "deploy", "serverless", "edge", "nextjs", "next.js"],
                agents=["devops-engineer", "frontend-specialist"],
                priority=8,
                description="Deployment and hosting automation"
            ),
            MCPActivationRule(
                mcp_name="vercel",
                trigger_type=MCPTriggerType.PROJECT_TYPE,
                conditions=["web_app", "frontend", "nextjs"],
                agents=["devops-engineer"],
                priority=6
            ),
            
            # SQLite MCP Rules
            MCPActivationRule(
                mcp_name="sqlite",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["sqlite", "local", "prototype", "mvp", "poc", "demo", "lightweight"],
                agents=["database-expert", "rapid-builder"],
                priority=7,
                description="Lightweight database for prototyping"
            ),
            MCPActivationRule(
                mcp_name="sqlite",
                trigger_type=MCPTriggerType.PROJECT_TYPE,
                conditions=["prototype", "mvp", "demo"],
                agents=["rapid-builder", "database-expert"],
                priority=8
            ),
            
            # Brave Search MCP Rules
            MCPActivationRule(
                mcp_name="brave_search",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["research", "search", "investigate", "analyze", "compare", "best practices", "troubleshoot"],
                agents=["requirements-analyst", "project-architect", "debug-specialist"],
                priority=6,
                description="Web search for research and troubleshooting"
            ),
            MCPActivationRule(
                mcp_name="brave_search",
                trigger_type=MCPTriggerType.AGENT_ROLE,
                conditions=["requirements-analyst"],
                agents=["requirements-analyst"],
                priority=7
            ),
            
            # Firecrawl MCP Rules
            MCPActivationRule(
                mcp_name="firecrawl",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["scrape", "crawl", "extract", "competitor", "market research", "web data"],
                agents=["requirements-analyst", "documentation-writer"],
                priority=7,
                description="Web scraping and content extraction"
            ),
            MCPActivationRule(
                mcp_name="firecrawl",
                trigger_type=MCPTriggerType.FEATURE,
                conditions=["competitor_analysis", "market_research"],
                agents=["requirements-analyst"],
                priority=8
            ),
            
            # Quick-data MCP Rules
            MCPActivationRule(
                mcp_name="quick_data",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["data", "csv", "json", "transform", "analyze", "statistics", "metrics", "process"],
                agents=["requirements-analyst", "project-architect", "ai-specialist", "performance-optimizer"],
                priority=6,
                description="Data manipulation and analysis"
            ),
            MCPActivationRule(
                mcp_name="quick_data",
                trigger_type=MCPTriggerType.FEATURE,
                conditions=["data_processing", "analytics", "reporting"],
                agents=["requirements-analyst", "ai-specialist"],
                priority=7
            ),
            
            # Fetch MCP Rules
            MCPActivationRule(
                mcp_name="fetch",
                trigger_type=MCPTriggerType.KEYWORD,
                conditions=["api", "webhook", "http", "rest", "integration", "endpoint", "third-party"],
                agents=["api-integrator", "quality-guardian", "debug-specialist"],
                priority=5,
                description="Enhanced HTTP operations and API testing"
            ),
            MCPActivationRule(
                mcp_name="fetch",
                trigger_type=MCPTriggerType.FEATURE,
                conditions=["api_testing", "webhook_testing", "integration_testing"],
                agents=["api-integrator", "quality-guardian"],
                priority=7
            ),
        ]
    
    def should_load_mcp(self, 
                       agent_name: str, 
                       requirements: Dict[str, Any],
                       project_type: str = None) -> List[str]:
        """
        Determine which MCPs to load based on context
        
        Args:
            agent_name: Name of the agent requesting MCPs
            requirements: Project requirements dictionary
            project_type: Type of project (web_app, api_service, etc.)
            
        Returns:
            List of MCP names to activate
        """
        active_mcps = set()
        
        # Convert requirements to searchable text
        requirement_text = json.dumps(requirements).lower() if requirements else ""
        
        # Extract features from requirements
        features = self._extract_features(requirements)
        
        # Check each activation rule
        for rule in self.activation_rules:
            # Check if agent is allowed to use this MCP
            if agent_name not in rule.agents:
                continue
            
            activated = False
            
            # Check trigger conditions based on type
            if rule.trigger_type == MCPTriggerType.KEYWORD:
                for keyword in rule.conditions:
                    if keyword.lower() in requirement_text:
                        activated = True
                        logger.info(f"Activating {rule.mcp_name} for {agent_name} - keyword match: {keyword}")
                        break
            
            elif rule.trigger_type == MCPTriggerType.PROJECT_TYPE:
                if project_type and project_type.lower() in [c.lower() for c in rule.conditions]:
                    activated = True
                    logger.info(f"Activating {rule.mcp_name} for {agent_name} - project type: {project_type}")
            
            elif rule.trigger_type == MCPTriggerType.AGENT_ROLE:
                if agent_name in rule.conditions:
                    activated = True
                    logger.info(f"Activating {rule.mcp_name} for {agent_name} - agent role match")
            
            elif rule.trigger_type == MCPTriggerType.FEATURE:
                for feature in features:
                    if feature in rule.conditions:
                        activated = True
                        logger.info(f"Activating {rule.mcp_name} for {agent_name} - feature: {feature}")
                        break
            
            if activated:
                active_mcps.add(rule.mcp_name)
                self._track_activation(rule.mcp_name, agent_name, rule.priority)
        
        # Apply optimization - limit MCPs per agent
        max_mcps_per_agent = 3
        if len(active_mcps) > max_mcps_per_agent:
            # Sort by priority and take top N
            sorted_mcps = sorted(
                active_mcps, 
                key=lambda x: self._get_mcp_priority(x, agent_name),
                reverse=True
            )
            active_mcps = set(sorted_mcps[:max_mcps_per_agent])
            logger.info(f"Limited {agent_name} to top {max_mcps_per_agent} MCPs: {active_mcps}")
        
        self.active_mcps.update(active_mcps)
        return list(active_mcps)
    
    def _extract_features(self, requirements: Dict) -> List[str]:
        """Extract feature flags from requirements"""
        features = []
        
        if not requirements:
            return features
        
        # Check for specific feature patterns
        feature_keywords = {
            "payment": ["payment", "checkout", "billing", "subscription"],
            "data_processing": ["csv", "excel", "data", "transform", "etl"],
            "api_testing": ["api", "endpoint", "integration", "test"],
            "competitor_analysis": ["competitor", "market", "research"],
            "analytics": ["analytics", "metrics", "dashboard", "reporting"],
            "webhook_testing": ["webhook", "callback", "event"],
        }
        
        req_text = json.dumps(requirements).lower()
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in req_text for keyword in keywords):
                features.append(feature)
        
        return features
    
    def _get_mcp_priority(self, mcp_name: str, agent_name: str) -> int:
        """Get priority score for an MCP based on context"""
        for rule in self.activation_rules:
            if rule.mcp_name == mcp_name and agent_name in rule.agents:
                return rule.priority
        return 0
    
    def _track_activation(self, mcp_name: str, agent_name: str, priority: int):
        """Track MCP activation for analytics"""
        if mcp_name not in self.mcp_usage_stats:
            self.mcp_usage_stats[mcp_name] = {
                "activations": 0,
                "agents": {},
                "total_priority": 0
            }
        
        stats = self.mcp_usage_stats[mcp_name]
        stats["activations"] += 1
        stats["total_priority"] += priority
        
        if agent_name not in stats["agents"]:
            stats["agents"][agent_name] = 0
        stats["agents"][agent_name] += 1
    
    def get_mcp_recommendations(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get MCP recommendations for a specific agent"""
        recommendations = []
        
        for rule in self.activation_rules:
            if agent_name in rule.agents:
                recommendations.append({
                    "mcp": rule.mcp_name,
                    "description": rule.description,
                    "priority": rule.priority,
                    "triggers": rule.conditions[:3]  # Show first 3 triggers
                })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        return recommendations
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Generate usage report for MCP activations"""
        report = {
            "total_active_mcps": len(self.active_mcps),
            "active_mcps": list(self.active_mcps),
            "activation_stats": {}
        }
        
        for mcp_name, stats in self.mcp_usage_stats.items():
            avg_priority = stats["total_priority"] / stats["activations"] if stats["activations"] > 0 else 0
            report["activation_stats"][mcp_name] = {
                "total_activations": stats["activations"],
                "average_priority": round(avg_priority, 2),
                "top_agents": sorted(
                    stats["agents"].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
            }
        
        return report
    
    def should_deactivate_mcp(self, mcp_name: str, usage_threshold: float = 0.3) -> bool:
        """
        Determine if an MCP should be deactivated due to low usage
        
        Args:
            mcp_name: Name of the MCP
            usage_threshold: Minimum usage rate to keep MCP active
            
        Returns:
            True if MCP should be deactivated
        """
        if mcp_name not in self.mcp_usage_stats:
            return False
        
        stats = self.mcp_usage_stats[mcp_name]
        
        # Check if usage is below threshold
        if stats["activations"] < 5:  # Minimum activations before considering deactivation
            return False
        
        # Calculate usage efficiency (could be enhanced with more metrics)
        avg_priority = stats["total_priority"] / stats["activations"]
        
        # Deactivate if priority is consistently low
        if avg_priority < 4.0:  # Priority threshold
            logger.info(f"Recommending deactivation of {mcp_name} - low average priority: {avg_priority:.2f}")
            return True
        
        return False
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.mcp_usage_stats.clear()
        self.active_mcps.clear()
        logger.info("MCP conditional loader stats reset")

# Example usage
if __name__ == "__main__":
    loader = MCPConditionalLoader()
    
    # Test with payment requirements
    requirements = {
        "features": ["user authentication", "payment processing", "subscription management"],
        "tech_stack": {"payment": "stripe"}
    }
    
    # Test for api-integrator agent
    active_mcps = loader.should_load_mcp(
        agent_name="api-integrator",
        requirements=requirements,
        project_type="saas"
    )
    print(f"Active MCPs for api-integrator: {active_mcps}")
    
    # Test for requirements-analyst
    requirements2 = {
        "analysis": ["competitor research", "market analysis"],
        "data": ["csv processing", "metrics generation"]
    }
    
    active_mcps2 = loader.should_load_mcp(
        agent_name="requirements-analyst",
        requirements=requirements2,
        project_type="research"
    )
    print(f"Active MCPs for requirements-analyst: {active_mcps2}")
    
    # Get recommendations
    recommendations = loader.get_mcp_recommendations("devops-engineer")
    print(f"Recommendations for devops-engineer: {recommendations}")
    
    # Get usage report
    report = loader.get_usage_report()
    print(f"Usage report: {json.dumps(report, indent=2)}")