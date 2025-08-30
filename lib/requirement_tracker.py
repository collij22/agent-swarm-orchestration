#!/usr/bin/env python3
"""
Requirement Tracker Module
Tracks project requirements, their assignment to agents, and completion status
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path


class RequirementStatus(Enum):
    """Status of a requirement"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    PARTIAL = "partial"


class RequirementPriority(Enum):
    """Priority levels for requirements"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Requirement:
    """Individual requirement with tracking information"""
    id: str
    name: str
    description: str
    priority: RequirementPriority = RequirementPriority.MEDIUM
    status: RequirementStatus = RequirementStatus.PENDING
    assigned_agents: List[str] = field(default_factory=list)
    completion_percentage: int = 0
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    actual_deliverables: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_agents": self.assigned_agents,
            "completion_percentage": self.completion_percentage,
            "dependencies": self.dependencies,
            "deliverables": self.deliverables,
            "actual_deliverables": self.actual_deliverables,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Requirement':
        """Create from dictionary"""
        req = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            priority=RequirementPriority(data.get("priority", "medium")),
            status=RequirementStatus(data.get("status", "pending")),
            assigned_agents=data.get("assigned_agents", []),
            completion_percentage=data.get("completion_percentage", 0),
            dependencies=data.get("dependencies", []),
            deliverables=data.get("deliverables", []),
            actual_deliverables=data.get("actual_deliverables", []),
            notes=data.get("notes", "")
        )
        if data.get("start_time"):
            req.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            req.end_time = datetime.fromisoformat(data["end_time"])
        return req


class RequirementTracker:
    """
    Tracks requirements throughout the project lifecycle
    """
    
    def __init__(self, requirements_file: Optional[str] = None):
        """Initialize tracker with optional requirements file"""
        self.requirements: Dict[str, Requirement] = {}
        self.agent_assignments: Dict[str, List[str]] = {}  # agent -> [requirement_ids]
        
        if requirements_file:
            self.load_requirements(requirements_file)
    
    def load_requirements(self, requirements_file: str):
        """Load requirements from YAML or JSON file"""
        file_path = Path(requirements_file)
        
        if not file_path.exists():
            print(f"Requirements file not found: {requirements_file}")
            return
        
        # Load based on file extension
        if file_path.suffix in ['.yaml', '.yml']:
            try:
                import yaml
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
            except ImportError:
                print("PyYAML not installed. Install with: pip install pyyaml")
                return
        else:
            with open(file_path, 'r') as f:
                data = json.load(f)
        
        # Parse requirements
        self._parse_requirements(data)
    
    def _parse_requirements(self, data: Dict):
        """Parse requirements from loaded data"""
        # Handle different requirement formats
        features = data.get('features', [])
        
        for idx, feature in enumerate(features):
            # Handle string or dict format
            if isinstance(feature, str):
                req_id = f"REQ-{idx+1:03d}"
                req = Requirement(
                    id=req_id,
                    name=feature,
                    description=feature
                )
            else:
                req_id = feature.get('id', f"REQ-{idx+1:03d}")
                req = Requirement(
                    id=req_id,
                    name=feature.get('name', feature.get('title', f"Feature {idx+1}")),
                    description=feature.get('description', ''),
                    priority=RequirementPriority(feature.get('priority', 'medium').lower())
                )
                
                # Add acceptance criteria as deliverables
                if 'acceptance_criteria' in feature:
                    req.deliverables = feature['acceptance_criteria']
            
            self.requirements[req_id] = req
        
        # Add technical requirements if present
        tech_requirements = data.get('technical_requirements', [])
        for idx, tech in enumerate(tech_requirements):
            req_id = f"TECH-{idx+1:03d}"
            if isinstance(tech, str):
                req = Requirement(
                    id=req_id,
                    name=tech,
                    description=tech,
                    priority=RequirementPriority.HIGH
                )
            else:
                req = Requirement(
                    id=req_id,
                    name=tech.get('name', f"Technical Requirement {idx+1}"),
                    description=tech.get('description', ''),
                    priority=RequirementPriority.HIGH
                )
            
            self.requirements[req_id] = req
    
    def add_requirement(self, requirement: Requirement):
        """Add a new requirement"""
        self.requirements[requirement.id] = requirement
    
    def assign_to_agent(self, agent_name: str, requirement_ids: List[str]):
        """Assign requirements to an agent"""
        # Update agent assignments
        if agent_name not in self.agent_assignments:
            self.agent_assignments[agent_name] = []
        
        for req_id in requirement_ids:
            if req_id in self.requirements:
                # Add to agent's list
                if req_id not in self.agent_assignments[agent_name]:
                    self.agent_assignments[agent_name].append(req_id)
                
                # Add agent to requirement's assigned list
                if agent_name not in self.requirements[req_id].assigned_agents:
                    self.requirements[req_id].assigned_agents.append(agent_name)
    
    def mark_in_progress(self, requirement_id: str):
        """Mark a requirement as in progress"""
        if requirement_id in self.requirements:
            req = self.requirements[requirement_id]
            req.status = RequirementStatus.IN_PROGRESS
            if not req.start_time:
                req.start_time = datetime.now()
    
    def mark_completed(self, requirement_id: str):
        """Mark a requirement as completed"""
        if requirement_id in self.requirements:
            req = self.requirements[requirement_id]
            req.status = RequirementStatus.COMPLETED
            req.completion_percentage = 100
            if not req.end_time:
                req.end_time = datetime.now()
    
    def mark_failed(self, requirement_id: str, notes: str = ""):
        """Mark a requirement as failed"""
        if requirement_id in self.requirements:
            req = self.requirements[requirement_id]
            req.status = RequirementStatus.FAILED
            if notes:
                req.notes = notes
            if not req.end_time:
                req.end_time = datetime.now()
    
    def update_progress(self, requirement_id: str, percentage: int):
        """Update completion percentage"""
        if requirement_id in self.requirements:
            req = self.requirements[requirement_id]
            req.completion_percentage = min(100, max(0, percentage))
            
            # Update status based on percentage
            if percentage == 0:
                req.status = RequirementStatus.PENDING
            elif 0 < percentage < 100:
                req.status = RequirementStatus.IN_PROGRESS
            else:
                req.status = RequirementStatus.COMPLETED
    
    def add_deliverable(self, requirement_id: str, deliverable: str):
        """Add an actual deliverable to a requirement"""
        if requirement_id in self.requirements:
            req = self.requirements[requirement_id]
            if deliverable not in req.actual_deliverables:
                req.actual_deliverables.append(deliverable)
            
            # Auto-calculate completion based on deliverables
            if req.deliverables:
                delivered = len(req.actual_deliverables)
                expected = len(req.deliverables)
                percentage = int((delivered / expected) * 100)
                self.update_progress(requirement_id, percentage)
    
    def get_agent_requirements(self, agent_name: str) -> List[Requirement]:
        """Get all requirements assigned to an agent"""
        req_ids = self.agent_assignments.get(agent_name, [])
        return [self.requirements[req_id] for req_id in req_ids if req_id in self.requirements]
    
    def get_uncovered_requirements(self) -> List[Requirement]:
        """Get requirements with no agent assignment"""
        return [req for req in self.requirements.values() if not req.assigned_agents]
    
    def get_incomplete_requirements(self) -> List[Requirement]:
        """Get requirements that are not completed"""
        return [req for req in self.requirements.values() 
                if req.status != RequirementStatus.COMPLETED]
    
    def get_blocked_requirements(self) -> List[Requirement]:
        """Get requirements that are blocked"""
        blocked = []
        for req in self.requirements.values():
            # Check if dependencies are met
            for dep_id in req.dependencies:
                if dep_id in self.requirements:
                    dep = self.requirements[dep_id]
                    if dep.status != RequirementStatus.COMPLETED:
                        req.status = RequirementStatus.BLOCKED
                        blocked.append(req)
                        break
        return blocked
    
    def get_coverage_percentage(self) -> float:
        """Get overall requirement coverage percentage"""
        if not self.requirements:
            return 0.0
        
        total_completion = sum(req.completion_percentage for req in self.requirements.values())
        return total_completion / len(self.requirements)
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get count of requirements by status"""
        summary = {status.value: 0 for status in RequirementStatus}
        for req in self.requirements.values():
            summary[req.status.value] += 1
        return summary
    
    def get_coverage_report(self) -> Dict:
        """Get comprehensive coverage report (alias for generate_coverage_report)"""
        report = self.generate_coverage_report()
        # Add overall_completion field for compatibility
        report["overall_completion"] = report.get("overall_coverage", 0)
        return report
    
    def generate_coverage_report(self) -> Dict:
        """Generate comprehensive coverage report"""
        
        # Get status summary for by_status field
        status_summary = {}
        for status in RequirementStatus:
            count = sum(1 for req in self.requirements.values() if req.status == status)
            if count > 0:
                status_summary[status.value] = count
        
        # Calculate completion percentage
        total = len(self.requirements)
        completed = sum(1 for req in self.requirements.values() 
                       if req.status == RequirementStatus.COMPLETED)
        completion_percentage = (completed / total * 100) if total > 0 else 0
        
        report = {
            "total": total,  # Add this for compatibility
            "total_requirements": len(self.requirements),
            "overall_coverage": self.get_coverage_percentage(),
            "completion_percentage": completion_percentage,  # Add this field
            "by_status": status_summary,  # Add this field
            "status_summary": self.get_status_summary(),
            "uncovered": len(self.get_uncovered_requirements()),
            "incomplete": len(self.get_incomplete_requirements()),
            "blocked": len(self.get_blocked_requirements()),
            "by_priority": {},
            "by_agent": {},
            "requirements": []
        }
        
        # Group by priority
        for priority in RequirementPriority:
            priority_reqs = [req for req in self.requirements.values() 
                            if req.priority == priority]
            if priority_reqs:
                completed = sum(1 for req in priority_reqs 
                              if req.status == RequirementStatus.COMPLETED)
                report["by_priority"][priority.value] = {
                    "total": len(priority_reqs),
                    "completed": completed,
                    "percentage": (completed / len(priority_reqs)) * 100
                }
        
        # Group by agent
        for agent, req_ids in self.agent_assignments.items():
            agent_reqs = [self.requirements[req_id] for req_id in req_ids 
                         if req_id in self.requirements]
            if agent_reqs:
                completed = sum(1 for req in agent_reqs 
                              if req.status == RequirementStatus.COMPLETED)
                report["by_agent"][agent] = {
                    "total": len(agent_reqs),
                    "completed": completed,
                    "percentage": (completed / len(agent_reqs)) * 100
                }
        
        # Add detailed requirement info
        for req in self.requirements.values():
            report["requirements"].append({
                "id": req.id,
                "name": req.name,
                "status": req.status.value,
                "completion": req.completion_percentage,
                "priority": req.priority.value,
                "agents": req.assigned_agents,
                "deliverables_expected": len(req.deliverables),
                "deliverables_actual": len(req.actual_deliverables)
            })
        
        return report
    
    def save_state(self, file_path: str):
        """Save current state to file"""
        state = {
            "requirements": {req_id: req.to_dict() 
                           for req_id, req in self.requirements.items()},
            "agent_assignments": self.agent_assignments,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, file_path: str):
        """Load state from file"""
        with open(file_path, 'r') as f:
            state = json.load(f)
        
        self.requirements = {}
        for req_id, req_data in state.get("requirements", {}).items():
            self.requirements[req_id] = Requirement.from_dict(req_data)
        
        self.agent_assignments = state.get("agent_assignments", {})


# Example usage
if __name__ == "__main__":
    # Create tracker
    tracker = RequirementTracker()
    
    # Add some requirements
    tracker.add_requirement(Requirement(
        id="AUTH-001",
        name="User Authentication",
        description="Implement JWT-based authentication",
        priority=RequirementPriority.CRITICAL,
        deliverables=["login endpoint", "register endpoint", "JWT middleware"]
    ))
    
    tracker.add_requirement(Requirement(
        id="CRUD-001", 
        name="Task CRUD Operations",
        description="Create, Read, Update, Delete for tasks",
        priority=RequirementPriority.HIGH,
        deliverables=["GET /tasks", "POST /tasks", "PUT /tasks/:id", "DELETE /tasks/:id"]
    ))
    
    # Assign to agents
    tracker.assign_to_agent("rapid-builder", ["AUTH-001", "CRUD-001"])
    tracker.assign_to_agent("frontend-specialist", ["AUTH-001"])
    
    # Update progress
    tracker.mark_in_progress("AUTH-001")
    tracker.add_deliverable("AUTH-001", "login endpoint")
    tracker.add_deliverable("AUTH-001", "register endpoint")
    
    # Generate report
    report = tracker.generate_coverage_report()
    print(json.dumps(report, indent=2))