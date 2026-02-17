#!/usr/bin/env python3
"""
Godzilla Agent Importer - Converts Prompt Library agents to LAIAS Godzilla Python agents.

This script reads agent prompts from the Prompt Library and generates
production-ready CrewAI Flow agents following the Godzilla pattern.
"""

import os
import re
import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# Paths
PROMPT_LIBRARY = Path("/Volumes/Storage/Prompt Library")
OUTPUT_DIR = Path("/Volumes/Storage/LAIAS/templates/presets")
AGENTS_OUTPUT = Path("/Volumes/Storage/LAIAS/agents/imported")


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def extract_agent_info(markdown_content: str, filename: str) -> Dict[str, Any]:
    """Extract agent information from markdown prompt file."""
    info = {
        "id": slugify(Path(filename).stem.replace("-agent", "")),
        "name": Path(filename).stem.replace("-", " ").title(),
        "description": "",
        "category": "general",
        "tags": [],
        "prompt": "",
        "when_to_invoke": [],
        "core_identity": "",
        "mission": ""
    }

    # Extract title from first heading
    title_match = re.search(r'^#\s+(.+?)$', markdown_content, re.MULTILINE)
    if title_match:
        info["name"] = title_match.group(1).strip()

    # Extract description from first paragraph after title
    desc_match = re.search(r'^#\s+.+?\n\n(.+?)(?:\n\n|\n#)', markdown_content, re.DOTALL)
    if desc_match:
        info["description"] = desc_match.group(1).strip()[:200]

    # Extract "When to Invoke" section
    invoke_match = re.search(r'##\s+When to Invoke.*?\n(.*?)(?=\n##|\n---|\Z)', markdown_content, re.DOTALL)
    if invoke_match:
        invoke_text = invoke_match.group(1)
        bullets = re.findall(r'[-*]\s+(.+)', invoke_text)
        info["when_to_invoke"] = [b.strip() for b in bullets if b.strip()]

    # Extract "Agent Prompt" section - the actual system prompt
    prompt_match = re.search(r'##\s+Agent Prompt\s*\n```\s*\n(.*?)```', markdown_content, re.DOTALL)
    if prompt_match:
        info["prompt"] = prompt_match.group(1).strip()

    # Extract Core Identity
    identity_match = re.search(r'##\s+Your Core Identity\s*\n(.*?)(?=\n##|\Z)', markdown_content, re.DOTALL)
    if identity_match:
        info["core_identity"] = identity_match.group(1).strip()

    # Extract Mission
    mission_match = re.search(r'##\s+Your Mission\s*\n(.*?)(?=\n##|\Z)', markdown_content, re.DOTALL)
    if mission_match:
        info["mission"] = mission_match.group(1).strip()

    # Determine category from content or path
    if "research" in markdown_content.lower() or "researcher" in info["name"].lower():
        info["category"] = "research"
    elif "code" in markdown_content.lower() or "developer" in info["name"].lower():
        info["category"] = "development"
    elif "security" in markdown_content.lower():
        info["category"] = "security"
    elif "test" in markdown_content.lower():
        info["category"] = "development"
    elif "document" in markdown_content.lower() or "writer" in info["name"].lower():
        info["category"] = "content"
    elif "analyst" in info["name"].lower() or "analysis" in markdown_content.lower():
        info["category"] = "analysis"
    elif "support" in markdown_content.lower():
        info["category"] = "support"
    elif "manager" in info["name"].lower():
        info["category"] = "management"
    elif "marketing" in markdown_content.lower():
        info["category"] = "marketing"

    # Extract tags from content
    tag_keywords = [
        "research", "analysis", "code", "development", "security", "testing",
        "automation", "documentation", "api", "database", "web", "cloud",
        "monitoring", "refactoring", "architecture", "deployment"
    ]
    for keyword in tag_keywords:
        if keyword in markdown_content.lower():
            info["tags"].append(keyword)

    return info


