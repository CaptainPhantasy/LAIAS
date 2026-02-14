"""
Prompt templates and system prompts for LLM code generation.

Includes system prompts, few-shot examples, and Godzilla template reference.
"""

from app.prompts.system_prompts import SYSTEM_PROMPT, CODE_GENERATION_SYSTEM_PROMPT
from app.prompts.few_shot_examples import FEW_SHOT_SELECTOR, get_few_shot_examples
from app.prompts.godzilla_template import GODZILLA_TEMPLATE_REFERENCE

__all__ = [
    "SYSTEM_PROMPT",
    "CODE_GENERATION_SYSTEM_PROMPT",
    "FEW_SHOT_SELECTOR",
    "get_few_shot_examples",
    "GODZILLA_TEMPLATE_REFERENCE",
]
