"""
Few-shot examples for LLM code generation.

Provides curated examples of generated agents to guide the LLM
toward high-quality outputs following the Godzilla pattern.
"""

from typing import List, Dict, Any

# =============================================================================
# Simple Examples
# =============================================================================

SIMPLE_RESEARCH_EXAMPLE = {
    "description": "Create a web research agent that searches for information and summarizes findings",
    "output": {
        "flow_code": """
from crewai import Agent, Task, Crew, Process, LLM
from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class ResearchState(BaseModel):
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: str = Field(default=None)
    progress: float = Field(default=0.0)
    confidence: float = Field(default=0.5)
    query: str = Field(default="")
    research_results: str = Field(default="")

@persist
class SimpleResearchFlow(Flow[ResearchState]):
    def __init__(self):
        super().__init__()
        self.tools = [SerperDevTool(), ScrapeWebsiteTool()]

    def _create_researcher(self) -> Agent:
        return Agent(
            role="Research Specialist",
            goal="Find and summarize relevant information",
            backstory="Expert researcher with 10+ years of experience finding accurate information online.",
            tools=self.tools,
            llm=LLM(model="gpt-4o", temperature=0.7)
        )

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> ResearchState:
        self.state.task_id = inputs.get("task_id", "research_001")
        self.state.query = inputs.get("query", "")
        self.state.status = "initializing"
        logger.info("Starting research", task_id=self.state.task_id, query=self.state.query)
        return self.state

    @listen("initialize")
    async def research(self, state: ResearchState) -> ResearchState:
        try:
            self.state.status = "researching"
            researcher = self._create_researcher()

            task = Task(
                description=f"Research: {self.state.query}\\nFind comprehensive information and summarize key findings.",
                expected_output="Detailed summary of findings",
                agent=researcher
            )

            crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential)
            result = await crew.kickoff_async()

            self.state.research_results = str(result)
            self.state.progress = 100.0
            self.state.confidence = 0.8
            self.state.status = "completed"

            logger.info("Research completed", task_id=self.state.task_id)
            return self.state

        except Exception as e:
            logger.error(f"Research failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            self.state.status = "failed"
            return self.state
""",
        "state_class": """
class ResearchState(BaseModel):
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    last_error: str = Field(default=None)
    progress: float = Field(default=0.0)
    confidence: float = Field(default=0.5)
    query: str = Field(default="")
    research_results: str = Field(default="")
""",
        "agents_yaml": """
researcher:
  role: Research Specialist
  goal: Find and summarize relevant information
  backstory: Expert researcher with 10+ years of experience
  tools:
    - SerperDevTool
    - ScrapeWebsiteTool
""",
        "flow_diagram": """graph TD
    A[initialize] --> B[research]
    B --> C{status}
    C -->|completed| D[End]
    C -->|failed| E[End]"""
    }
}

SIMPLE_AUTOMATION_EXAMPLE = {
    "description": "Create a monitoring agent that checks API health and sends alerts",
    "output": {
        "flow_code": """
from crewai import Agent, Task, Crew, LLM
from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
from pydantic import BaseModel, Field
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class MonitorState(BaseModel):
    task_id: str = Field(default="")
    status: str = Field(default="pending")
    error_count: int = Field(default=0)
    target_url: str = Field(default="")
    health_status: str = Field(default="unknown")
    alerts_sent: int = Field(default=0)

@persist
class ApiMonitorFlow(Flow[MonitorState]):
    def __init__(self):
        super().__init__()

    def _create_monitor(self) -> Agent:
        return Agent(
            role="API Monitor",
            goal="Check API health and generate status reports",
            backstory="Specialized monitoring agent for API health checking.",
            llm=LLM(model="gpt-4o")
        )

    @start()
    async def initialize(self, inputs: Dict[str, Any]) -> MonitorState:
        self.state.task_id = inputs.get("task_id", "monitor_001")
        self.state.target_url = inputs.get("url", "")
        return self.state

    @listen("initialize")
    async def check_health(self, state: MonitorState) -> MonitorState:
        try:
            monitor = self._create_monitor()
            task = Task(
                description=f"Check health of {self.state.target_url}\\nGenerate a status report.",
                expected_output="Health status and any issues found",
                agent=monitor
            )
            crew = Crew(agents=[monitor], tasks=[task])
            result = await crew.kickoff_async()
            self.state.health_status = str(result)
            self.state.status = "completed"
            return self.state
        except Exception as e:
            self.state.error_count += 1
            self.state.status = "error"
            return self.state
""",
        "state_class": "class MonitorState(BaseModel):\n    task_id: str\n    status: str\n    error_count: int\n    target_url: str\n    health_status: str\n    alerts_sent: int",
        "agents_yaml": "monitor:\n  role: API Monitor\n  goal: Check API health",
        "flow_diagram": "graph TD\n    A[initialize] --> B[check_health]\n    B --> C[End]"
    }
}

# =============================================================================
# Moderate Examples
# =============================================================================

MODERATE_RESEARCH_EXAMPLE = {
    "description": "Create a multi-agent research team that analyzes competitor data",
    "output": {
        "agents_info": [
            {
                "role": "Lead Researcher",
                "goal": "Coordinate research efforts and synthesize findings",
                "tools": ["SerperDevTool", "ScrapeWebsiteTool"],
                "llm_config": {"model": "gpt-4o", "temperature": 0.7}
            },
            {
                "role": "Data Analyst",
                "goal": "Analyze competitor data and extract insights",
                "tools": ["CodeInterpreterTool"],
                "llm_config": {"model": "gpt-4o", "temperature": 0.5}
            }
        ],
        "flow_diagram": """graph TD
    A[initialize] --> B[research_phase]
    B --> C[analyze_phase]
    C --> D{router}
    D -->|confidence >= 0.7| E[finalize]
    D -->|confidence < 0.7| F[refine]
    F --> B
    E --> G[End]"""
    }
}

