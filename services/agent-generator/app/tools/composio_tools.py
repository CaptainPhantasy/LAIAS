"""
Composio Tools Integration

Provides access to 850+ integrations via Composio's unified API.
This is the KEY to full CrewAI parity - all enterprise integrations
available without CrewAI's paid AMP service.

Supported integrations include:
- Communication: Slack, Discord, Telegram, Gmail, Outlook, Teams
- Project Management: GitHub, Jira, Linear, Asana, Notion, ClickUp
- CRM: Salesforce, HubSpot, Zendesk
- Payments: Stripe, Shopify
- And 800+ more...
"""

import os
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()

_composio_loaded = False
_Composio: type | None = None
try:
    from composio import Composio as _ComposioImport
    from composio_crewai import ComposioTool  # noqa: F401

    _composio_loaded = True
    _Composio = _ComposioImport
    logger.info("composio_loaded", version="0.11.1")
except ImportError as e:
    logger.warning("composio_not_available", error=str(e))

COMPOSIO_AVAILABLE: bool = _composio_loaded


@dataclass
class ComposioConfig:
    """Configuration for Composio integration."""

    api_key: str | None = None
    base_url: str | None = None
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "ComposioConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("COMPOSIO_API_KEY"),
            base_url=os.getenv("COMPOSIO_BASE_URL"),
            enabled=os.getenv("COMPOSIO_ENABLED", "true").lower() == "true",
        )

    def is_available(self) -> bool:
        """Check if Composio is properly configured."""
        return COMPOSIO_AVAILABLE and self.enabled and bool(self.api_key)


class ComposioToolsManager:
    """
    Manager for Composio tools integration.

    Provides unified access to 850+ integrations through a single API.
    """

    # Popular toolkits for easy reference
    POPULAR_TOOLKITS = {
        # Communication
        "gmail": "Gmail - send emails, manage inbox, read messages",
        "slack": "Slack - send messages, read channels, manage workspace",
        "discord": "Discord - send messages, manage servers",
        "telegram": "Telegram - send messages, manage chats",
        "outlook": "Microsoft Outlook - email and calendar",
        "microsoft_teams": "MS Teams - messages and channels",
        # Project Management
        "github": "GitHub - repos, issues, PRs, workflows",
        "gitlab": "GitLab - repos, issues, pipelines",
        "jira": "Jira - issues, projects, sprints",
        "linear": "Linear - issues, projects, cycles",
        "asana": "Asana - tasks, projects, teams",
        "notion": "Notion - pages, databases, blocks",
        "clickup": "ClickUp - tasks, lists, spaces",
        "trello": "Trello - boards, cards, lists",
        # CRM & Support
        "salesforce": "Salesforce - accounts, opportunities, leads",
        "hubspot": "HubSpot - contacts, deals, tickets",
        "zendesk": "Zendesk - tickets, users, articles",
        "intercom": "Intercom - conversations, users",
        # Payments
        "stripe": "Stripe - payments, customers, subscriptions",
        "shopify": "Shopify - products, orders, customers",
        # Storage & Files
        "google_drive": "Google Drive - files, folders, sharing",
        "dropbox": "Dropbox - files, folders, sharing",
        "box": "Box - files, folders, sharing",
        "googlesheets": "Google Sheets - spreadsheets, data",
        # Calendar & Scheduling
        "google_calendar": "Google Calendar - events, scheduling",
        "calendly": "Calendly - scheduling, bookings",
        # Dev & Monitoring
        "sentry": "Sentry - errors, issues, releases",
        "pagerduty": "PagerDuty - incidents, alerts",
        # Social
        "twitter": "Twitter/X - tweets, DMs, timeline",
        "linkedin": "LinkedIn - posts, connections",
    }

    # Toolkit categories
    CATEGORIES = {
        "communication": ["gmail", "slack", "discord", "telegram", "outlook", "microsoft_teams"],
        "project_management": [
            "github",
            "gitlab",
            "jira",
            "linear",
            "asana",
            "notion",
            "clickup",
            "trello",
        ],
        "crm": ["salesforce", "hubspot", "zendesk", "intercom"],
        "payments": ["stripe", "shopify"],
        "storage": ["google_drive", "dropbox", "box", "googlesheets"],
        "calendar": ["google_calendar", "calendly"],
        "devops": ["sentry", "pagerduty"],
        "social": ["twitter", "linkedin"],
    }

    def __init__(self, config: ComposioConfig | None = None):
        """Initialize Composio tools manager."""
        self.config = config or ComposioConfig.from_env()
        self._client: Any | None = None
        self._connected_toolkits: dict[str, bool] = {}

    def _get_client(self) -> Any | None:
        """Get or create Composio client."""
        if not self.config.is_available():
            logger.warning("composio_not_configured")
            return None

        if self._client is None:
            try:
                if _Composio is None:
                    return None
                self._client = _Composio(api_key=self.config.api_key)
                logger.info("composio_client_initialized")
            except Exception as e:
                logger.error("composio_client_init_failed", error=str(e))
                return None

        return self._client

    def get_toolkits_by_category(self, category: str) -> list[str]:
        """Get toolkit names for a category."""
        return self.CATEGORIES.get(category, [])

    def get_toolkit_description(self, toolkit: str) -> str:
        """Get description for a toolkit."""
        return self.POPULAR_TOOLKITS.get(toolkit, f"Unknown toolkit: {toolkit}")

    def list_available_toolkits(self) -> dict[str, str]:
        """List all popular toolkits with descriptions."""
        return self.POPULAR_TOOLKITS.copy()

    def get_tools_for_toolkits(self, toolkits: list[str], user_id: str = "default") -> list[Any]:
        """
        Get CrewAI tools for specified toolkits.

        Args:
            toolkits: List of toolkit names (e.g., ["github", "slack"])
            user_id: User identifier for connection lookup

        Returns:
            List of CrewAI-compatible tools
        """
        if not COMPOSIO_AVAILABLE:
            logger.warning("composio_not_available_cannot_get_tools")
            return []

        client = self._get_client()
        if client is None:
            return []

        tools = []
        for toolkit in toolkits:
            try:
                # Get tools from Composio
                toolkit_tools = client.tools.get(user_id=user_id, toolkits=[toolkit.upper()])
                tools.extend(toolkit_tools)
                logger.info("composio_tools_loaded", toolkit=toolkit, count=len(toolkit_tools))
            except Exception as e:
                logger.warning("composio_toolkit_load_failed", toolkit=toolkit, error=str(e))

        return tools

    def get_tools_for_actions(self, actions: list[str], user_id: str = "default") -> list[Any]:
        """
        Get CrewAI tools for specific actions.

        Args:
            actions: List of action names (e.g., ["GITHUB_CREATE_ISSUE", "SLACK_SEND_MESSAGE"])
            user_id: User identifier for connection lookup

        Returns:
            List of CrewAI-compatible tools
        """
        if not COMPOSIO_AVAILABLE:
            return []

        client = self._get_client()
        if client is None:
            return []

        try:
            tools = client.tools.get(user_id=user_id, tools=actions)
            return tools
        except Exception as e:
            logger.error("composio_actions_load_failed", error=str(e))
            return []

    def get_auth_url(
        self, toolkit: str, user_id: str = "default", redirect_url: str | None = None
    ) -> str | None:
        """
        Get authentication URL for a toolkit.

        Args:
            toolkit: Toolkit name
            user_id: User identifier
            redirect_url: Optional redirect URL after auth

        Returns:
            Auth URL or None
        """
        client = self._get_client()
        if client is None:
            return None

        try:
            auth_connection = client.integrations.create(
                user_id=user_id, integration=toolkit.upper(), redirect_url=redirect_url
            )
            return auth_connection.redirect_url
        except Exception as e:
            logger.error("composio_auth_url_failed", toolkit=toolkit, error=str(e))
            return None

    def check_connection(self, toolkit: str, user_id: str = "default") -> bool:
        """Check if a toolkit is connected for a user."""
        client = self._get_client()
        if client is None:
            return False

        try:
            # Try to get entities/connections
            entities = client.connectedAccounts.get(user_id=user_id)
            return any(acc.toolkit == toolkit.upper() for acc in entities)
        except Exception as e:
            logger.warning(
                "composio_connection_check_failed",
                toolkit=toolkit,
                user_id=user_id,
                error=str(e),
                context="check_connection",
            )
            return False


