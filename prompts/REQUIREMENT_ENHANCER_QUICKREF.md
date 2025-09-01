# Requirement Enhancer Quick Reference

## 🎯 Purpose
Transform basic project requirements into detailed specifications optimized for the 15-agent swarm system.

## 📝 Quick Usage
1. Copy the prompt from `requirement_enhancer_prompt.md`
2. Add your original requirement at the bottom
3. Submit to any LLM (Claude, GPT-4, etc.)
4. Save output as `requirements.yaml`
5. Run: `python orchestrate_enhanced.py --requirements requirements.yaml`

## 🔑 Key Trigger Words for Optimization

### Payment Features
- **Keywords**: payment, billing, subscription, e-commerce, checkout
- **Activates**: Stripe MCP, payment workflow
- **Agents**: api-integrator, devops-engineer

### AI/ML Features  
- **Keywords**: AI, ML, GPT, recommendations, categorization, analysis
- **Activates**: ai-specialist agent, OpenAI integration
- **MCPs**: Ref MCP for documentation

### Real-time Features
- **Keywords**: real-time, live, instant, WebSocket, notifications
- **Activates**: WebSocket implementation, event-driven architecture
- **Agents**: rapid-builder, frontend-specialist

### Data Processing
- **Keywords**: CSV, analytics, ETL, data pipeline, reporting
- **Activates**: quick-data MCP, data workflow
- **Agents**: database-expert, performance-optimizer

### Performance Critical
- **Keywords**: high-performance, scale, concurrent users, load
- **Activates**: performance-optimizer early, caching strategies
- **MCPs**: Redis configuration, CDN setup

### Research/Analysis
- **Keywords**: research, competitor analysis, web scraping, market
- **Activates**: firecrawl MCP, brave_search MCP
- **Workflow**: research_heavy_project

## 📊 Requirement Structure (Required Fields)

```yaml
project:
  name: "Project Name"
  type: "web_app|api_service|ai_solution"  # Pick one
  complexity: "simple|moderate|complex"

core_requirements:
  - id: "REQ-001"
    description: "What must be built"
    priority: 1  # 1=critical, 2=important, 3=nice

features:
  - "User-facing feature description"

tech_stack:  # Only if specific preferences
  frontend: 
  backend:
  database:
```

## ⚡ Workflow Patterns (Auto-Selected)

| Project Contains | Workflow Activated | MCPs Enabled |
|-----------------|-------------------|--------------|
| Payment processing | payment_enabled_webapp | stripe, fetch, sqlite |
| Research/scraping | research_heavy_project | firecrawl, brave_search |
| MVP/prototype | rapid_prototype | sqlite, fetch |
| Next.js/Vercel | vercel_deployment | vercel, fetch |
| Data/CSV/analytics | data_processing_pipeline | quick_data, sqlite |
| API testing | api_testing_focused | fetch, brave_search |

## 🎨 Default Tech Stack (Override Only If Needed)

### Frontend
- React + TypeScript
- Tailwind CSS
- Vite bundler
- Zustand state management

### Backend  
- FastAPI (Python) or Express (Node.js)
- PostgreSQL + Redis
- JWT authentication
- Docker deployment

### Infrastructure
- AWS or Vercel hosting
- GitHub Actions CI/CD
- Docker containerization

## ⚠️ Important Guidelines

1. **DON'T override tech choices** unless explicitly required
2. **DON'T overcomplicate** simple projects
3. **DO include** measurable success metrics
4. **DO specify** data models and relationships
5. **DO mention** integration requirements
6. **DO state** performance expectations

## 📈 Complexity Guidelines

### Simple (3-5 requirements)
- Basic CRUD
- Standard auth
- 1-2 integrations
- ~1 week timeline

### Moderate (5-10 requirements)  
- Multiple user roles
- Real-time features
- 3-5 integrations
- ~2-3 weeks timeline

### Complex (10+ requirements)
- Microservices
- ML/AI components
- High scalability
- ~1 month+ timeline

## 🚀 Example Commands

```bash
# After generating enhanced requirements
python orchestrate_enhanced.py --requirements requirements.yaml

# With dashboard monitoring
python orchestrate_enhanced.py --requirements requirements.yaml --dashboard

# Test with mock mode first
set MOCK_MODE=true
python orchestrate_enhanced.py --requirements requirements.yaml --mock

# Resume from checkpoint
python orchestrate_enhanced.py --resume-checkpoint checkpoints/workflow_*.json
```

## 📁 File Locations
- **Prompt**: `prompts/requirement_enhancer_prompt.md`
- **Usage Script**: `prompts/use_requirement_enhancer.py`
- **Output**: Save as `requirements.yaml` in project root

## 💡 Pro Tips
- Mention specific compliance (GDPR, HIPAA) to activate security-auditor
- Include "mobile-first" for responsive design priority
- Specify "offline-capable" for PWA features
- Add "multi-tenant" for enterprise architecture
- Include performance metrics (e.g., "<200ms response") for optimization focus

## 🔍 Validation
The enhanced requirement should have:
- ✅ Clear project type and complexity
- ✅ Numbered requirements (REQ-001, TECH-001)
- ✅ Acceptance criteria for core features
- ✅ Tech stack (only if overriding defaults)
- ✅ Success metrics
- ✅ Data model descriptions
- ✅ Integration specifications