def generate_godzilla_python(agent_info: Dict[str, Any]) -> str:
    """Generate a Godzilla-pattern Python agent from agent info."""

    agent_class_name = agent_info["id"].replace("_", " ").title().replace(" ", "") + "Flow"
    state_class_name = agent_info["id"].replace("_", " ").title().replace(" ", "") + "State"

    # Determine tools based on category
    tools_map = {
        "research": ["SerperDevTool", "ScrapeWebsiteTool", "FileReadTool"],
        "development": ["FileReadTool", "CodeInterpreterTool", "DirectoryReadTool"],
        "analysis": ["FileReadTool", "CodeInterpreterTool"],
        "content": ["FileReadTool", "SerperDevTool"],
        "security": ["FileReadTool", "DirectoryReadTool"],
        "general": ["SerperDevTool", "FileReadTool"]
    }
    tools = tools_map.get(agent_info["category"], tools_map["general"])

    # Build the prompt content
    system_prompt = agent_info.get("prompt", agent_info.get("core_identity", ""))
    if not system_prompt:
        system_prompt = f"You are the {agent_info['name']}. {agent_info.get('description', '')}"

    python_code = f'''"""
{'='*80}
                    {agent_info['name'].upper()}
{agent_info.get('description', 'AI Agent')[:70]}
{'='*80}

Generated from Prompt Library
Date: {datetime.now().strftime('%Y-%m-%d')}
Category: {agent_info['category']}
{'='*80}
"""

# =============================================================================
# IMPORTS
# =============================================================================

from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai.flow.persistence import persist
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    DirectoryReadTool,
    FileReadTool,
    CodeInterpreterTool
)
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()


# =============================================================================
# STATE CLASS
# =============================================================================

class {state_class_name}(BaseModel):
    """Typed state for {agent_info['name']}."""

    task_id: str = Field(default="", description="Unique task identifier")
    status: str = Field(default="pending", description="Current execution status")
    error_count: int = Field(default=0, description="Number of errors encountered")
    last_error: Optional[str] = Field(default=None, description="Most recent error message")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Result confidence score")

    inputs: Dict[str, Any] = Field(default_factory=dict, description="Original inputs")
    intermediate_results: Dict[str, Any] = Field(default_factory=dict, description="Work in progress")
    final_results: Dict[str, Any] = Field(default_factory=dict, description="Completed outputs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


# =============================================================================
# FLOW CLASS
# =============================================================================

@persist
class {agent_class_name}(Flow[{state_class_name}]):
    """
    {agent_info['name']} - {agent_info.get('description', 'AI Agent')[:100]}

    Category: {agent_info['category']}
    Tags: {', '.join(agent_info['tags'][:5])}
    """

    def __init__(self):
        super().__init__()
        self.tools = self._initialize_tools()
        logger.info("{agent_info['name']} initialized")

    def _initialize_tools(self) -> List:
        """Initialize tools for this agent."""
        tools = []
        tool_classes = {{
            "SerperDevTool": SerperDevTool,
            "ScrapeWebsiteTool": ScrapeWebsiteTool,
            "DirectoryReadTool": DirectoryReadTool,
            "FileReadTool": FileReadTool,
            "CodeInterpreterTool": CodeInterpreterTool,
        }}
        for tool_name in {tools}:
            if tool_name in tool_classes:
                try:
                    tools.append(tool_classes[tool_name]())
                except Exception as e:
                    logger.warning(f"Failed to initialize {{tool_name}}: {{e}}")
        return tools

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> {state_class_name}:
        """Entry point - Initialize execution."""
        self.state.task_id = inputs.get('task_id', f"task_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}")
        self.state.status = "initializing"
        self.state.inputs = inputs
        logger.info("Starting execution", task_id=self.state.task_id)
        self.state.status = "initialized"
        self.state.progress = 10.0
        return self.state

    @listen("initialize")
    async def execute(self, state: {state_class_name}) -> {state_class_name}:
        """Main execution - Perform the agent's primary task."""
        if self.state.status == "error":
            return self.state

        try:
            self.state.status = "executing"
            logger.info("Executing main task", task_id=self.state.task_id)

            # Create the primary agent
            agent = Agent(
                role="{agent_info['name']}",
                goal="{agent_info.get('mission', 'Complete the assigned task effectively')[:100]}",
                backstory="""{system_prompt[:500]}""",
                tools=self.tools,
                llm=LLM(model=os.getenv("DEFAULT_MODEL", "gpt-4o"), temperature=0.7),
                verbose=True,
                memory=True
            )

            # Create the task
            task = Task(
                description=f"""{{self.state.inputs}}

                When to invoke this agent:
                {chr(10).join(['- ' + w for w in agent_info.get('when_to_invoke', ['Complete the task'])[:5]])}
                """,
                expected_output="Complete the requested task with detailed results",
                agent=agent
            )

            # Execute
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )

            result = await crew.kickoff_async()

            self.state.intermediate_results["execution"] = str(result)
            self.state.progress = 80.0
            self.state.confidence = 0.85

            return self.state

        except Exception as e:
            logger.error(f"Execution failed: {{e}}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return self.state

    @listen("execute")
    async def finalize(self, state: {state_class_name}) -> {state_class_name}:
        """Finalize and report results."""
        try:
            self.state.status = "finalizing"

            self.state.final_results = {{
                "output": self.state.intermediate_results.get("execution", ""),
                "confidence": self.state.confidence,
                "completed_at": datetime.utcnow().isoformat()
            }}

            self.state.status = "completed"
            self.state.progress = 100.0

            logger.info("Execution completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Finalization failed: {{e}}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "error"
            return self.state


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point for running the flow."""
    import json

    inputs = {{
        "task_description": os.getenv("TASK_DESCRIPTION", "Execute task"),
        "task_id": os.getenv("TASK_ID", None),
    }}

    task_inputs_json = os.getenv("TASK_INPUTS")
    if task_inputs_json:
        try:
            inputs.update(json.loads(task_inputs_json))
        except json.JSONDecodeError:
            logger.warning("Failed to parse TASK_INPUTS JSON")

    flow = {agent_class_name}()

    try:
        result = await flow.kickoff_async(inputs=inputs)
        print(json.dumps({{
            "status": flow.state.status,
            "results": flow.state.final_results
        }}, indent=2, default=str))
    except Exception as e:
        logger.error(f"Flow execution failed: {{e}}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
'''

    return python_code


