"""
Helper functions for Agent Generator Service.

Provides utility functions for ID generation, sanitization,
and common operations.
"""

import re
import secrets
from datetime import datetime


def generate_agent_id() -> str:
    """
    Generate a unique agent ID.

    Returns:
        Agent ID in format 'gen_' + random hex
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(4)
    return f"gen_{timestamp}_{random_suffix}"


def sanitize_agent_name(name: str) -> str:
    """
    Sanitize agent name to be a valid Python identifier.

    Args:
        name: Raw agent name

    Returns:
        Sanitized name
    """
    # Remove invalid characters
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "", name)
    # Ensure starts with letter
    if sanitized and sanitized[0].isdigit():
        sanitized = "Agent_" + sanitized
    # Handle empty result
    if not sanitized:
        sanitized = "GeneratedAgent"
    return sanitized


def extract_code_from_markdown(content: str) -> str:
    """
    Extract Python code from markdown code blocks.

    Args:
        content: Content possibly containing markdown code blocks

    Returns:
        Extracted Python code
    """
    # Match ```python ... ``` or ``` ... ``` blocks
    pattern = r"```(?:python)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)

    if matches:
        # Return the first match if found
        return matches[0].strip()

    # If no code blocks found, return original content
    return content.strip()


def validate_requirements(reqs: list) -> list:
    """
    Validate and normalize Python package requirements.

    Args:
        reqs: List of requirement strings

    Returns:
        Normalized list of requirements
    """
    normalized = []
    known_patterns = [
        r"^crewai(\[tools\])?>=\d+\.\d+\.\d+",
        r"^pydantic>=\d+\.\d+\.\d+",
        r"^structlog>=\d+\.\d+\.\d+",
        r"^openai>=",
        r"^anthropic>=",
    ]

    for req in reqs:
        req = req.strip()
        if req:
            normalized.append(req)

    return normalized


def calculate_cost_estimate(
    complexity: str,
    agent_count: int,
    model: str = "gpt-4o"
) -> dict:
    """
    Calculate estimated cost per agent run.

    Args:
        complexity: Complexity level
        agent_count: Number of agents
        model: Model name

    Returns:
        Dictionary with cost estimate details
    """
    # Base costs per 1M tokens (approximate 2026 pricing)
    costs = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    }

    model_costs = costs.get(model, costs["gpt-4o"])

    # Estimate tokens based on complexity and agent count
    complexity_multipliers = {
        "simple": 1000,
        "moderate": 3000,
        "complex": 6000,
    }

    base_tokens = complexity_multipliers.get(complexity, 3000)
    total_tokens = base_tokens * agent_count

    # Assume 50/50 split input/output
    input_tokens = total_tokens // 2
    output_tokens = total_tokens // 2

    input_cost = (input_tokens / 1_000_000) * model_costs["input"]
    output_cost = (output_tokens / 1_000_000) * model_costs["output"]
    total_cost = input_cost + output_cost

    return {
        "estimated_cost_usd": round(total_cost, 4),
        "token_estimate": total_tokens,
        "api_call_estimate": agent_count * 2,  # Each agent makes ~2 calls
        "confidence": 0.7  # 70% confidence in estimate
    }


def format_mermaid_diagram(
    entry_point: str,
    steps: list,
    decision_points: dict = None
) -> str:
    """
    Format a Mermaid flow diagram.

    Args:
        entry_point: Entry point name
        steps: List of step names
        decision_points: Dict of decision point -> options

    Returns:
        Mermaid diagram string
    """
    lines = ["graph TD", f"    A[{entry_point}]"]

    current = "A"
    for i, step in enumerate(steps, 1):
        node = chr(65 + i)  # B, C, D, ...
        lines.append(f"    {current} --> {node}[{step}]")
        current = node

    if decision_points:
        for point, options in decision_points.items():
            decision_node = chr(65 + len(steps) + 1)
            lines.append(f"    {current} --> {decision_node}{{{{{point}}}}}")
            for j, option in enumerate(options):
                result_node = chr(65 + len(steps) + 2 + j)
                lines.append(f"    {decision_node} --> |{option}| {result_node}[{option}]")

    lines.append("")

    return "\n".join(lines)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
