# LAIAS Template YAML Schema v2

## Overview

Each template is a YAML file in `templates/presets/` that defines a reusable agent
configuration for the Legacy AI Agent Studio. Templates are loaded by the
`/api/templates` endpoint and can be applied to pre-fill agent generation requests.

## Target Audience

Solo founder running a MicroSaaS company ("Legacy AI"). Templates cover the full
spectrum of business operations: revenue, marketing, product, customer success,
operations, data, content, legal, and hiring.

## Schema

```yaml
# Required fields
id: string                    # snake_case unique identifier (matches filename without .yaml)
name: string                  # Human-readable display name
description: string           # What this agent does and why it's useful
category: string              # One of the 9 categories below
tags: list[string]            # Searchable keywords (3-6 tags)
default_complexity: string    # simple | moderate | complex
default_tools: list[string]   # CrewAI tool class names
sample_prompts: list[string]  # 2-3 example prompts a user might type
suggested_config:
  llm_provider: string        # zai | openai | anthropic
  model: string               # e.g., gpt-4o
  include_memory: boolean
  include_analytics: boolean
  max_agents: integer          # 1-10
agent_structure:
  agents: list
    - name: string             # snake_case agent name
      role: string             # Agent's role description
      backstory: string        # Agent's expertise backstory
expected_outputs: list[string] # What the agent produces

# Optional fields (v2 additions for OutputRouter)
output_config:
  format: string               # markdown | json | html | csv
  destination: string           # filesystem | api | both
  filename_pattern: string      # e.g., "{agent_name}_{date}.md"
```

## Categories

| Category | ID | Count |
|----------|-----|-------|
| Revenue & Growth | revenue_growth | 15 |
| Marketing & Brand | marketing_brand | 15 |
| Product & Engineering | product_engineering | 15 |
| Customer Success | customer_success | 12 |
| Operations & Productivity | operations_productivity | 12 |
| Data & Intelligence | data_intelligence | 10 |
| Content & Communications | content_communications | 10 |
| Legal & Compliance | legal_compliance | 6 |
| Hiring & Team | hiring_team | 5 |

## Valid Tools

Tools must be from the CrewAI tools whitelist in `app/models/requests.py`.
Common tools for MicroSaaS templates:

- **Research**: SerperDevTool, ScrapeWebsiteTool, EXASearchTool
- **Documents**: FileReadTool, PDFSearchTool, CSVSearchTool, JSONSearchTool
- **Code**: CodeInterpreterTool, CodeDocsSearchTool
- **Communication**: EmailTool, SlackTool
- **Data**: PandasTool, NL2SQLTool
- **Browser**: BrowserbaseLoadTool, ScrapflyScrapeWebsiteTool

## Naming Convention

- File: `{category_prefix}_{descriptive_name}.yaml`
- ID: matches filename without `.yaml`
- Example: `revenue_lead_scoring_qualifier.yaml` → id: `revenue_lead_scoring_qualifier`
