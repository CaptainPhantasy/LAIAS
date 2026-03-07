"""Container service facade with runtime abstraction."""

import asyncio
from typing import Any, cast

import structlog

from app.services.runtime import get_runtime

logger = structlog.get_logger()


class DockerService:
    """Backwards-compatible service delegating to a runtime implementation."""

    def __init__(self) -> None:
        """Initialize service using configured container runtime."""
        self.runtime = get_runtime()

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to underlying runtime."""
        return getattr(self.runtime, name)

    @property
    def client(self) -> Any:
        """Expose underlying client for compatibility with existing callers."""
        return getattr(self.runtime, "client", None)

    async def ping(self) -> bool:
        """Verify runtime control plane accessibility."""
        return await self.runtime.ping()

    async def deploy_agent(
        self,
        deployment_id: str,
        agent_id: str,
        agent_name: str,
        flow_code: str,
        agents_yaml: str,
        requirements: list[str] | None = None,
        environment_vars: dict[str, str] | None = None,
        output_config: dict[str, bool] | None = None,
        output_path: str | None = None,
        output_format: str = "markdown",
        cpu_limit: float = 1.0,
        memory_limit: str = "512m",
    ) -> Any:
        """Deploy an agent workload via configured runtime."""
        return await self.runtime.deploy_agent(
            deployment_id=deployment_id,
            agent_id=agent_id,
            agent_name=agent_name,
            flow_code=flow_code,
            agents_yaml=agents_yaml,
            requirements=requirements,
            environment_vars=environment_vars,
            output_config=output_config,
            output_path=output_path,
            output_format=output_format,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
        )

    async def start_container(self, container_id: str) -> None:
        """Start a stopped container."""
        await self.runtime.start_container(container_id)

    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container."""
        await self.runtime.stop_container(container_id, timeout=timeout)

    async def restart_container(self, container_id: str, timeout: int = 10) -> None:
        """Restart a container."""
        restart = getattr(self.runtime, "restart_container", None)
        if callable(restart):
            await cast(Any, restart)(container_id, timeout=timeout)
            return
        await self.stop_container(container_id, timeout=timeout)
        await asyncio.sleep(1)
        await self.start_container(container_id)
        logger.info("Container restarted", container_id=container_id)

    async def pause_container(self, container_id: str) -> None:
        """Pause a running container."""
        pause = getattr(self.runtime, "pause_container", None)
        if callable(pause):
            await cast(Any, pause)(container_id)
            return
        raise NotImplementedError("pause_container is not supported by current runtime")

    async def resume_container(self, container_id: str) -> None:
        """Resume a paused container."""
        resume = getattr(self.runtime, "resume_container", None)
        if callable(resume):
            await cast(Any, resume)(container_id)
            return
        raise NotImplementedError("resume_container is not supported by current runtime")

    async def cancel_container(self, container_id: str, timeout: int = 10) -> None:
        """Cancel execution by stopping and removing a container."""
        cancel = getattr(self.runtime, "cancel_container", None)
        if callable(cancel):
            await cast(Any, cancel)(container_id, timeout=timeout)
            return
        await self.remove_container(container_id, force=True)

    async def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container from runtime backend."""
        await self.runtime.remove_container(container_id, force=force)

    async def get_container(self, container_id: str) -> Any | None:
        """Get a container by ID."""
        return await self.runtime.get_container(container_id)

    async def list_containers(self, all: bool = True) -> list[dict[str, Any]]:
        """List managed containers."""
        return await self.runtime.list_containers(all=all)

    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: str | None = None,
    ) -> list[str]:
        """Fetch container logs from runtime backend."""
        return await self.runtime.get_container_logs(
            container_id=container_id, tail=tail, since=since
        )

    async def get_container_stats(self, container_id: str) -> dict[str, Any]:
        """Fetch container stats from runtime backend."""
        return await self.runtime.get_container_stats(container_id)

    async def get_info(self) -> dict[str, Any]:
        """Get runtime information when backend provides it."""
        runtime = cast(Any, self.runtime)
        if hasattr(runtime, "get_info"):
            return await runtime.get_info()
        return {}

    async def ensure_network(self, network_name: str) -> None:
        """Ensure runtime network exists when supported."""
        runtime = cast(Any, self.runtime)
        if hasattr(runtime, "ensure_network"):
            await runtime.ensure_network(network_name)

    async def cleanup_deployment(self, deployment_id: str) -> None:
        """Clean up deployment artifacts when supported by runtime."""
        runtime = cast(Any, self.runtime)
        if hasattr(runtime, "cleanup_deployment"):
            await runtime.cleanup_deployment(deployment_id)

    async def garbage_collect_containers(self) -> dict[str, Any]:
        """Run runtime garbage collection when backend supports it."""
        runtime = cast(Any, self.runtime)
        if hasattr(runtime, "garbage_collect_containers"):
            return await runtime.garbage_collect_containers()
        return {"inspected": 0, "removed": 0, "skipped": 0, "failed": 0}

    async def close(self) -> None:
        """Close runtime resources when backend provides close."""
        runtime = cast(Any, self.runtime)
        if hasattr(runtime, "close"):
            await runtime.close()


# Singleton instance
_docker_service: DockerService | None = None


def get_docker_service() -> "DockerService":
    """Get the Docker service singleton."""
    global _docker_service
    if _docker_service is None:
        _docker_service = DockerService()
    return _docker_service


# For backwards compatibility with imports
docker_service = get_docker_service