def get_composio_manager() -> ComposioToolsManager:
    """Get the global Composio tools manager instance."""
    return ComposioToolsManager()


def get_composio_tools(toolkits: list[str], user_id: str = "default") -> list[Any]:
    """
    Convenience function to get Composio tools.

    Args:
        toolkits: List of toolkit names
        user_id: User identifier

    Returns:
        List of CrewAI-compatible tools
    """
    manager = get_composio_manager()
    return manager.get_tools_for_toolkits(toolkits, user_id)


# Code generation helpers
COMPOSIO_IMPORT_TEMPLATE = """
# Composio Integration - 850+ tools via unified API
from composio import Composio
from composio_crewai import ComposioTool

# Initialize Composio client
composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))

# Get tools for specific integrations
composio_tools = composio.tools.get(
    user_id="default",
    toolkits=["{toolkits}"]
)
"""

COMPOSIO_AGENT_TEMPLATE = """
# Agent with Composio tools
agent = Agent(
    role="{role}",
    goal="{goal}",
    backstory="{backstory}",
    tools=composio.tools.get(
        user_id="default",
        toolkits={toolkits_list}
    ),
    llm=LLM(model="{model}")
)
"""


def generate_composio_code(
    toolkits: list[str],
    agent_role: str = "Integration Agent",
    agent_goal: str = "Integrate with external services",
    model: str = "gpt-4o",
) -> str:
    """
    Generate code snippet for Composio integration.

    Args:
        toolkits: List of toolkit names
        agent_role: Role for the agent
        agent_goal: Goal for the agent
        model: LLM model to use

    Returns:
        Python code string
    """
    toolkits_str = ", ".join(f'"{t.upper()}"' for t in toolkits)

    return f'''
# =============================================================================
# COMPOSIO INTEGRATION - {len(toolkits)} TOOLKIT(S)
# =============================================================================

import os
from composio import Composio
from crewai import Agent, LLM

# Initialize Composio
composio = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))

# Get tools for requested integrations
composio_tools = composio.tools.get(
    user_id="default",
    toolkits=[{toolkits_str}]
)

print(f"Loaded {{len(composio_tools)}} tools from Composio")

# Agent with Composio tools
agent = Agent(
    role="{agent_role}",
    goal="{agent_goal}",
    backstory="Expert at integrating with external services using Composio.",
    tools=composio_tools,
    llm=LLM(model="{model}")
)
'''
