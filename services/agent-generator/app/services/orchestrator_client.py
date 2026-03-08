"""
Internal HTTP client for Agent Generator → Docker Orchestrator handoff.

Enables server-side deployment without frontend bridging.
Uses Docker DNS (docker-orchestrator:8002) when running in Docker,
falls back to localhost:4522 for local development.
"""

import os
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

# Docker Compose network: agent-generator can reach docker-orchestrator:8002
# Local dev: fall back to localhost:4522
ORCHESTRATOR_URL = os.environ.get(
    "DOCKER_ORCHESTRATOR_URL",
    "http://docker-orchestrator:8002",
)


class OrchestratorClient:
    """Async HTTP client for the Docker Orchestrator service."""

    def __init__(self, base_url: str = ORCHESTRATOR_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def deploy_agent(
        self,
        agent_id: str,
        agent_name: str,
        flow_code: str,
        agents_yaml: str,
        requirements: list[str] | None = None,
        environment_vars: dict[str, str] | None = None,
        output_config: dict[str, bool] | None = None,
        output_path: str | None = None,
        output_format: str = "markdown",
        input_volumes: list[dict[str, str]] | None = None,
        auto_start: bool = True,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
    ) -> dict[str, Any]:
        """
        Deploy an agent by calling the Docker Orchestrator's /api/deploy endpoint.

        Returns the deployment response dict on success.
        Raises OrchestratorError on failure.
        """
        payload = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "flow_code": flow_code,
            "agents_yaml": agents_yaml,
            "requirements": requirements or [],
            "environment_vars": environment_vars or {},
            "output_config": output_config or {"postgres": True, "files": True},
            "output_path": output_path,
            "output_format": output_format,
            "input_volumes": input_volumes or [],
            "auto_start": auto_start,
            "memory_limit": memory_limit,
            "cpu_limit": cpu_limit,
        }

        logger.info(
            "Orchestrator handoff: deploying agent",
            agent_id=agent_id,
            orchestrator_url=self.base_url,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/deploy",
                json=payload,
            )

        if response.status_code == 201:
            result = response.json()
            logger.info(
                "Orchestrator handoff: deployment successful",
                agent_id=agent_id,
                deployment_id=result.get("deployment_id"),
                container_id=result.get("container_id"),
            )
            return result

        # Deployment failed
        error_detail = ""
        try:
            error_body = response.json()
            error_detail = error_body.get("message") or error_body.get("detail") or str(error_body)
        except Exception as e:
            logger.error(
                "Orchestrator handoff: failed to parse error response",
                agent_id=agent_id,
                status_code=response.status_code,
                error=str(e),
                context="deploy_agent_error_parse",
            )
            error_detail = response.text[:500]

        logger.error(
            "Orchestrator handoff: deployment failed",
            agent_id=agent_id,
            status_code=response.status_code,
            error=error_detail,
        )
        raise OrchestratorError(f"Deployment failed (HTTP {response.status_code}): {error_detail}")

    async def health_check(self) -> dict[str, Any]:
        """Check orchestrator health."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/health")
        return response.json()


class OrchestratorError(Exception):
    """Raised when the Docker Orchestrator returns an error."""

    pass


# Singleton
_client: OrchestratorClient | None = None


def get_orchestrator_client() -> OrchestratorClient:
    """Get singleton orchestrator client."""
    global _client
    if _client is None:
        _client = OrchestratorClient()
    return _client
