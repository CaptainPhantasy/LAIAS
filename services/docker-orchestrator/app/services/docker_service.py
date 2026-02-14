"""
Docker SDK wrapper for container management.

Implements the No-Build deployment strategy:
- Uses pre-built laias/agent-runner:latest image
- Mounts generated code as volumes
- Spawns containers as siblings via host socket
"""

import os
import shutil
import aiofiles
from typing import Dict, Any, Optional, List
from datetime import datetime

import docker
from docker.errors import DockerException, NotFound, APIError
import structlog

from app.config import settings


logger = structlog.get_logger()


class DockerService:
    """
    Docker SDK wrapper implementing the No-Build deployment strategy.

    Key architecture:
    - Uses pre-built laias/agent-runner:latest image
    - Mounts generated code as volumes at /app/agent:ro
    - Spawns containers as siblings via host socket
    """

    def __init__(self):
        """Initialize Docker client from environment."""
        self.client = docker.from_env()
        self.aio_client = None  # Async client for WebSocket streaming
        self.base_image = settings.AGENT_IMAGE_BASE
        self.code_path = settings.AGENT_CODE_PATH
        self.network = settings.DOCKER_NETWORK

    async def ping(self) -> bool:
        """Verify Docker daemon is accessible."""
        try:
            self.client.ping()
            return True
        except DockerException as e:
            logger.error("Docker ping failed", error=str(e))
            raise

    async def get_info(self) -> Dict[str, Any]:
        """Get Docker system information."""
        try:
            return self.client.info()
        except DockerException as e:
            logger.error("Failed to get Docker info", error=str(e))
            raise

    async def ensure_network(self, network_name: str) -> None:
        """Ensure Docker network exists."""
        try:
            self.client.networks.get(network_name)
        except NotFound:
            logger.info("Creating Docker network", network=network_name)
            self.client.networks.create(
                network_name,
                driver="bridge",
                labels={"laias": "true"}
            )

    async def deploy_agent(
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
    ) -> Any:
        """
        Deploy agent using volume mounting strategy.

        Steps:
        1. Write generated code to host filesystem
        2. Create container with code mounted as volume
        3. Return container object (caller must start)

        Args:
            deployment_id: Unique deployment identifier
            agent_id: Agent ID from generator
            agent_name: Human-readable name
            flow_code: Generated Python flow code
            agents_yaml: Agent configuration YAML
            requirements: List of pip requirements
            environment_vars: Environment variables for container
            cpu_limit: CPU limit (0.1 - 4.0)
            memory_limit: Memory limit (e.g., "512m", "1g")

        Returns:
            Docker Container object
        """
        requirements = requirements or []
        environment_vars = environment_vars or {}

        # Step 1: Write code to deployment directory
        deploy_dir = os.path.join(self.code_path, deployment_id)
        await self._write_agent_code(
            deploy_dir, flow_code, agents_yaml, requirements
        )

        # Step 2: Create container with volume mount
        container_name = f"{settings.CONTAINER_PREFIX}{deployment_id[:12]}"

        # Build environment variables
        env_vars = {
            "DEPLOYMENT_ID": deployment_id,
            "AGENT_ID": agent_id,
            "AGENT_NAME": agent_name,
            **environment_vars
        }

        # Create container
        try:
            container = self.client.containers.create(
                image=self.base_image,
                name=container_name,
                volumes={
                    deploy_dir: {
                        "bind": "/app/agent",
                        "mode": "ro"  # Read-only mount
                    }
                },
                environment=env_vars,
                cpu_period=100000,
                cpu_quota=int(cpu_limit * 100000),
                mem_limit=memory_limit,
                network=self.network,
                detach=True,
                auto_remove=False,
                labels={
                    "deployment_id": deployment_id,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "laias": "agent",
                }
            )

            logger.info(
                "Container created",
                deployment_id=deployment_id,
                container_id=container.id,
                container_name=container_name,
                image=self.base_image,
            )

            return container

        except APIError as e:
            logger.error("Container creation failed", error=str(e))
            # Clean up deployment directory
            await self._cleanup_deployment_dir(deploy_dir)
            raise

    async def _write_agent_code(
        self,
        deploy_dir: str,
        flow_code: str,
        agents_yaml: str,
        requirements: List[str],
    ) -> None:
        """Write generated code to deployment directory."""
        os.makedirs(deploy_dir, exist_ok=True)

        # Write flow.py
        flow_path = os.path.join(deploy_dir, "flow.py")
        async with aiofiles.open(flow_path, "w") as f:
            await f.write(flow_code)

        # Write agents.yaml
        yaml_path = os.path.join(deploy_dir, "agents.yaml")
        async with aiofiles.open(yaml_path, "w") as f:
            await f.write(agents_yaml)

        # Write requirements.txt if provided
        if requirements:
            req_path = os.path.join(deploy_dir, "requirements.txt")
            async with aiofiles.open(req_path, "w") as f:
                await f.write("\n".join(requirements))

        logger.info("Agent code written", deploy_dir=deploy_dir)

    async def _cleanup_deployment_dir(self, deploy_dir: str) -> None:
        """Remove deployment directory."""
        try:
            if os.path.exists(deploy_dir):
                shutil.rmtree(deploy_dir)
                logger.info("Deployment directory cleaned", deploy_dir=deploy_dir)
        except Exception as e:
            logger.warning("Failed to clean deployment directory", error=str(e))

    async def start_container(self, container_id: str) -> None:
        """Start a stopped container."""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info("Container started", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as e:
            logger.error("Failed to start container", container_id=container_id, error=str(e))
            raise

    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container."""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info("Container stopped", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as e:
            logger.error("Failed to stop container", container_id=container_id, error=str(e))
            raise

    async def remove_container(
        self, container_id: str, force: bool = False
    ) -> None:
        """Remove a container and its code directory."""
        try:
            container = self.client.containers.get(container_id)

            # Get deployment ID from labels
            deployment_id = container.labels.get("deployment_id")

            # Remove container
            container.remove(force=force)

            # Clean up code directory
            if deployment_id:
                deploy_dir = os.path.join(self.code_path, deployment_id)
                await self._cleanup_deployment_dir(deploy_dir)

            logger.info("Container removed", container_id=container_id)

        except NotFound:
            logger.warning("Container not found for removal", container_id=container_id)
        except APIError as e:
            logger.error("Failed to remove container", container_id=container_id, error=str(e))
            raise

    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: Optional[str] = None,
    ) -> List[str]:
        """Get container logs."""
        try:
            container = self.client.containers.get(container_id)

            logs = container.logs(
                tail=tail if tail > 0 else None,
                since=since,
                timestamps=True,
            )

            return logs.decode("utf-8").split("\n")

        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as e:
            logger.error("Failed to get logs", container_id=container_id, error=str(e))
            raise

    async def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource statistics."""
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0.0

            # Memory usage
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 0)

            # Network stats
            network_stats = stats.get("networks", {})
            network_rx = 0
            network_tx = 0
            for iface in network_stats.values():
                network_rx += iface.get("rx_bytes", 0)
                network_tx += iface.get("tx_bytes", 0)

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                "network_rx_bytes": network_rx,
                "network_tx_bytes": network_tx,
            }

        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as e:
            logger.error("Failed to get stats", container_id=container_id, error=str(e))
            raise

    async def list_containers(self, all: bool = True) -> List[Dict[str, Any]]:
        """List all LAIAS agent containers."""
        try:
            containers = self.client.containers.list(
                all=all,
                filters={"label": "laias=agent"}
            )

            return [
                {
                    "container_id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "created": c.attrs["Created"],
                    "deployment_id": c.labels.get("deployment_id", ""),
                    "agent_id": c.labels.get("agent_id", ""),
                    "agent_name": c.labels.get("agent_name", c.name),
                }
                for c in containers
            ]

        except APIError as e:
            logger.error("Failed to list containers", error=str(e))
            raise

    async def get_container(self, container_id: str) -> Optional[Any]:
        """Get a container by ID."""
        try:
            return self.client.containers.get(container_id)
        except NotFound:
            return None
        except APIError as e:
            logger.error("Failed to get container", container_id=container_id, error=str(e))
            raise

    async def cleanup_deployment(self, deployment_id: str) -> None:
        """Clean up a failed deployment."""
        deploy_dir = os.path.join(self.code_path, deployment_id)
        await self._cleanup_deployment_dir(deploy_dir)

    async def close(self) -> None:
        """Close Docker client connection."""
        try:
            self.client.close()
        except Exception as e:
            logger.warning("Error closing Docker client", error=str(e))


# Singleton instance
_docker_service: Optional["DockerService"] = None


def get_docker_service() -> "DockerService":
    """Get the Docker service singleton."""
    global _docker_service
    if _docker_service is None:
        _docker_service = DockerService()
    return _docker_service


# For backwards compatibility with imports
docker_service = property(get_docker_service)
