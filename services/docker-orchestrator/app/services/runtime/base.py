"""Container runtime abstraction for orchestrator services."""

from abc import ABC, abstractmethod
from typing import Any


class ContainerRuntime(ABC):
    """Abstract interface for container runtime implementations."""

    @abstractmethod
    async def ping(self) -> bool:
        """Verify runtime daemon/control plane accessibility."""

    @abstractmethod
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
        input_volumes: list[dict[str, str]] | None = None,
        cpu_limit: float = 1.0,
        memory_limit: str = "512m",
    ) -> Any:
        """Create a runtime workload for an agent deployment."""

    @abstractmethod
    async def start_container(self, container_id: str) -> None:
        """Start a stopped runtime workload."""

    @abstractmethod
    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running runtime workload."""

    @abstractmethod
    async def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a runtime workload and associated local resources."""

    @abstractmethod
    async def get_container(self, container_id: str) -> Any | None:
        """Get a runtime workload object by ID."""

    @abstractmethod
    async def list_containers(self, all: bool = True) -> list[dict[str, Any]]:
        """List runtime workloads managed by LAIAS."""

    @abstractmethod
    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: str | None = None,
    ) -> list[str]:
        """Return runtime workload logs."""

    @abstractmethod
    async def get_container_stats(self, container_id: str) -> dict[str, Any]:
        """Return runtime workload resource statistics."""
