"""
Template Service for Agent Generator.

Manages Godzilla template reference, YAML-based preset templates,
and provides template-based generation capabilities.
"""

import os
from pathlib import Path

import structlog
import yaml

from app.prompts.godzilla_template import GODZILLA_TEMPLATE_REFERENCE, GODZILLA_VALIDATION_RULES
from app.prompts.system_prompts import TOOL_GUIDANCE

logger = structlog.get_logger()

# =============================================================================
# Templates Directory
# =============================================================================

TEMPLATES_DIR = Path(os.environ.get("TEMPLATES_DIR", "/app/templates/presets"))


# =============================================================================
# Template Service
# =============================================================================


class TemplateService:
    """
    Service for managing agent generation templates.

    Loads preset templates from YAML files on disk and provides:
    - YAML-based template listing, filtering, and retrieval
    - Godzilla template reference for code generation
    - Tool selection guidance
    - Pattern validation rules
    """

    def __init__(self):
        """Initialize the template service and load YAML templates."""
        self._templates: dict[str, dict] = {}
        self._categories: list[str] = []
        self._load_templates()

    def _load_templates(self):
        """Load all YAML template files from the presets directory."""
        if not TEMPLATES_DIR.exists():
            logger.warning(
                "Templates directory not found",
                path=str(TEMPLATES_DIR),
            )
            return

        loaded = 0
        skipped = 0

        for template_file in sorted(TEMPLATES_DIR.glob("*.yaml")):
            try:
                with open(template_file) as f:
                    data = yaml.safe_load(f)

                if not isinstance(data, dict):
                    logger.warning(
                        "Invalid template format",
                        file=str(template_file),
                    )
                    skipped += 1
                    continue

                template_id = data.get("id")
                if not template_id:
                    logger.warning(
                        "Template missing id field",
                        file=str(template_file),
                    )
                    skipped += 1
                    continue

                # Sanitize optional fields with sensible defaults
                self._sanitize_template(data, template_id)
                self._templates[template_id] = data
                loaded += 1

            except Exception as e:
                logger.error(
                    "Failed to load template file",
                    file=str(template_file),
                    error=str(e),
                )
                skipped += 1

        # Build category index
        self._categories = sorted(
            set(t.get("category", "general") for t in self._templates.values())
        )

        logger.info(
            "Templates loaded",
            loaded=loaded,
            skipped=skipped,
            categories=len(self._categories),
        )

    @staticmethod
    def _sanitize_template(data: dict, template_id: str) -> None:
        """Fill missing optional fields with sensible defaults."""
        if not data.get("name"):
            data["name"] = template_id.replace("_", " ").title()

        if not data.get("description"):
            data["description"] = f"Agent template: {data['name']}"

        if not data.get("category"):
            data["category"] = "general"

        if not data.get("tags"):
            data["tags"] = ["agent"]

        if not data.get("sample_prompts"):
            data["sample_prompts"] = [f"Use the {data['name']} template"]

        if not data.get("default_complexity"):
            data["default_complexity"] = "moderate"

        if not data.get("default_tools"):
            data["default_tools"] = ["SerperDevTool"]

        if not data.get("suggested_config"):
            data["suggested_config"] = {
                "llm_provider": "openai",
                "model": "gpt-4o",
                "include_memory": True,
                "include_analytics": True,
                "max_agents": 3,
            }

        if not data.get("agent_structure"):
            data["agent_structure"] = {
                "agents": [
                    {
                        "name": "primary_agent",
                        "role": "AI Agent",
                        "backstory": "Specialized AI agent",
                    }
                ]
            }

        if not data.get("expected_outputs"):
            data["expected_outputs"] = ["Task completion report"]

    # =========================================================================
    # Template Retrieval
    # =========================================================================

    def get_template(self, template_id: str) -> dict | None:
        """Get a single template by ID."""
        return self._templates.get(template_id)

    def list_templates(
        self,
        category: str | None = None,
        complexity: str | None = None,
        task_type: str | None = None,
        search: str | None = None,
    ) -> list[dict]:
        """
        List templates with optional filtering.

        Args:
            category: Filter by category (e.g., 'revenue_growth')
            complexity: Filter by default_complexity ('simple', 'moderate', 'complex')
            task_type: Filter by category (legacy compat — maps to category)
            search: Search in name and description
        """
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.get("category") == category]

        if task_type:
            templates = [t for t in templates if t.get("category") == task_type]

        if complexity:
            templates = [t for t in templates if t.get("default_complexity") == complexity]

        if search:
            search_lower = search.lower()
            templates = [
                t
                for t in templates
                if search_lower in t.get("name", "").lower()
                or search_lower in t.get("description", "").lower()
            ]

        return templates

    def list_categories(self) -> list[str]:
        """Get all unique template categories."""
        return list(self._categories)

    def get_template_count(self) -> int:
        """Get total number of loaded templates."""
        return len(self._templates)

    # =========================================================================
    # Godzilla Pattern Reference
    # =========================================================================

    def get_godzilla_reference(self) -> str:
        """Get the Godzilla pattern reference."""
        return GODZILLA_TEMPLATE_REFERENCE

    def get_validation_rules(self) -> dict[str, list[tuple]]:
        """Get pattern validation rules."""
        return GODZILLA_VALIDATION_RULES

    def get_tool_guidance(self) -> str:
        """Get tool selection guidance."""
        return TOOL_GUIDANCE

    # =========================================================================
    # Template Suggestions
    # =========================================================================

    def suggest_template(
        self,
        task_type: str,
        complexity: str,
    ) -> dict | None:
        """Suggest a template based on task type and complexity."""
        templates = self.list_templates(
            category=task_type,
            complexity=complexity,
        )
        return templates[0] if templates else None

    def get_default_tools(self, task_type: str) -> list[str]:
        """Get default tools for a task type from loaded templates."""
        templates = self.list_templates(category=task_type)
        if templates:
            return templates[0].get("default_tools", ["SerperDevTool"])

        # Fallback mapping for categories without templates
        fallback = {
            "research": ["SerperDevTool", "ScrapeWebsiteTool"],
            "development": ["FileReadTool", "CodeInterpreterTool"],
            "analysis": ["FileReadTool", "CodeInterpreterTool"],
            "automation": ["DirectoryReadTool", "FileReadTool"],
            "general": ["SerperDevTool", "FileReadTool"],
        }
        return fallback.get(task_type, ["SerperDevTool"])

    def get_agent_count_suggestion(self, complexity: str) -> int:
        """Get suggested agent count for complexity."""
        suggestions = {"simple": 1, "moderate": 3, "complex": 5}
        return suggestions.get(complexity, 3)

    def get_model_suggestion(
        self,
        task_type: str,
        complexity: str,
        provider: str = "openai",
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
        agent_count: int,
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

    def reload(self) -> None:
        """Reload templates from disk (useful after adding new templates)."""
        self._templates.clear()
        self._categories.clear()
        self._load_templates()


# =============================================================================
# Global Service Instance
# =============================================================================

_template_service: TemplateService | None = None


def get_template_service() -> TemplateService:
    """Get or create template service instance."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service
