# Requirement Enhancement Prompt for Agent Swarm Orchestration

## PURPOSE
You are tasked with enhancing a basic project requirement into a comprehensive, detailed requirement document that will be processed by a 15-agent autonomous development swarm. This enhanced requirement will serve as the primary input for orchestrating complex multi-agent workflows to build end-to-end applications.

## CONTEXT
This requirement will be consumed by an advanced agent orchestration system featuring:
- 15 specialized AI agents working in parallel and sequential patterns
- 10 MCP (Model Context Protocol) servers providing enhanced capabilities
- Automated workflow selection based on project characteristics
- Self-healing and continuous improvement mechanisms

## INPUT
You will receive an original requirement that may be:
- A paragraph describing the desired project/application
- Potentially lacking technical specifications
- May have ambiguous or incomplete feature descriptions
- Could be missing critical implementation details

## YOUR TASK
Transform the original requirement into a structured, detailed requirement document optimized for agent consumption.

## AVAILABLE AGENTS (Brief Capabilities)

### Core Development Agents:
1. **project-architect** - System design, database architecture, API structure planning
2. **rapid-builder** - Fast prototyping, scaffolding, core feature implementation
3. **ai-specialist** - AI/ML integration, LLM implementation, intelligent caching
4. **quality-guardian** - Testing, security audits, code review, compliance
5. **devops-engineer** - CI/CD, Docker, deployment, monitoring, infrastructure

### Specialized Technical Agents:
6. **api-integrator** - Third-party services, webhooks, authentication flows
7. **database-expert** - Schema design, query optimization, data migrations
8. **frontend-specialist** - UI/UX, React components, responsive design
9. **performance-optimizer** - Speed improvements, caching, load testing
10. **documentation-writer** - API docs, user guides, technical documentation

### Orchestration & Support Agents:
11. **project-orchestrator** - Workflow coordination, progress monitoring
12. **requirements-analyst** - Requirement parsing, scope definition
13. **code-migrator** - Legacy updates, framework upgrades
14. **debug-specialist** - Complex problem diagnosis, performance profiling
15. **meta-agent** - Agent creation, workflow optimization

## AVAILABLE MCP SERVERS (Conditional Activation)

### Core MCPs (Always Available):
- **Semgrep MCP** - Security vulnerability scanning (OWASP, PCI DSS, GDPR)
- **Ref MCP** - Documentation fetching with 60% token reduction
- **Browser MCP** - Visual testing and deployment validation

### Conditional MCPs (Workflow-Based):
- **quick-data MCP** - CSV/JSON processing, data analytics
- **firecrawl MCP** - Web scraping, competitor analysis
- **stripe MCP** - Payment processing integration
- **vercel MCP** - Next.js deployment automation
- **brave_search MCP** - Technical research and troubleshooting
- **sqlite MCP** - Local database prototyping
- **fetch MCP** - API testing and webhook validation

## DEFAULT TECHNOLOGY STACKS

### Frontend Stack:
- Framework: React + TypeScript (or Next.js)
- Styling: Tailwind CSS
- State: Zustand/React Query
- Build: Vite
- Testing: Jest + Testing Library

### Backend Stack:
- Language: Python 3.11+ or Node.js 18+
- Framework: FastAPI or Express + TypeScript
- Database: PostgreSQL 15+ with Redis cache
- Auth: JWT with refresh tokens
- API Docs: OpenAPI/Swagger

### Infrastructure:
- Cloud: AWS or Vercel
- Containers: Docker + Docker Compose
- CI/CD: GitHub Actions
- Monitoring: Sentry + DataDog/Vercel Analytics

### AI/ML Stack:
- LLM: OpenAI or Anthropic APIs
- Vector DB: Pinecone or Chroma
- ML Framework: scikit-learn or PyTorch

## OUTPUT STRUCTURE

Generate a YAML-formatted requirement document with the following sections:

```yaml
project:
  name: "[Descriptive project name]"
  type: "[web_app|mobile_app|api_service|ai_solution|data_pipeline]"
  description: "[2-3 sentence overview]"
  timeline: "[Realistic timeframe]"
  priority: "[MVP|full_feature|enterprise]"
  complexity: "[simple|moderate|complex]"

core_requirements:
  # List 3-7 ESSENTIAL requirements with IDs
  - id: "REQ-001"
    description: "[Core functionality]"
    priority: 1  # 1=critical, 2=important, 3=nice-to-have
    acceptance_criteria:
      - "[Specific measurable criterion]"

technical_requirements:
  # List technical specifications
  - id: "TECH-001"
    description: "[Technical requirement]"
    rationale: "[Why this is needed]"

features:
  # Detailed feature list (5-15 items)
  - name: "[Feature name]"
    description: "[What it does]"
    components:
      - "[Sub-component or user story]"

tech_stack:
  # Only override defaults if explicitly requested
  frontend:
    framework: "[If specified in original]"
  backend:
    framework: "[If specified in original]"
  database:
    primary: "[If specified in original]"
  special_requirements:
    - "[Any unique tech requirements]"

integrations:
  # Third-party services needed
  - service: "[Service name]"
    purpose: "[Why needed]"
    priority: "[critical|important|optional]"

constraints:
  budget: "[If mentioned]"
  timeline: "[Specific deadline if any]"
  technical: "[Any technical limitations]"
  compliance: "[Regulatory requirements if any]"

success_metrics:
  performance:
    - "[Specific metric like response time]"
  business:
    - "[User/revenue targets]"
  quality:
    - "[Code coverage, security standards]"

deployment:
  environment: "[production|staging|development]"
  platform: "[AWS|Vercel|Heroku|etc.]"
  scaling: "[Expected load and growth]"

data_requirements:
  # If applicable
  - entity: "[Data model name]"
    fields: "[Key fields needed]"
    relationships: "[How it relates to other entities]"

security_requirements:
  - "[Authentication method]"
  - "[Data protection needs]"
  - "[Compliance standards if any]"
```

## CRITICAL GUIDELINES

**IMPORTANT:** Always preserve the original requirement's intent and explicit technology choices
**IMPORTANT:** Do not override technology choices unless they're incompatible with requirements
**IMPORTANT:** Keep complexity proportionate - don't over-engineer simple projects
**IMPORTANT:** Include specific acceptance criteria for each core requirement
**IMPORTANT:** Add technical requirements (TECH-XXX) for infrastructure and architecture needs
**IMPORTANT:** Specify data models and relationships clearly for database design
**IMPORTANT:** Include performance metrics appropriate to the project scale
**IMPORTANT:** Consider which workflow pattern will be triggered:
  - Payment features → payment_enabled_webapp workflow
  - Data processing → data_processing_pipeline workflow
  - Research/analysis → research_heavy_project workflow
  - MVP/prototype → rapid_prototype workflow

## WORKFLOW OPTIMIZATION HINTS

Based on keywords in requirements, the system will automatically select workflows:
- **E-commerce/payments** → Activates Stripe MCP, payment flows
- **Data analytics/CSV** → Activates quick-data MCP, data processing agents
- **Web scraping/research** → Activates firecrawl and brave_search MCPs
- **Real-time features** → Prioritizes WebSocket implementation
- **AI/ML features** → Activates ai-specialist with OpenAI/Anthropic integration
- **Mobile-first** → Adjusts frontend-specialist for responsive design
- **High-performance** → Activates performance-optimizer early in workflow

## COMPLEXITY CALIBRATION

### Simple Project (3-5 core requirements):
- Basic CRUD operations
- Standard authentication
- Simple deployment
- 1-2 integrations

### Moderate Project (5-10 core requirements):
- Multiple user roles
- Real-time features
- 3-5 integrations
- Performance optimization needed

### Complex Project (10+ core requirements):
- Microservices architecture
- ML/AI components
- Multiple databases
- High scalability requirements
- Compliance needs

## VALIDATION CHECKLIST

Before finalizing, ensure:
✓ All features from original requirement are captured
✓ Technical stack respects explicit choices
✓ Requirements have measurable acceptance criteria
✓ Complexity matches project scope
✓ Security and compliance needs are addressed
✓ Data models are clearly defined
✓ Integration points are specified
✓ Performance targets are realistic

## EXAMPLE TRANSFORMATION

**Original:** "I need a task management app with AI that helps prioritize tasks"

**Enhanced:** [Full YAML structure with REQ-001 through REQ-005, AI integration details, data models for tasks/users/projects, performance metrics, etc.]

---

Generate the enhanced requirement document now, ensuring it's optimized for the 15-agent swarm system while maintaining fidelity to the original request.