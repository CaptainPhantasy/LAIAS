"""
API dependencies for dependency injection.

Provides reusable dependencies for FastAPI routes.
"""

from collections.abc import AsyncGenerator

from app.services.docker_service import DockerService


async def get_docker_service() -> AsyncGenerator[DockerService, None]:
    """
    Dependency for getting Docker service instance.

    Yields a DockerService instance for use in endpoints.
    """
    service = DockerService()
    try:
        yield service
    finally:
        await service.close()
