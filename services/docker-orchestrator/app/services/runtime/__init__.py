"""Runtime selection for container backends."""

from app.config import settings
from app.services.runtime.base import ContainerRuntime
from app.services.runtime.docker_runtime import DockerRuntime

_runtime: ContainerRuntime | None = None


def get_runtime() -> ContainerRuntime:
    """Return the configured container runtime singleton."""
    global _runtime
    if _runtime is None:
        if settings.CONTAINER_RUNTIME == "docker":
            _runtime = DockerRuntime()
        else:
            raise ValueError(f"Unsupported container runtime: {settings.CONTAINER_RUNTIME}")
    return _runtime


__all__ = ["ContainerRuntime", "DockerRuntime", "get_runtime"]
