"""
Integration Tools Configuration

Tools for integrating with external services and platforms.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class IntegrationToolsConfig:
    """Configuration for Integration tools."""

    # Communication tools settings
    slack_channel: Optional[str] = None
    discord_channel: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Email settings
    smtp_from_email: Optional[str] = None
    email_template_dir: str = "./templates/email"

    # Project management settings
    jira_project_key: Optional[str] = None
    linear_team_id: Optional[str] = None
    asana_workspace_id: Optional[str] = None
    trello_board_id: Optional[str] = None

    # CRM settings
    hubspot_portal_id: Optional[str] = None
    salesforce_sandbox: bool = False

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
        """Get all Integration tool configurations."""
        return [
            # Communication - Chat
            ToolConfig(
                name="SlackTool",
                import_path="crewai_tools.SlackTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Slack",
                required_env_vars=["SLACK_BOT_TOKEN"],
                dependencies=["slack-sdk"],
            ),
            ToolConfig(
                name="DiscordTool",
                import_path="crewai_tools.DiscordTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Discord",
                required_env_vars=["DISCORD_BOT_TOKEN"],
                dependencies=["discord.py"],
            ),
            ToolConfig(
                name="TelegramTool",
                import_path="crewai_tools.TelegramTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Telegram",
                required_env_vars=["TELEGRAM_BOT_TOKEN"],
                dependencies=["python-telegram-bot"],
            ),
            ToolConfig(
                name="MicrosoftTeamsTool",
                import_path="crewai_tools.MicrosoftTeamsTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Microsoft Teams",
                required_env_vars=["TEAMS_WEBHOOK_URL"],
            ),

            # Communication - Email
            ToolConfig(
                name="EmailTool",
                import_path="crewai_tools.EmailTool",
                category=ToolCategory.INTEGRATION,
                description="Send and read emails",
                required_env_vars=["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"],
            ),
            ToolConfig(
                name="SendgridTool",
                import_path="crewai_tools.SendgridTool",
                category=ToolCategory.INTEGRATION,
                description="Send emails via SendGrid",
                required_env_vars=["SENDGRID_API_KEY"],
                dependencies=["sendgrid"],
            ),
            ToolConfig(
                name="MailgunTool",
                import_path="crewai_tools.MailgunTool",
                category=ToolCategory.INTEGRATION,
                description="Send emails via Mailgun",
                required_env_vars=["MAILGUN_API_KEY", "MAILGUN_DOMAIN"],
            ),
            ToolConfig(
                name="PostmarkTool",
                import_path="crewai_tools.PostmarkTool",
                category=ToolCategory.INTEGRATION,
                description="Send emails via Postmark",
                required_env_vars=["POSTMARK_API_KEY"],
            ),

            # Documentation & Knowledge
            ToolConfig(
                name="NotionTool",
                import_path="crewai_tools.NotionTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Notion",
                required_env_vars=["NOTION_API_KEY"],
                dependencies=["notion-client"],
            ),
            ToolConfig(
                name="ConfluenceTool",
                import_path="crewai_tools.ConfluenceTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Confluence",
                required_env_vars=["CONFLUENCE_URL", "CONFLUENCE_API_TOKEN"],
                dependencies=["atlassian-python-api"],
            ),
            ToolConfig(
                name="GoogleDocsTool",
                import_path="crewai_tools.GoogleDocsTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Google Docs",
                required_env_vars=["GOOGLE_APPLICATION_CREDENTIALS"],
                dependencies=["google-api-python-client"],
            ),
            ToolConfig(
                name="CodaTool",
                import_path="crewai_tools.CodaTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Coda docs",
                required_env_vars=["CODA_API_KEY"],
            ),

            # Project Management
            ToolConfig(
                name="JiraTool",
                import_path="crewai_tools.JiraTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Jira",
                required_env_vars=["JIRA_API_TOKEN", "JIRA_EMAIL", "JIRA_DOMAIN"],
                dependencies=["atlassian-python-api"],
            ),
            ToolConfig(
                name="LinearTool",
                import_path="crewai_tools.LinearTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Linear",
                required_env_vars=["LINEAR_API_KEY"],
                dependencies=["linear-client"],
            ),
            ToolConfig(
                name="AsanaTool",
                import_path="crewai_tools.AsanaTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Asana",
                required_env_vars=["ASANA_ACCESS_TOKEN"],
                dependencies=["asana"],
            ),
            ToolConfig(
                name="TrelloTool",
                import_path="crewai_tools.TrelloTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Trello",
                required_env_vars=["TRELLO_API_KEY", "TRELLO_TOKEN"],
                dependencies=["trello"],
            ),
            ToolConfig(
                name="MondayTool",
                import_path="crewai_tools.MondayTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Monday.com",
                required_env_vars=["MONDAY_API_KEY"],
            ),
            ToolConfig(
                name="ClickUpTool",
                import_path="crewai_tools.ClickUpTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with ClickUp",
                required_env_vars=["CLICKUP_API_KEY"],
            ),

            # CRM
            ToolConfig(
                name="HubspotTool",
                import_path="crewai_tools.HubspotTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with HubSpot CRM",
                required_env_vars=["HUBSPOT_API_KEY"],
                dependencies=["hubspot-api-client"],
            ),
            ToolConfig(
                name="SalesforceTool",
                import_path="crewai_tools.SalesforceTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Salesforce",
                required_env_vars=["SALESFORCE_USERNAME", "SALESFORCE_PASSWORD", "SALESFORCE_SECURITY_TOKEN"],
                dependencies=["simple-salesforce"],
            ),
            ToolConfig(
                name="PipedriveTool",
                import_path="crewai_tools.PipedriveTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Pipedrive",
                required_env_vars=["PIPEDRIVE_API_KEY"],
            ),
            ToolConfig(
                name="CloseTool",
                import_path="crewai_tools.CloseTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Close CRM",
                required_env_vars=["CLOSE_API_KEY"],
            ),

            # Support & Tickets
            ToolConfig(
                name="ZendeskTool",
                import_path="crewai_tools.ZendeskTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Zendesk",
                required_env_vars=["ZENDESK_EMAIL", "ZENDESK_API_TOKEN", "ZENDESK_DOMAIN"],
                dependencies=["zendesk"],
            ),
            ToolConfig(
                name="FreshdeskTool",
                import_path="crewai_tools.FreshdeskTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Freshdesk",
                required_env_vars=["FRESHDESK_API_KEY", "FRESHDESK_DOMAIN"],
            ),
            ToolConfig(
                name="IntercomTool",
                import_path="crewai_tools.IntercomTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Intercom",
                required_env_vars=["INTERCOM_ACCESS_TOKEN"],
            ),

            # Payments
            ToolConfig(
                name="StripeTool",
                import_path="crewai_tools.StripeTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Stripe payments",
                required_env_vars=["STRIPE_API_KEY"],
                dependencies=["stripe"],
            ),
            ToolConfig(
                name="PayPalTool",
                import_path="crewai_tools.PayPalTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with PayPal",
                required_env_vars=["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"],
            ),
            ToolConfig(
                name="SquareTool",
                import_path="crewai_tools.SquareTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Square",
                required_env_vars=["SQUARE_ACCESS_TOKEN"],
            ),

            # Social Media
            ToolConfig(
                name="TwitterTool",
                import_path="crewai_tools.TwitterTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Twitter/X",
                required_env_vars=["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
                dependencies=["tweepy"],
            ),
            ToolConfig(
                name="LinkedInTool",
                import_path="crewai_tools.LinkedInTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with LinkedIn",
                required_env_vars=["LINKEDIN_ACCESS_TOKEN"],
                dependencies=["linkedin-api"],
            ),
            ToolConfig(
                name="InstagramTool",
                import_path="crewai_tools.InstagramTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Instagram",
                required_env_vars=["INSTAGRAM_ACCESS_TOKEN"],
            ),
            ToolConfig(
                name="FacebookTool",
                import_path="crewai_tools.FacebookTool",
                category=ToolCategory.INTEGRATION,
                description="Interact with Facebook",
                required_env_vars=["FACEBOOK_ACCESS_TOKEN"],
                dependencies=["facebook-sdk"],
            ),

            # Analytics
            ToolConfig(
                name="GoogleAnalyticsTool",
                import_path="crewai_tools.GoogleAnalyticsTool",
                category=ToolCategory.INTEGRATION,
                description="Query Google Analytics",
                required_env_vars=["GOOGLE_APPLICATION_CREDENTIALS", "GA_PROPERTY_ID"],
                dependencies=["google-analytics-data"],
            ),
            ToolConfig(
                name="MixpanelTool",
                import_path="crewai_tools.MixpanelTool",
                category=ToolCategory.INTEGRATION,
                description="Query Mixpanel analytics",
                required_env_vars=["MIXPANEL_API_KEY", "MIXPANEL_PROJECT_ID"],
            ),
            ToolConfig(
                name="AmplitudeTool",
                import_path="crewai_tools.AmplitudeTool",
                category=ToolCategory.INTEGRATION,
                description="Query Amplitude analytics",
                required_env_vars=["AMPLITUDE_API_KEY"],
            ),

            # Developer Tools
            ToolConfig(
                name="GithubTool",
                import_path="crewai_tools.GithubTool",
                category=ToolCategory.INTEGRATION,
                description="GitHub operations",
                required_env_vars=["GITHUB_TOKEN"],
                dependencies=["PyGithub"],
            ),
            ToolConfig(
                name="GitlabTool",
                import_path="crewai_tools.GitlabTool",
                category=ToolCategory.INTEGRATION,
                description="GitLab operations",
                required_env_vars=["GITLAB_TOKEN"],
                dependencies=["python-gitlab"],
            ),
            ToolConfig(
                name="BitbucketTool",
                import_path="crewai_tools.BitbucketTool",
                category=ToolCategory.INTEGRATION,
                description="Bitbucket operations",
                required_env_vars=["BITBUCKET_USERNAME", "BITBUCKET_APP_PASSWORD"],
            ),
            ToolConfig(
                name="DockerTool",
                import_path="crewai_tools.DockerTool",
                category=ToolCategory.INTEGRATION,
                description="Docker operations",
                dependencies=["docker"],
            ),
            ToolConfig(
                name="KubernetesTool",
                import_path="crewai_tools.KubernetesTool",
                category=ToolCategory.INTEGRATION,
                description="Kubernetes operations",
                dependencies=["kubernetes"],
            ),
        ]

    def get_integration_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
        """
        Get instantiated integration tools.

        Args:
            env_vars: Environment variables for configuration

        Returns:
            List of tool instances
        """
        from app.tools.registry import get_tool_registry

        registry = get_tool_registry()
        env = env_vars or dict(os.environ)

        tools = []
        for config in self.get_tool_configs():
            if config.is_available(env):
                try:
                    tool = registry.instantiate_tool(config.name)
                    tools.append(tool)
                except Exception:
                    pass

        return tools

    def get_slack_config(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Get Slack configuration."""
        return {
            "bot_token": env_vars.get("SLACK_BOT_TOKEN"),
            "default_channel": self.slack_channel,
        }

    def get_jira_config(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Get Jira configuration."""
        return {
            "api_token": env_vars.get("JIRA_API_TOKEN"),
            "email": env_vars.get("JIRA_EMAIL"),
            "domain": env_vars.get("JIRA_DOMAIN"),
            "project_key": self.jira_project_key,
        }

    def get_hubspot_config(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Get HubSpot configuration."""
        return {
            "api_key": env_vars.get("HUBSPOT_API_KEY"),
            "portal_id": self.hubspot_portal_id,
        }
