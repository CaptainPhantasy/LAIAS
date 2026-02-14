"""
Container lifecycle management service.

Provides high-level operations for managing agent containers
including creation, start, stop, restart, and removal.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

import docker
from docker.errors import DockerException, NotFound
import structlog

from app.services.docker_service import DockerService
from app.config import settings


logger = structlog.get_logger()


class ContainerManager:
    """
    High-level container lifecycle management.

    Builds on DockerService to provide operations like:
    - Batch container operations
    - Container state queries
    - Health check management
    - Auto-restart logic
    """

    def __init__(self):
        self.docker_service = DockerService()

    async def create_and_start(
        self,
        deployment_id: str,
        agent_id: str,
        agent_name: str,
        flow_code: str,
        agents_yaml: str,
        requirements: List[str] = None,
        environment_vars: Dict[str, str] = None,
        cpu_limit: float = 1.0,
        memory_limit: str = "512m",
    ) -> Dict[str, Any]:
        """
        Create and start a container in one operation.

        Returns:
            Container information dict
        """
        container = await self.docker_service.deploy_agent(
            deployment_id=deployment_id,
            agent_id=agent_id,
            agent_name=agent_name,
            flow_code=flow_code,
            agents_yaml=agents_yaml,
            requirements=requirements,
            environment_vars=environment_vars,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
        )

        await self.docker_service.start_container(container.id)

        container.reload()

        return {
            "container_id": container.id,
            "container_name": container.name,
            "status": container.status,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

    async def restart_container(
        self, container_id: str, timeout: int = 10
    ) -> None:
        """Restart a container."""
        await self.docker_service.stop_container(container_id, timeout=timeout)
        await asyncio.sleep(1)  # Brief pause
        await self.docker_service.start_container(container_id)
        logger.info("Container restarted", container_id=container_id)

    async def get_container_state(self, container_id: str) -> Dict[str, Any]:
        """
        Get comprehensive container state.

        Returns:
            Dict with status, health, uptime, metrics
        """
        container = await self.docker_service.get_container(container_id)
        if not container:
            raise NotFound(f"Container {container_id} not found")

        container.reload()

        # Get stats if running
        stats = None
        if container.status == "running":
            stats = await self.docker_service.get_container_stats(container_id)

        # Calculate uptime
        created = datetime.fromisoformat(container.attrs["Created"].replace("Z", "+00:00"))
        uptime_seconds = (datetime.utcnow() - created).total_seconds()

        return {
            "container_id": container.id,
            "name": container.name,
            "status": container.status,
            "health": self._get_health_status(container),
            "uptime_seconds": int(uptime_seconds),
            "metrics": stats,
            "labels": container.labels,
        }

    def _get_health_status(self, container) -> str:
        """Get container health status."""
        health = container.attrs.get("State", {}).get("Health", {})
        return health.get("Status", "unknown")

    async def get_deployment_containers(
        self, deployment_id: str
    ) -> List[Dict[str, Any]]:
        """Get all containers for a specific deployment."""
        all_containers = await self.docker_service.list_containers(all=True)

        return [
            c for c in all_containers
            if c.get("deployment_id") == deployment_id
        ]

    async def stop_all_deployment_containers(
        self, deployment_id: str
    ) -> int:
        """Stop all containers for a deployment. Returns count stopped."""
        containers = await self.get_deployment_containers(deployment_id)
        stopped = 0

        for container in containers:
            if container["status"] == "running":
                try:
                    await self.docker_service.stop_container(container["container_id"])
                    stopped += 1
                except Exception as e:
                    logger.warning(
                        "Failed to stop container",
                        container_id=container["container_id"],
                        error=str(e),
                    )

        return stopped

    async def remove_deployment(self, deployment_id: str) -> int:
        """Remove all containers and resources for a deployment. Returns count removed."""
        containers = await self.get_deployment_containers(deployment_id)
        removed = 0

        for container in containers:
            try:
                await self.docker_service.remove_container(
                    container["container_id"], force=True
                )
                removed += 1
            except Exception as e:
                logger.warning(
                    "Failed to remove container",
                    container_id=container["container_id"],
                    error=str(e),
                )

        return removed

    async def get_container_logs_since(
        self, container_id: str, since_seconds: int = 300
    ) -> List[str]:
        """Get logs from the last N seconds."""
        from datetime import timedelta

        since = datetime.utcnow() - timedelta(seconds=since_seconds)
        since_str = since.isoformat() + "Z"

        return await self.docker_service.get_container_logs(
            container_id=container_id,
            tail=0,  # No tail limit
            since=since_str,
        )

    async def execute_in_container(
        self, container_id: str, command: str
    ) -> Dict[str, Any]:
        """
        Execute a command inside a running container.

        Returns:
            Dict with exit_code, output
        """
        container = await self.docker_service.get_container(container_id)
        if not container:
            raise NotFound(f"Container {container_id} not found")

        try:
            result = container.exec_run(command)
            return {
                "exit_code": result.exit_code,
                "output": result.output.decode("utf-8") if result.output else "",
            }
        except Exception as e:
            logger.error("Exec failed", container_id=container_id, error=str(e))
            raise


# Singleton instance
_container_manager: Optional["ContainerManager"] = None


def get_container_manager() -> "ContainerManager":
    """Get the container manager singleton."""
    global _container_manager
    if _container_manager is None:
        from app.services.docker_service import get_docker_service
        _container_manager = ContainerManager(get_docker_service())
    return _container_manager


# For backwards compatibility with imports
container_manager = property(get_container_manager)
