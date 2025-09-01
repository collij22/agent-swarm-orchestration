# Comprehensive Agent Swarm Fix Plan

## Phase 1: Critical Infrastructure Repairs (Week 1)
**Goal**: Fix foundational issues preventing basic functionality

### 1.1 Automated Debugger Registration
- **File**: `lib/agent_runtime.py`
- **Action**: Register automated-debugger in AGENT_REGISTRY
- **Implementation**:
  ```python
  AGENT_REGISTRY['automated-debugger'] = {
      'model': ModelType.SONNET,
      'path': '.claude/agents/automated-debugger.md',
      'capabilities': ['error_recovery', 'build_fixing', 'validation_retry']
  }
  ```

### 1.2 Character Encoding Fix
- **Files**: All Python files with Unicode characters
- **Action**: Replace Unicode with ASCII equivalents
- **Changes**:
  - ✅ → [SUCCESS]
  - ❌ → [FAILED]
  - 🔄 → [PROCESSING]
- **Add to agent_runtime.py**:
  ```python
  import sys
  import io
  sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
  ```

### 1.3 Dependency Fixes
- **File**: `backend/requirements.txt`
- **Add**: `pydantic-settings==2.0.3`
- **Fix version conflicts between parallel agents**

### 1.4 Workflow Phase Restoration
- **File**: `orchestrate_enhanced.py`
- **Action**: Ensure Phase 1 (requirements-analyst, project-architect) always executes
- **Implementation**:
  ```python
  def determine_workflow():
      # ALWAYS start with Phase 1
      phases = [
          Phase(1, "Analysis", ["requirements-analyst", "project-architect"]),
          Phase(2, "Building", ["rapid-builder", "api-integrator", "frontend-specialist"]),
          Phase(3, "Quality", ["quality-guardian", "devops-engineer"])
      ]
      return phases
  ```

### 1.5 Parallel Agent Configuration
- **File**: `lib/orchestration_enhanced.py`
- **Change**: `MAX_PARALLEL_AGENTS = 3` (currently 2)

## Phase 2: Agent Enhancement & Coordination (Week 1-2)
**Goal**: Prevent conflicts and ensure complete implementations

### 2.1 File Locking Mechanism
- **New File**: `lib/file_coordinator.py`
- **Implementation**:
  ```python
  class FileCoordinator:
      def __init__(self):
          self.file_locks = {}
          self.file_owners = {}
      
      def acquire_lock(self, file_path, agent_name):
          if file_path in self.file_locks:
              return False  # File locked by another agent
          self.file_locks[file_path] = agent_name
          return True
      
      def release_lock(self, file_path, agent_name):
          if self.file_locks.get(file_path) == agent_name:
              del self.file_locks[file_path]
  ```

### 2.2 Agent Verification Requirements
- **Update all agent prompts** to include:
  ```
  MANDATORY VERIFICATION STEPS:
  1. After creating any file with imports, verify all imports resolve
  2. After creating configuration files, create the referenced entry points
  3. After scaffolding, implement at least one working example
  4. Before marking complete, run a syntax check on created files
  ```

### 2.3 Fix DevOps-Engineer Reasoning Loop
- **File**: `.claude/agents/devops-engineer.md`
- **Action**: Add deduplication logic in agent prompt processing
- **Add to agent_runtime.py**:
  ```python
  def clean_reasoning(text):
      lines = text.split('\n')
      unique_lines = []
      for line in lines:
          if line not in unique_lines:
              unique_lines.append(line)
      return '\n'.join(unique_lines[:3])  # Max 3 lines
  ```

### 2.4 Inter-Agent Communication Protocol
- **New Tool**: `share_artifact`
- **Implementation**:
  ```python
  def share_artifact(agent_name, artifact_type, content):
      context.artifacts[f"{agent_name}_{artifact_type}"] = content
      return f"Shared {artifact_type} for other agents"
  ```

## Phase 3: Implementation Completion Requirements (Week 2)
**Goal**: Ensure agents create working code, not just scaffolding

### 3.1 Mandatory Implementation Rules
- **Update**: `.claude/agents/rapid-builder.md`
- **Add Requirements**:
  ```yaml
  MANDATORY_IMPLEMENTATIONS:
    - If creating main.py with imports, CREATE all imported modules
    - If creating package.json, CREATE the entry point (src/main.tsx)
    - If creating models, CREATE at least one API endpoint using them
    - If creating config, CREATE the code that uses the config
  ```

