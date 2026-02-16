"""
Automation Tools Configuration

Tools for workflow automation and external service integration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class AutomationToolsConfig:
    """Configuration for Automation tools."""

    # Apify settings
    apify_timeout_secs: int = 300
    apify_memory_mbytes: int = 2048

    # Composio settings
    composio_integration_ids: List[str] = field(default_factory=list)

    # MultiOn settings
    multion_timeout: int = 60
    multion_headless: bool = True

    # Zapier settings
    zapier_actions: List[str] = field(default_factory=list)

    # n8n settings
    n8n_timeout: int = 300

    # Make settings
    make_scenario_ids: List[str] = field(default_factory=list)

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
        """Get all Automation tool configurations."""
        return [
            # Web Automation
            ToolConfig(
                name="ApifyActorTool",
                import_path="crewai_tools.ApifyActorTool",
                category=ToolCategory.AUTOMATION,
                description="Run Apify actors for web automation",
                required_env_vars=["APIFY_API_KEY"],
                dependencies=["apify-client"],
            ),
            ToolConfig(
                name="MultiOnTool",
                import_path="crewai_tools.MultiOnTool",
                category=ToolCategory.AUTOMATION,
                description="Browser automation with MultiOn",
                required_env_vars=["MULTION_API_KEY"],
            ),
            ToolConfig(
                name="StagehandTool",
                import_path="crewai_tools.StagehandTool",
                category=ToolCategory.AUTOMATION,
                description="AI-powered browser automation",
                dependencies=["stagehand"],
            ),
            ToolConfig(
                name="BrowserbaseTool",
                import_path="crewai_tools.BrowserbaseTool",
                category=ToolCategory.AUTOMATION,
                description="Browser automation with Browserbase",
                required_env_vars=["BROWSERBASE_API_KEY"],
            ),

            # Integration Platforms
            ToolConfig(
                name="ComposioTool",
                import_path="crewai_tools.ComposioTool",
                category=ToolCategory.AUTOMATION,
                description="Integrate with 100+ apps via Composio",
                required_env_vars=["COMPOSIO_API_KEY"],
                dependencies=["composio-client"],
            ),
            ToolConfig(
                name="ZapierActionsTool",
                import_path="crewai_tools.ZapierActionsTool",
                category=ToolCategory.AUTOMATION,
                description="Connect to Zapier actions",
                required_env_vars=["ZAPIER_NLA_API_KEY"],
            ),
            ToolConfig(
                name="N8nTool",
                import_path="crewai_tools.N8nTool",
                category=ToolCategory.AUTOMATION,
                description="Trigger n8n workflows",
                required_env_vars=["N8N_WEBHOOK_URL"],
            ),
            ToolConfig(
                name="MakeTool",
                import_path="crewai_tools.MakeTool",
                category=ToolCategory.AUTOMATION,
                description="Integrate with Make.com scenarios",
                required_env_vars=["MAKE_API_KEY"],
            ),
            ToolConfig(
                name="PipedreamTool",
                import_path="crewai_tools.PipedreamTool",
                category=ToolCategory.AUTOMATION,
                description="Trigger Pipedream workflows",
                required_env_vars=["PIPEDREAM_API_KEY"],
            ),

            # RPA Tools
            ToolConfig(
                name="UiPathTool",
                import_path="crewai_tools.UiPathTool",
                category=ToolCategory.AUTOMATION,
                description="UiPath RPA integration",
                required_env_vars=["UIPATH_CLIENT_ID", "UIPATH_CLIENT_SECRET"],
            ),
            ToolConfig(
                name="AutomationAnywhereTool",
                import_path="crewai_tools.AutomationAnywhereTool",
                category=ToolCategory.AUTOMATION,
                description="Automation Anywhere integration",
                required_env_vars=["AA_CONTROL_ROOM_URL", "AA_API_KEY"],
            ),

            # Scheduler Tools
            ToolConfig(
                name="CronTool",
                import_path="crewai_tools.CronTool",
                category=ToolCategory.AUTOMATION,
                description="Schedule cron jobs",
            ),
            ToolConfig(
                name="TemporalTool",
                import_path="crewai_tools.TemporalTool",
                category=ToolCategory.AUTOMATION,
                description="Temporal workflow integration",
                required_env_vars=["TEMPORAL_ADDRESS"],
                dependencies=["temporalio"],
            ),

            # Notification Tools
            ToolConfig(
                name="PagerDutyTool",
                import_path="crewai_tools.PagerDutyTool",
                category=ToolCategory.AUTOMATION,
                description="PagerDuty incident management",
                required_env_vars=["PAGERDUTY_API_KEY"],
            ),
            ToolConfig(
                name="OpsgenieTool",
                import_path="crewai_tools.OpsgenieTool",
                category=ToolCategory.AUTOMATION,
                description="Opsgenie alerting",
                required_env_vars=["OPSGENIE_API_KEY"],
            ),
            ToolConfig(
                name="VictorOpsTool",
                import_path="crewai_tools.VictorOpsTool",
                category=ToolCategory.AUTOMATION,
                description="VictorOps incident management",
                required_env_vars=["VICTOROPS_API_KEY"],
            ),
        ]

    def get_automation_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
        """
        Get instantiated automation tools.

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

    def get_apify_config(self) -> Dict[str, Any]:
        """Get Apify configuration."""
        return {
            "timeout_secs": self.apify_timeout_secs,
            "memory_mbytes": self.apify_memory_mbytes,
        }

    def get_multion_config(self) -> Dict[str, Any]:
        """Get MultiOn configuration."""
        return {
            "timeout": self.multion_timeout,
            "headless": self.multion_headless,
        }
