"""
================================================================================
                    DASES PIPELINE — AGENT FACTORY
================================================================================
Factory functions for creating the 8 DASES pipeline agents.
Each agent is configured with role, goal, backstory, and LLM settings.
Default LLM: GLM via ZAI (OpenAI-compatible endpoint).
================================================================================
"""

from crewai import Agent, LLM
from typing import Optional
import os
import structlog

from .prompts import (
    DEEP_PLANNER_BACKSTORY,
    DEEP_PLANNER_GOAL,
    DEEP_THINKER_BACKSTORY,
    DEEP_THINKER_GOAL,
    SCAFFOLDING_EXPERT_BACKSTORY,
    SCAFFOLDING_EXPERT_GOAL,
    DATABASE_SPECIALIST_BACKSTORY,
    DATABASE_SPECIALIST_GOAL,
    CODING_EXPERT_BACKSTORY,
    CODING_EXPERT_GOAL,
    FRONTEND_DESIGNER_BACKSTORY,
    FRONTEND_DESIGNER_GOAL,
    RELEASE_DOCUMENTARIAN_BACKSTORY,
    RELEASE_DOCUMENTARIAN_GOAL,
    CRITIC_BACKSTORY,
    CRITIC_GOAL,
)
from .state import DASESConfig

logger = structlog.get_logger()


# =============================================================================
# LLM CONFIGURATION
# =============================================================================

def get_llm(config: Optional[DASESConfig] = None) -> LLM:
    """
    Create an LLM instance configured for the DASES pipeline.

    Litellm-native provider routing — model prefix determines provider:
      openrouter/...  → OpenRouter (OPENROUTER_API_KEY)
      deepseek/...    → DeepSeek  (DEEPSEEK_API_KEY)
      anthropic/...   → Anthropic (ANTHROPIC_API_KEY)
      openai/...      → OpenAI   (OPENAI_API_KEY)
      mistral/...     → Mistral  (MISTRAL_API_KEY)
      (no prefix)     → ZAI/OpenAI-compatible via custom base_url

    Returns:
        Configured CrewAI LLM instance
    """
    cfg = config or DASESConfig()
    model = os.getenv("LLM_MODEL", os.getenv("DEFAULT_MODEL", cfg.default_model))

    # Litellm-native providers — no custom base_url needed
    NATIVE_PREFIXES = (
        "openrouter/", "deepseek/", "anthropic/", "mistral/",
        "openai/", "ollama/", "groq/", "xai/",
    )

    if model.startswith(NATIVE_PREFIXES):
        llm = LLM(
            model=model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
        logger.info("LLM configured (native provider)", model=model)
    else:
        # Fallback: OpenAI-compatible endpoint (ZAI, local, etc.)
        api_key = (
            os.getenv("ZAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("LLM_API_KEY", "")
        )
        api_base = os.getenv(
            "ZAI_API_BASE",
            os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        )
        if not model.startswith("openai/"):
            model = f"openai/{model}"
        llm = LLM(
            model=model,
            api_key=api_key,
            base_url=api_base,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
        logger.info("LLM configured (custom endpoint)", model=model, base_url=api_base)

    return llm


# =============================================================================
# AGENT FACTORY
# =============================================================================

def create_deep_planner(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 1: Senior Requirements Architect."""
    return Agent(
        role="Deep Planner — Senior Requirements Architect",
        goal=DEEP_PLANNER_GOAL,
        backstory=DEEP_PLANNER_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_deep_thinker(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 2: Senior Technical Blocker Finder."""
    return Agent(
        role="Deep Thinker — Senior Technical Blocker Finder",
        goal=DEEP_THINKER_GOAL,
        backstory=DEEP_THINKER_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_scaffolding_expert(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 3: Dependencies & Project Structure Architect."""
    return Agent(
        role="Scaffolding Expert — Dependencies & Project Structure Architect",
        goal=SCAFFOLDING_EXPERT_GOAL,
        backstory=SCAFFOLDING_EXPERT_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_database_specialist(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 4: Data Architecture Engineer."""
    return Agent(
        role="Database Specialist — Data Architecture Engineer",
        goal=DATABASE_SPECIALIST_GOAL,
        backstory=DATABASE_SPECIALIST_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_coding_expert(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 5: Principal Software Engineer."""
    return Agent(
        role="Coding Expert — Principal Software Engineer",
        goal=CODING_EXPERT_GOAL,
        backstory=CODING_EXPERT_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_frontend_designer(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 6: Senior UI/UX Engineer."""
    return Agent(
        role="Frontend Designer — Senior UI/UX Engineer",
        goal=FRONTEND_DESIGNER_GOAL,
        backstory=FRONTEND_DESIGNER_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_release_documentarian(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 7: Technical Writer & Release Manager."""
    return Agent(
        role="Release Documentarian — Technical Writer & Release Manager",
        goal=RELEASE_DOCUMENTARIAN_GOAL,
        backstory=RELEASE_DOCUMENTARIAN_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


def create_critic(config: Optional[DASESConfig] = None) -> Agent:
    """Agent 8: Senior QA & Release Engineer (The Critic)."""
    return Agent(
        role="The Critic — Senior QA & Release Engineer",
        goal=CRITIC_GOAL,
        backstory=CRITIC_BACKSTORY,
        llm=get_llm(config),
        verbose=True,
        allow_delegation=False,
        memory=True,
    )


# =============================================================================
# CONVENIENCE: ALL AGENTS
# =============================================================================

AGENT_FACTORIES = {
    "planner": create_deep_planner,
    "thinker": create_deep_thinker,
    "scaffolder": create_scaffolding_expert,
    "database": create_database_specialist,
    "coder": create_coding_expert,
    "frontend": create_frontend_designer,
    "documentarian": create_release_documentarian,
    "critic": create_critic,
}
