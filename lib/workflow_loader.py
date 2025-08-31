#!/usr/bin/env python3
"""
Workflow Loader for MCP-Enhanced Patterns
Loads and manages workflow patterns from YAML files with MCP integration
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

@dataclass
class WorkflowPhase:
    """Represents a phase in a workflow"""
    name: str
    execution_type: str  # 'sequential' or 'parallel'
    agents: List[Dict[str, Any]]  # List of agents with their MCPs

@dataclass
class WorkflowPattern:
    """Represents a complete workflow pattern"""
    name: str
    description: str
    triggers: List[str]
    phases: List[WorkflowPhase]
    priority: int = 1

class WorkflowLoader:
    """Loads and manages MCP-enhanced workflow patterns"""
    
    def __init__(self, patterns_file: Path = None):
        """Initialize workflow loader
        
        Args:
            patterns_file: Path to workflow patterns YAML file
        """
        self.patterns_file = patterns_file or Path("workflows/mcp_enhanced_patterns.yaml")
        self.patterns: Dict[str, WorkflowPattern] = {}
        self.selection_rules = []
        self.mcp_guidelines = {}
        self.logger = logging.getLogger(__name__)
        
        # Load patterns on initialization
        if self.patterns_file.exists():
            self.load_patterns()
    
    def load_patterns(self) -> bool:
        """Load workflow patterns from YAML file
        
        Returns:
            True if patterns loaded successfully
        """
        try:
            with open(self.patterns_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Load workflow patterns
            for workflow_name, workflow_data in data.items():
                if workflow_name in ['selection_rules', 'mcp_usage_guidelines']:
                    continue
                
                # Parse phases
                phases = []
                if 'phases' in workflow_data:
                    for phase_data in workflow_data['phases']:
                        # Handle different phase formats
                        if 'name' in phase_data:
                            phase_name = phase_data['name']
                            
                            # Determine execution type
                            if 'sequential' in phase_data:
                                exec_type = 'sequential'
                                agents_data = phase_data['sequential']
                            elif 'parallel' in phase_data:
                                exec_type = 'parallel'
                                agents_data = phase_data['parallel']
                            elif 'workflow_ref' in phase_data:
                                # Reference to another workflow
                                phases.append(WorkflowPhase(
                                    name=phase_name,
                                    execution_type='workflow_ref',
                                    agents=[{'ref': phase_data['workflow_ref']}]
                                ))
                                continue
                            else:
                                continue
                            
                            # Parse agents
                            agents = []
                            if isinstance(agents_data, list):
                                for agent_info in agents_data:
                                    if isinstance(agent_info, dict):
                                        agents.append(agent_info)
                            
                            phases.append(WorkflowPhase(
                                name=phase_name,
                                execution_type=exec_type,
                                agents=agents
                            ))
                
                # Create workflow pattern
                pattern = WorkflowPattern(
                    name=workflow_name,
                    description=workflow_data.get('description', ''),
                    triggers=workflow_data.get('triggers', []),
                    phases=phases,
                    priority=workflow_data.get('priority', 1)
                )
                
                self.patterns[workflow_name] = pattern
            
            # Load selection rules
            if 'selection_rules' in data:
                self.selection_rules = data['selection_rules']
            
            # Load MCP usage guidelines
            if 'mcp_usage_guidelines' in data:
                self.mcp_guidelines = data['mcp_usage_guidelines']
            
            self.logger.info(f"Loaded {len(self.patterns)} workflow patterns")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow patterns: {e}")
            return False
    
    def select_workflow(self, requirements: Dict, project_type: str = None) -> Optional[WorkflowPattern]:
        """Select the best workflow pattern based on requirements and project type
        
        Args:
            requirements: Project requirements dictionary
            project_type: Explicit project type
            
        Returns:
            Selected workflow pattern or None
        """
        # Convert requirements to searchable text
        req_text = json.dumps(requirements).lower()
        
        # Check explicit project type first
        if project_type:
            # Check if there's a workflow matching the project type
            for pattern_name, pattern in self.patterns.items():
                if project_type.lower() in pattern_name.lower():
                    self.logger.info(f"Selected workflow '{pattern_name}' based on project type '{project_type}'")
                    return pattern
        
        # Check triggers in requirements
        best_match = None
        best_priority = -1
        
        for pattern_name, pattern in self.patterns.items():
            # Check if any triggers match
            for trigger in pattern.triggers:
                if trigger.lower() in req_text:
                    # Use selection rules to determine priority
                    priority = self._get_workflow_priority(pattern_name, requirements)
                    if priority > best_priority:
                        best_match = pattern
                        best_priority = priority
                        break
        
        if best_match:
            self.logger.info(f"Selected workflow '{best_match.name}' with priority {best_priority}")
            return best_match
        
        # Default to standard development if available
        if 'standard_development' in self.patterns:
            self.logger.info("Using default 'standard_development' workflow")
            return self.patterns['standard_development']
        
        return None
    
    def _get_workflow_priority(self, workflow_name: str, requirements: Dict) -> int:
        """Get priority for a workflow based on selection rules
        
        Args:
            workflow_name: Name of the workflow
            requirements: Project requirements
            
        Returns:
            Priority value (higher is better)
        """
        for rule in self.selection_rules:
            if rule.get('workflow') == workflow_name:
                # Check if condition matches
                condition = rule.get('condition', '')
                if self._evaluate_condition(condition, requirements):
                    return rule.get('priority', 1)
        
        return 1  # Default priority
    
    def _evaluate_condition(self, condition: str, requirements: Dict) -> bool:
        """Evaluate a selection rule condition
        
        Args:
            condition: Condition string to evaluate
            requirements: Requirements to check against
            
        Returns:
            True if condition matches
        """
        if condition == 'default':
            return True
        
        # Simple keyword matching
        req_text = json.dumps(requirements).lower()
        
        # Parse condition (format: "requirements contains X or Y")
        if 'contains' in condition:
            keywords = condition.split('contains')[1].strip()
            # Handle 'or' conditions
            if ' or ' in keywords:
                for keyword in keywords.split(' or '):
                    if keyword.strip() in req_text:
                        return True
            else:
                return keywords.strip() in req_text
        
        return False
    
    def get_agent_mcps(self, agent_name: str, workflow_name: str, 
                       phase_name: str = None) -> List[str]:
        """Get MCPs for a specific agent in a workflow
        
        Args:
            agent_name: Name of the agent
            workflow_name: Name of the workflow
            phase_name: Optional phase name
            
        Returns:
            List of MCP names to activate for this agent
        """
        if workflow_name not in self.patterns:
            return []
        
        pattern = self.patterns[workflow_name]
        mcps = []
        
        # Search through phases
        for phase in pattern.phases:
            if phase_name and phase.name != phase_name:
                continue
            
            # Search for agent
            for agent_info in phase.agents:
                if agent_info.get('agent') == agent_name:
                    mcps.extend(agent_info.get('mcps', []))
        
        return list(set(mcps))  # Remove duplicates
    
    def get_workflow_agents(self, workflow_name: str) -> List[Tuple[str, List[str], str]]:
        """Get all agents and their MCPs for a workflow
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            List of tuples (agent_name, mcps, execution_type)
        """
        if workflow_name not in self.patterns:
            return []
        
        pattern = self.patterns[workflow_name]
        agents = []
        
        for phase in pattern.phases:
            exec_type = phase.execution_type
            
            if exec_type == 'workflow_ref':
                # Handle workflow reference
                ref_workflow = phase.agents[0].get('ref')
                if ref_workflow:
                    # Recursively get agents from referenced workflow
                    agents.extend(self.get_workflow_agents(ref_workflow))
            else:
                # Regular agents
                for agent_info in phase.agents:
                    agent_name = agent_info.get('agent', '')
                    mcps = agent_info.get('mcps', [])
                    agents.append((agent_name, mcps, exec_type))
        
        return agents
    
    def get_mcp_guidelines(self, mcp_name: str) -> Dict[str, Any]:
        """Get usage guidelines for a specific MCP
        
        Args:
            mcp_name: Name of the MCP
            
        Returns:
            Dictionary with MCP guidelines
        """
        return self.mcp_guidelines.get(mcp_name, {})
    
    def get_workflow_description(self, workflow_name: str) -> str:
        """Get description for a workflow
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Workflow description
        """
        if workflow_name in self.patterns:
            return self.patterns[workflow_name].description
        return ""
    
    def list_available_workflows(self) -> List[str]:
        """Get list of all available workflow patterns
        
        Returns:
            List of workflow names
        """
        return list(self.patterns.keys())
    
    def export_workflow_summary(self) -> Dict[str, Any]:
        """Export a summary of all workflows and their MCP usage
        
        Returns:
            Dictionary with workflow summaries
        """
        summary = {
            'total_workflows': len(self.patterns),
            'workflows': {},
            'mcp_usage_stats': {}
        }
        
        # Count MCP usage across workflows
        mcp_counts = {}
        
        for workflow_name, pattern in self.patterns.items():
            workflow_info = {
                'description': pattern.description,
                'triggers': pattern.triggers,
                'phases': len(pattern.phases),
                'agents': [],
                'mcps_used': []
            }
            
            # Collect agents and MCPs
            agents_mcps = self.get_workflow_agents(workflow_name)
            for agent_name, mcps, exec_type in agents_mcps:
                workflow_info['agents'].append(agent_name)
                workflow_info['mcps_used'].extend(mcps)
                
                # Count MCP usage
                for mcp in mcps:
                    mcp_counts[mcp] = mcp_counts.get(mcp, 0) + 1
            
            # Remove duplicates
            workflow_info['agents'] = list(set(workflow_info['agents']))
            workflow_info['mcps_used'] = list(set(workflow_info['mcps_used']))
            
            summary['workflows'][workflow_name] = workflow_info
        
        summary['mcp_usage_stats'] = mcp_counts
        
        return summary


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create workflow loader
    loader = WorkflowLoader()
    
    # Test workflow selection
    test_requirements = {
        "project": {
            "name": "TestApp",
            "type": "web_app"
        },
        "features": ["payment", "subscription"]
    }
    
    selected = loader.select_workflow(test_requirements)
    if selected:
        print(f"Selected workflow: {selected.name}")
        print(f"Description: {selected.description}")
        print(f"Phases: {len(selected.phases)}")
        
        # Get agents and MCPs
        agents_mcps = loader.get_workflow_agents(selected.name)
        for agent, mcps, exec_type in agents_mcps:
            print(f"  {agent} ({exec_type}): MCPs = {mcps}")
    
    # Export summary
    summary = loader.export_workflow_summary()
    print(f"\nWorkflow Summary:")
    print(f"Total workflows: {summary['total_workflows']}")
    print(f"MCP usage stats: {summary['mcp_usage_stats']}")