### 3.2 API Router Creation Template
- **Add to rapid-builder**: Template for creating routers
- **Example for auth.py**:
  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from app.core.security import create_access_token
  from app.db.models import User
  
  router = APIRouter()
  
  @router.post("/login")
  async def login(username: str, password: str):
      # Implementation required
      return {"access_token": create_access_token({"sub": username})}
  
  @router.post("/register")
  async def register(user_data: dict):
      # Implementation required
      return {"message": "User created"}
  ```

### 3.3 Frontend Entry Point Template
- **Add to frontend-specialist**: Mandatory entry files
- **src/main.tsx**:
  ```typescript
  import React from 'react'
  import ReactDOM from 'react-dom/client'
  import App from './App'
  import './index.css'
  
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
  ```

### 3.4 Project Path Standardization
- **Add to context initialization**:
  ```python
  PROJECT_ROOT = f"projects/{project_name}/"
  context.project_root = PROJECT_ROOT
  # ALL file operations must use context.project_root
  ```

## Phase 4: Validation & Recovery Systems (Week 2-3)
**Goal**: Catch errors early and enable self-healing

### 4.1 Progressive Validation
- **New System**: Validate during execution, not just after
- **Implementation**:
  ```python
  class ProgressiveValidator:
      def validate_imports(self, file_path):
          # Check imports resolve immediately after file creation
          
      def validate_syntax(self, file_path):
          # Run syntax check on each file
          
      def validate_references(self, file_path):
          # Ensure referenced files exist
  ```

### 4.2 Checkpoint System
- **Add to agent_runtime.py**:
  ```python
  def create_checkpoint(agent_name, progress):
      checkpoint = {
          'agent': agent_name,
          'progress': progress,
          'files_created': context.created_files,
          'timestamp': datetime.now()
      }
      save_checkpoint(checkpoint)
  
  def resume_from_checkpoint(checkpoint_id):
      # Restore context and continue
  ```

### 4.3 Self-Healing Mechanisms
- **Auto-fix common issues**:
  ```python
  SELF_HEALING_RULES = {
      'ModuleNotFoundError': create_missing_module,
      'ImportError': fix_import_path,
      'FileNotFoundError': create_missing_file,
      'UnicodeDecodeError': fix_encoding
  }
  ```

### 4.4 Validation Gates
- **Before agent completion**:
  1. Syntax validation
  2. Import resolution
  3. Reference validation
  4. Minimal functionality test

## Phase 5: Quality Assurance & Monitoring (Week 3)
**Goal**: Ensure consistent quality and track performance

### 5.1 Mandatory Testing
- **Add to each agent**: Create minimal tests
- **Example**:
  ```python
  def test_basic_functionality():
      # Every agent must include at least one test
      assert api_endpoint_responds()
      assert frontend_renders()
      assert database_connects()
  ```

### 5.2 Token Usage Monitoring
- **Track per agent**:
  ```python
  class TokenMonitor:
      def track_usage(self, agent_name, tokens_used):
          if tokens_used > TOKEN_LIMIT:
              create_checkpoint()
              split_task()
  ```

### 5.3 Quality Gates
- **Minimum requirements**:
  - Backend: At least one working endpoint
  - Frontend: At least one rendered component
  - Database: Schema created and seeded
  - Docker: Containers start without errors

### 5.4 Progress Tracking
- **Real-time updates**:
  ```python
  class ProgressTracker:
      def update(self, agent, status, completion_percent):
          broadcast_to_dashboard({
              'agent': agent,
              'status': status,
              'completion': completion_percent,
              'eta': calculate_eta()
          })
  ```

### 5.5 Post-Execution Verification
- **Final checks**:
  1. Can backend start? (`python main.py`)
  2. Can frontend build? (`npm run build`)
  3. Do Docker containers run? (`docker-compose up`)
  4. Are critical endpoints accessible?

## Implementation Priority & Timeline

### Week 1: Foundation (Phase 1 + Phase 2.1-2.3)
- Fix critical infrastructure
- Implement file locking
- Fix reasoning loops

### Week 2: Implementation (Phase 2.4 + Phase 3)
- Add verification requirements
- Create implementation templates
- Standardize paths

### Week 3: Validation (Phase 4 + Phase 5)
- Add progressive validation
- Implement self-healing
- Add quality gates

## Success Metrics
- Validation success rate: >95% (from current 0%)
- Implementation completeness: >90% (from current 50%)
- Self-healing rate: >80% of common errors
- Parallel agent conflicts: <5% (from current 100%)
- Token efficiency: Maintain 60% savings with MCP

## Risk Mitigation
- **Rollback capability**: Every change includes rollback mechanism
- **Gradual rollout**: Test with simple projects first
- **Monitoring**: Track metrics before/after each phase
- **Fallback options**: Keep current system as backup