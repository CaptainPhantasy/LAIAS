# LAIAS Agent Library

Production-ready CrewAI agent configurations organized by functional capability.

## Structure (126 Agents)

```
agents/
├── development/              # 30 agents - Code, APIs, implementation
├── project_management/       # 20 agents - Coordination, planning, workflows
├── quality_assurance/        # 20 agents - Testing, auditing, quality control
├── research_analysis/        # 12 agents - Intelligence, investigation, reasoning
├── tools_integration/        # 11 agents - Tool builders, MCP, integrations
├── design_experience/        # 8 agents - UX/UI, developer experience
├── data_analytics/           # 7 agents - Data analysis, observability
├── documentation_knowledge/  # 7 agents - Knowledge management, docs
├── business_strategy/        # 6 agents - Growth, customer support
└── security_compliance/      # 5 agents - Security, policy enforcement
```

## Categories

| Category | Count | Purpose |
|----------|-------|---------|
| `development/` | 30 | Code implementation, refactoring, architecture, APIs |
| `project_management/` | 20 | Orchestration, planning, coordination, governance |
| `quality_assurance/` | 20 | Testing, auditing, reviews, release gates |
| `research_analysis/` | 12 | Intelligence gathering, analysis, reasoning |
| `tools_integration/` | 11 | MCP servers, extensions, tooling |
| `design_experience/` | 8 | UX/UI design, user experience, usability |
| `data_analytics/` | 7 | Data flows, observability, pattern analysis |
| `documentation_knowledge/` | 7 | Docs, knowledge management, narratives |
| `business_strategy/` | 6 | Growth, customer support, experiments |
| `security_compliance/` | 5 | Security hardening, policy enforcement |

## Usage

### Load an Agent
```python
from crewai import Agent
import yaml

# Load from library
with open('templates/agents/development/implementer_agent.yaml') as f:
    config = yaml.safe_load(f)

agent = Agent(
    name=config['name'],
    role=config['role'],
    goal=config['goal'],
    backstory=config['backstory'],
    allow_delegation=config.get('allow_delegation', False),
    verbose=config.get('verbose', True)
)
```

### Deploy via LAIAS
1. Select agent YAML from library
2. POST to `/api/generate` with agent description
3. Generated `flow.py` uses agent config
4. Deploy to `/var/laias/agents/{agent-id}/`

## YAML Structure

```yaml
name: agent_name_normalized
role: Original-Agent-Name
goal: Excel at [specific capability]
backstory: |
  High-fidelity expert persona...
tools:
  - MCP tool references
allow_delegation: false
verbose: true
```

## Featured Agents by Category

### Development
- `implementer_agent.yaml` - Universal task executor
- `legacy_ai_senior_developer.yaml` - Production engineer
- `refactoring_architect_agent.yaml` - Safe code transformations

### Project Management
- `unau_orchestrator.yaml` - Universal agent orchestrator
- `repo_governor_autonomous_agent.yaml` - Repository governance
- `bmad_ssot_roadmap_author.yaml` - Roadmap planning

### Quality Assurance
- `testing_agent.yaml` - Focused test creation
- `critic_agent.yaml` - Repository quality analyst
- `overwatch_agent.yaml` - Verification authority

### Research Analysis
- `metacognitive_reasoner_agent.yaml` - Deep reasoning
- `code_archaeologist_agent.yaml` - Historical code analysis
- `deep_repo_intelligence_interview_agent.yaml` - Repository intelligence

### Tools Integration
- `mcp_specialist_agent.yaml` - MCP implementations
- `chrome_extension_bridge_agent.yaml` - Browser integration
- `phallus_agent.yaml` - File-system state management

## MCP Tools Available

All agents have access to:
- **Floyd Suite:** runner, git, explorer, patch, devtools, supercache, safe-ops, terminal
- **AI Orchestration:** lab-lead, hivemind, omega, novel-concepts, pattern-crystallizer, context-singularity
- **Specialized:** gemini-tools, zai-mcp-server, web-search, web-reader
