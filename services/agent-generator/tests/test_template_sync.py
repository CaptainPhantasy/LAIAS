"""
Tests that the Godzilla prompt template stays in sync with validation rules.

Catches drift between GODZILLA_TEMPLATE_REFERENCE (what the LLM sees) and
GODZILLA_VALIDATION_RULES (what generated code is checked against).
"""

import re

from app.prompts.godzilla_template import (
    GODZILLA_TEMPLATE_REFERENCE,
    GODZILLA_VALIDATION_RULES,
)

REFERENCE_FILE = "templates/godzilla_reference.py"


class TestTemplateSyncWithValidation:
    def test_every_required_pattern_mentioned_in_prompt(self):
        """Each required validation rule keyword must appear in the prompt template."""
        for pattern_regex, description in GODZILLA_VALIDATION_RULES["required_patterns"]:
            keyword = _extract_keyword(pattern_regex, description)
            assert keyword.lower() in GODZILLA_TEMPLATE_REFERENCE.lower(), (
                f"Validation rule '{description}' (keyword '{keyword}') "
                f"is missing from GODZILLA_TEMPLATE_REFERENCE"
            )

    def test_required_patterns_table_has_all_rules(self):
        """The Required Patterns markdown table must list every required rule."""
        table_section = _extract_table_section(GODZILLA_TEMPLATE_REFERENCE)
        assert table_section, "Required Patterns table not found in template"

        for _, description in GODZILLA_VALIDATION_RULES["required_patterns"]:
            keyword = _extract_keyword_from_description(description)
            assert keyword.lower() in table_section.lower(), (
                f"Required Patterns table is missing rule: '{description}'"
            )

    def test_prompt_contains_output_router_implementation(self):
        """Prompt must include OutputRouter class code, not just a mention."""
        assert "class OutputRouter:" in GODZILLA_TEMPLATE_REFERENCE
        assert "async def emit(" in GODZILLA_TEMPLATE_REFERENCE
        assert "_load_output_config" in GODZILLA_TEMPLATE_REFERENCE

    def test_prompt_contains_core_flow_structure(self):
        """Prompt must show the core flow decorators in code examples."""
        assert "@start()" in GODZILLA_TEMPLATE_REFERENCE
        assert "@listen(" in GODZILLA_TEMPLATE_REFERENCE
        assert "@router(" in GODZILLA_TEMPLATE_REFERENCE
        assert "@persist()" in GODZILLA_TEMPLATE_REFERENCE

    def test_prompt_contains_typed_state_example(self):
        """Prompt must include a typed state class example."""
        assert "class AgentState(BaseModel):" in GODZILLA_TEMPLATE_REFERENCE

    def test_prompt_contains_structured_logging(self):
        """Prompt must show structlog usage."""
        assert "structlog" in GODZILLA_TEMPLATE_REFERENCE
        assert "logger.info(" in GODZILLA_TEMPLATE_REFERENCE
        assert "logger.error(" in GODZILLA_TEMPLATE_REFERENCE

    def test_validation_rule_count_is_expected(self):
        """Guard against rules being silently removed."""
        required = GODZILLA_VALIDATION_RULES["required_patterns"]
        assert len(required) >= 8, (
            f"Expected at least 8 required patterns, got {len(required)}. Was a rule removed?"
        )


def _extract_keyword(pattern_regex: str, description: str) -> str:
    """Pull a human-readable keyword from a validation rule."""
    keyword_map = {
        "Flow[": "Flow[",
        "@start": "@start()",
        "@listen": "@listen(",
        "BaseModel": "BaseModel",
        "_create_": "_create_",
        "try:": "try:",
        "logger": "logger.",
        "OutputRouter": "OutputRouter",
    }
    for key, display in keyword_map.items():
        if key in pattern_regex or key in description:
            return display
    return description.split()[-1]


def _extract_keyword_from_description(description: str) -> str:
    """Pull a keyword from the description text for table matching."""
    keywords = {
        "Flow[State]": "Flow[",
        "@start()": "@start()",
        "@listen()": "@listen()",
        "typed state": "Typed State",
        "agent factory": "factory",
        "error handling": "try/except",
        "logging": "logging",
        "OutputRouter": "OutputRouter",
    }
    for trigger, keyword in keywords.items():
        if trigger.lower() in description.lower():
            return keyword
    return description


def _extract_table_section(template: str) -> str:
    """Extract the Required Patterns markdown table from the template."""
    match = re.search(
        r"## Required Patterns.*?(?=\n## |\n```|\Z)",
        template,
        re.DOTALL,
    )
    return match.group(0) if match else ""
