# Research Agent

A portable, 4-agent research workflow that takes any topic and produces structured, actionable documentation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESEARCH WORKFLOW                                    │
│                "From Question to Actionable Intelligence"                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐            │
│   │ RESEARCH │───▶│ ANALYZE  │───▶│ DOCUMENT  │───▶│  BUILD   │            │
│   │  Agent   │    │  Agent   │    │   Agent   │    │  Agent   │            │
│   └──────────┘    └──────────┘    └───────────┘    └──────────┘            │
│       ↓               ↓               ↓                ↓                    │
│   Deep research    Business         Markdown         Action plan           │
│   + synthesis      context          document         generation            │
│                    analysis         output                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your LLM

Copy the example config and add your API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key-here
```

Or edit `config.yaml` directly.

### 3. Run It

```bash
# Interactive mode (prompts for topic)
python run.py

# With topic argument
python run.py "Your research topic here"

# With custom output directory
python run.py --output ./my_research "Topic here"
```

## The 4 Agents

| Agent | Role | Purpose |
|-------|------|---------|
| **Researcher** | Senior Research Analyst | Deep research, source verification, structured synthesis |
| **Analyst** | Strategic Business Analyst | Maps findings to your business context, identifies opportunities |
| **Documenter** | Technical Documentation Specialist | Creates `YYYY-MM-DD_[Topic].md` with full analysis |
| **Builder** | Action Item Architect | Generates prioritized action plans if needed |

## Configuration

### config.yaml

```yaml
llm:
  provider: "openai"        # openai, anthropic, ollama, groq
  model: "gpt-4o"           # Provider-specific model name
  api_key: ""               # Or use environment variable
  base_url: null            # For OpenAI-compatible APIs

output_directory: "./research_output"

business_context:
  name: "Your Business Name"
  description: "What your business does"
  focus_areas:
    - "area 1"
    - "area 2"
```

### Supported LLM Providers

| Provider | Environment Variables | Models |
|----------|----------------------|--------|
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini, gpt-4-turbo |
| **Anthropic** | `ANTHROPIC_API_KEY`, `LLM_PROVIDER=anthropic` | claude-3-5-sonnet, claude-3-opus |
| **Groq** | `GROQ_API_KEY`, `LLM_PROVIDER=groq` | llama-3.3-70b, mixtral-8x7b |
| **Ollama** | `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://localhost:11434/v1` | llama3.2, mistral, any local model |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider to use | `openai` |
| `LLM_MODEL` | Model name | `gpt-4o` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `LLM_BASE_URL` | Custom API endpoint | - |
| `OUTPUT_DIR` | Output directory | `./research_output` |
| `RESEARCH_TOPIC` | Topic (optional) | - |

## Output

The workflow creates:

1. **Markdown Document**: `YYYY-MM-DD_[Topic].md`
   - Executive Summary
   - Key Findings
   - Business Relevance
   - Opportunities
   - Recommendations
   - Open Questions
   - Sources

2. **Summary JSON**: `[task_id]_summary.json`
   - Task metadata
   - Status
   - File paths

## Programmatic Usage

```python
import asyncio
from research_workflow import ResearchWorkflow

async def main():
    workflow = ResearchWorkflow()
    
    result = await workflow.kickoff_async(inputs={
        "topic": "Your research topic",
        "output_directory": "./output"
    })
    
    print(f"Documentation: {workflow.state.documentation_path}")

asyncio.run(main())
```

## Customizing for Your Business

Edit `config.yaml` to add your business context:

```yaml
business_context:
  name: "Acme Corp"
  description: "A SaaS company providing AI tools for small businesses"
  focus_areas:
    - "AI automation"
    - "Small business solutions"
    - "Product development"
    - "Market expansion"
```

The Analyst agent will use this context to provide relevant recommendations.

## Requirements

- Python 3.10+
- crewai >= 0.90.0
- An LLM API key (OpenAI, Anthropic, or Groq) OR a local Ollama installation

## Troubleshooting

### "No module named 'crewai'"
```bash
pip install crewai crewai-tools
```

### "API key not found"
Set your API key in `.env` or as an environment variable:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### "Model not found"
Check that you're using the correct model name for your provider. See the supported models table above.

## Files

```
research-agent/
├── research_workflow.py   # Main workflow (4 agents)
├── run.py                 # CLI runner
├── config.yaml            # Configuration
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## License

Free to use and modify.
