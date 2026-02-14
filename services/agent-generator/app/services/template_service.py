"""
Template Service for Agent Generator.

Manages Godzilla template reference and provides
template-based generation capabilities.
"""

from typing import Dict, List, Optional
import structlog

from app.prompts.godzilla_template import GODZILLA_TEMPLATE_REFERENCE, GODZILLA_VALIDATION_RULES
from app.prompts.system_prompts import TOOL_GUIDANCE

logger = structlog.get_logger()


class TemplateService:
    """
    Service for managing agent generation templates.

    Provides:
    - Godzilla template reference
    - Tool selection guidance
    - Pattern validation rules
    """

    def __init__(self):
        """Initialize the template service."""
        self._templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self):
        """Load available templates."""
        self._templates = {
            "research_simple": {
                "name": "Simple Research Agent",
                "description": "Single agent for web research tasks",
                "task_types": ["research"],
                "complexity": "simple",
                "agent_count_range": (1, 1),
                "default_tools": ["SerperDevTool"],
                "default_model": "gpt-4o"
            },
            "research_moderate": {
                "name": "Research Team",
                "description": "Multi-agent research with analyst",
                "task_types": ["research"],
                "complexity": "moderate",
                "agent_count_range": (2, 3),
                "default_tools": ["SerperDevTool", "ScrapeWebsiteTool"],
                "default_model": "gpt-4o"
            },
            "development_simple": {
                "name": "Code Assistant",
                "description": "Single agent for code tasks",
                "task_types": ["development"],
                "complexity": "simple",
                "agent_count_range": (1, 1),
                "default_tools": ["FileReadTool", "CodeInterpreterTool"],
                "default_model": "gpt-4o"
            },
            "automation_simple": {
                "name": "Task Automator",
                "description": "Single agent for automation",
                "task_types": ["automation"],
                "complexity": "simple",
                "agent_count_range": (1, 1),
                "default_tools": ["DirectoryReadTool"],
                "default_model": "gpt-4o"
            },
            "analysis_moderate": {
                "name": "Data Analyst",
                "description": "Multi-agent data analysis",
                "task_types": ["analysis"],
                "complexity": "moderate",
                "agent_count_range": (2, 3),
                "default_tools": ["FileReadTool", "CodeInterpreterTool"],
                "default_model": "gpt-4o"
            },
        }

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID."""
        return self._templates.get(template_id)

    def list_templates(
        self,
        task_type: Optional[str] = None,
        complexity: Optional[str] = None
    ) -> List[Dict]:
        """List available templates with optional filtering."""
        templates = list(self._templates.values())

        if task_type:
            templates = [t for t in templates if task_type in t.get("task_types", [])]

        if complexity:
            templates = [t for t in templates if t.get("complexity") == complexity]

        return templates

    def get_godzilla_reference(self) -> str:
        """Get the Godzilla pattern reference."""
        return GODZILLA_TEMPLATE_REFERENCE

    def get_validation_rules(self) -> Dict[str, List[tuple]]:
        """Get pattern validation rules."""
        return GODZILLA_VALIDATION_RULES

    def get_tool_guidance(self) -> str:
        """Get tool selection guidance."""
        return TOOL_GUIDANCE

    def suggest_template(self, task_type: str, complexity: str) -> Optional[Dict]:
        """Suggest a template based on task type and complexity."""
        templates = self.list_templates(task_type=task_type, complexity=complexity)
        return templates[0] if templates else None

    def get_default_tools(self, task_type: str) -> List[str]:
        """Get default tools for task type."""
        tool_mapping = {
            "research": ["SerperDevTool", "ScrapeWebsiteTool"],
            "development": ["FileReadTool", "CodeInterpreterTool"],
            "analysis": ["FileReadTool", "CodeInterpreterTool"],
            "automation": ["DirectoryReadTool", "FileReadTool"],
            "general": ["SerperDevTool", "FileReadTool"],
        }
        return tool_mapping.get(task_type, ["SerperDevTool"])

    def get_agent_count_suggestion(self, complexity: str) -> int:
        """Get suggested agent count for complexity."""
        suggestions = {"simple": 1, "moderate": 3, "complex": 5}
        return suggestions.get(complexity, 3)

    def get_model_suggestion(
        self,
        task_type: str,
        complexity: str,
        provider: str = "openai"
    ) -> str:
        """Get suggested model for task and complexity."""
        if provider == "openai":
            return "gpt-4o"
        elif provider == "anthropic":
            return "claude-3-5-sonnet-20241022"
        return "gpt-4o"

    def create_flow_diagram(
        self,
        complexity: str,
        task_type: str,
        agent_count: int
    ) -> str:
        """Create a flow diagram template."""
        if complexity == "simple":
            return """graph TD
    A[initialize] --> B[execute]
    B --> C[complete]"""
        elif complexity == "moderate":
            return """graph TD
    A[initialize] --> B[research]
    B --> C[analyze]
    C --> D[finalize]
    D --> E[complete]"""
        else:
            return """graph TD
    A[initialize] --> B[strategy]
    B --> C[collect_data]
    C --> D[analyze]
    D --> E{quality_check}
    E -->|pass| F[finalize]
    E -->|fail| G[refine]
    G --> C
    F --> H[complete]"""


# Global service instance
_template_service: Optional[TemplateService] = None


def get_template_service() -> TemplateService:
    """Get or create template service instance."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service