MODERATE_DEVELOPMENT_EXAMPLE = {
    "description": "Create a development assistant that reviews code and suggests improvements",
    "output": {
        "agents_info": [
            {
                "role": "Code Reviewer",
                "goal": "Review code for bugs, security issues, and best practices",
                "tools": ["FileReadTool"],
                "llm_config": {"model": "gpt-4o", "temperature": 0.3}
            },
            {
                "role": "Refactoring Specialist",
                "goal": "Suggest improvements and refactoring opportunities",
                "tools": ["CodeInterpreterTool"],
                "llm_config": {"model": "gpt-4o", "temperature": 0.5}
            }
        ],
        "requirements": ["crewai[tools]>=0.80.0", "pydantic>=2.5.0", "structlog>=24.1.0"]
    }
}

MODERATE_ANALYSIS_EXAMPLE = {
    "description": "Create a data analysis agent that processes files and generates reports",
    "output": {
        "agents_info": [
            {
                "role": "Data Collector",
                "goal": "Gather data from multiple sources",
                "tools": ["FileReadTool", "DirectoryReadTool"],
                "llm_config": {"model": "gpt-4o"}
            },
            {
                "role": "Data Analyst",
                "goal": "Process and analyze data",
                "tools": ["CodeInterpreterTool"],
                "llm_config": {"model": "gpt-4o"}
            },
            {
                "role": "Report Writer",
                "goal": "Generate comprehensive reports",
                "tools": [],
                "llm_config": {"model": "gpt-4o", "temperature": 0.3}
            }
        ]
    }
}

# =============================================================================
# Complex Examples
# =============================================================================

COMPLEX_RESEARCH_EXAMPLE = {
    "description": "Create a comprehensive research platform with multiple specialized agents",
    "output": {
        "agents_info": [
            {"role": "Lead Researcher", "goal": "Orchestrate research strategy"},
            {"role": "Web Researcher", "goal": "Gather online information", "tools": ["SerperDevTool", "ScrapeWebsiteTool"]},
            {"role": "Data Analyst", "goal": "Analyze findings", "tools": ["CodeInterpreterTool"]},
            {"role": "Report Generator", "goal": "Create comprehensive reports"},
            {"role": "Quality Reviewer", "goal": "Validate findings and ensure accuracy"}
        ],
        "flow_diagram": """graph TD
    A[initialize] --> B[strategy]
    B --> C[data_collection]
    C --> D[analysis]
    D --> E{quality_check}
    E -->|pass| F[generate_report]
    E -->|fail| G[refine]
    G --> C
    F --> H[End]"""
    }
}

COMPLEX_AUTOMATION_EXAMPLE = {
    "description": "Create an automation workflow with monitoring, alerts, and recovery",
    "output": {
        "flow_diagram": """graph TD
    A[initialize] --> B[monitor]
    B --> C{status}
    C -->|healthy| D[log_metrics]
    C -->|degraded| E[alert]
    C -->|error| F[recovery]
    F --> G{retry_count}
    G -->|< 3| B
    G -->|>= 3| H[escalate]
    D --> I[End]
    E --> I
    H --> I"""
    }
}

# =============================================================================
# Example Categories (defined after examples to avoid forward reference issues)
# =============================================================================

EXAMPLES_BY_COMPLEXITY = {
    "simple": {
        "research": SIMPLE_RESEARCH_EXAMPLE,
        "automation": SIMPLE_AUTOMATION_EXAMPLE,
    },
    "moderate": {
        "research": MODERATE_RESEARCH_EXAMPLE,
        "development": MODERATE_DEVELOPMENT_EXAMPLE,
        "analysis": MODERATE_ANALYSIS_EXAMPLE,
    },
    "complex": {
        "research": COMPLEX_RESEARCH_EXAMPLE,
        "automation": COMPLEX_AUTOMATION_EXAMPLE,
    }
}

# =============================================================================
# Few-Shot Selector
# =============================================================================

class FewShotSelector:
    """Selects appropriate few-shot examples based on request parameters."""

    def get_examples(self, complexity: str, task_type: str, count: int = 2) -> List[Dict[str, Any]]:
        """
        Get relevant few-shot examples.

        Args:
            complexity: Complexity level (simple, moderate, complex)
            task_type: Task type (research, development, etc.)
            count: Number of examples to return

        Returns:
            List of example dictionaries with descriptions and outputs
        """
        examples = []

        # Get best match for complexity/task_type
        if complexity in EXAMPLES_BY_COMPLEXITY:
            if task_type in EXAMPLES_BY_COMPLEXITY[complexity]:
                examples.append(EXAMPLES_BY_COMPLEXITY[complexity][task_type])

        # Add a simple example as baseline if not enough
        if len(examples) < count:
            examples.append(SIMPLE_RESEARCH_EXAMPLE)

        return examples[:count]

    def get_formatted_examples(self, complexity: str, task_type: str) -> str:
        """
        Get few-shot examples formatted for inclusion in prompt.

        Returns a formatted string with examples.
        """
        examples = self.get_examples(complexity, task_type)
        formatted = []

        for i, ex in enumerate(examples, 1):
            formatted.append(f"""
### Example {i}: {ex['description']}

```json
{ex.get('output', ex)}
```
""")

        return "\n".join(formatted)


# Global instance
FEW_SHOT_SELECTOR = FewShotSelector()


def get_few_shot_examples(complexity: str = "moderate", task_type: str = "general") -> str:
    """Convenience function to get formatted few-shot examples."""
    return FEW_SHOT_SELECTOR.get_formatted_examples(complexity, task_type)
