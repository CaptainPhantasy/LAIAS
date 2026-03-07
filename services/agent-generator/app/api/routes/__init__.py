"""API routes for Agent Generator."""

from . import agents, auth, generate, health, teams, templates, tools, users, validate

# business_dev routes disabled - functionality moved to Docker Orchestrator
# from . import business_dev

__all__ = ["agents", "auth", "generate", "health", "templates", "tools", "users", "teams", "validate"]