def generate_yaml_template(agent_info: Dict[str, Any]) -> str:
    """Generate a YAML template for the LAIAS template system."""

    tools_map = {
        "research": ["SerperDevTool", "ScrapeWebsiteTool"],
        "development": ["FileReadTool", "CodeInterpreterTool"],
        "analysis": ["FileReadTool", "CodeInterpreterTool"],
        "content": ["FileReadTool"],
        "security": ["FileReadTool", "DirectoryReadTool"],
        "general": ["SerperDevTool", "FileReadTool"]
    }

    yaml_content = f'''# {agent_info['name']} Template
# {agent_info.get('description', 'AI Agent Template')}

id: {agent_info['id']}
name: {agent_info['name']}
description: {agent_info.get('description', 'AI agent for various tasks')[:200]}

category: {agent_info['category']}

tags:
{chr(10).join([f"  - {tag}" for tag in agent_info['tags'][:5]])}

default_complexity: {"simple" if len(agent_info.get('when_to_invoke', [])) < 3 else "moderate"}

default_tools:
{chr(10).join([f"  - {tool}" for tool in tools_map.get(agent_info['category'], tools_map['general'])])}

sample_prompts:
{chr(10).join([f'  - "{prompt[:100]}"' for prompt in agent_info.get('when_to_invoke', ['Execute the primary task'])[:3]])}

suggested_config:
  llm_provider: zai
  model: gpt-4o
  include_memory: true
  max_agents: 2

agent_structure:
  agents:
    - name: primary_agent
      role: {agent_info['name']}
      backstory: |
        {agent_info.get('core_identity', agent_info.get('description', 'Specialized AI agent'))[:300]}

expected_outputs:
  - Task completion report
  - Analysis results
  - Recommendations
'''
    return yaml_content


def process_prompt_library():
    """Process all agents in the Prompt Library."""

    stats = {
        "total_files": 0,
        "processed": 0,
        "failed": 0,
        "python_generated": 0,
        "yaml_generated": 0,
        "categories": {}
    }

    # Create output directories
    AGENTS_OUTPUT.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Find all markdown files in agents directories
    agent_dirs = [
        PROMPT_LIBRARY / "agents" / "autonomous",
        PROMPT_LIBRARY / "agents" / "legacyai",
        PROMPT_LIBRARY / "agents-refactored" / "agents",
        PROMPT_LIBRARY / "agents-refactored" / "crewai-methodology",
    ]

    all_agent_files = []
    for agent_dir in agent_dirs:
        if agent_dir.exists():
            for md_file in agent_dir.glob("*.md"):
                if md_file.name not in ["INDEX.md", "README.md", "NEW_AGENT_TEMPLATE.md", "ORGANIZATION.md"]:
                    all_agent_files.append(md_file)

    stats["total_files"] = len(all_agent_files)
    print(f"Found {len(all_agent_files)} agent prompt files")

    for md_file in all_agent_files:
        try:
            with open(md_file, 'r') as f:
                content = f.read()

            # Extract agent info
            agent_info = extract_agent_info(content, md_file.name)

            # Track categories
            cat = agent_info['category']
            stats['categories'][cat] = stats['categories'].get(cat, 0) + 1

            # Generate Godzilla Python
            python_code = generate_godzilla_python(agent_info)
            python_path = AGENTS_OUTPUT / f"{agent_info['id']}" / "flow.py"
            python_path.parent.mkdir(parents=True, exist_ok=True)

            with open(python_path, 'w') as f:
                f.write(python_code)
            stats['python_generated'] += 1

            # Generate YAML template
            yaml_content = generate_yaml_template(agent_info)
            yaml_path = OUTPUT_DIR / f"{agent_info['id']}.yaml"

            with open(yaml_path, 'w') as f:
                f.write(yaml_content)
            stats['yaml_generated'] += 1

            stats['processed'] += 1
            print(f"  Processed: {agent_info['name']} ({agent_info['category']})")

        except Exception as e:
            stats['failed'] += 1
            print(f"  FAILED: {md_file.name} - {e}")

    return stats


if __name__ == "__main__":
    print("="*60)
    print("GODZILLA AGENT IMPORTER")
    print("Converting Prompt Library to LAIAS Godzilla Agents")
    print("="*60)
    print()

    stats = process_prompt_library()

    print()
    print("="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print(f"Total files found: {stats['total_files']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Python agents generated: {stats['python_generated']}")
    print(f"YAML templates generated: {stats['yaml_generated']}")
    print()
    print("By Category:")
    for cat, count in sorted(stats['categories'].items()):
        print(f"  {cat}: {count}")
    print()
    print(f"Python agents: {AGENTS_OUTPUT}")
    print(f"YAML templates: {OUTPUT_DIR}")
