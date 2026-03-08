"""Docker runtime implementation for container operations."""

import importlib
import json
import os
import shutil
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import structlog

aiofiles = importlib.import_module("aiofiles")
docker = importlib.import_module("docker")
docker_errors = importlib.import_module("docker.errors")
APIError = docker_errors.APIError
DockerException = docker_errors.DockerException
NotFound = docker_errors.NotFound

from app.config import settings
from app.services.runtime.base import ContainerRuntime

logger = structlog.get_logger()


class DockerRuntime(ContainerRuntime):
    """Container runtime backed by the Docker Python SDK."""

    def __init__(self) -> None:
        """Initialize Docker SDK clients and runtime defaults."""
        self.client = docker.from_env()
        self.aio_client = None
        self.base_image = settings.AGENT_IMAGE_BASE
        self.code_path = settings.AGENT_CODE_PATH
        self.network = settings.DOCKER_NETWORK

    @staticmethod
    def _get_label(labels: dict[str, str], key: str) -> str | None:
        return labels.get(f"laias.{key}") or labels.get(key)

    @staticmethod
    def _parse_docker_datetime(timestamp: str | None) -> datetime | None:
        if not timestamp or timestamp.startswith("0001-01-01"):
            return None

        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None

    def _deployment_config_file(self, deployment_id: str) -> str:
        config_dir = os.path.join(settings.AGENT_OUTPUT_PATH, ".deployment-config")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, f"{deployment_id}.json")

    def _write_deployment_config(
        self,
        deployment_id: str,
        output_path: str,
        output_format: str,
        output_config: dict[str, bool],
    ) -> None:
        config_file = self._deployment_config_file(deployment_id)
        payload = {
            "deployment_id": deployment_id,
            "output_path": output_path,
            "output_format": output_format,
            "output_config": output_config,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        with open(config_file, "w", encoding="utf-8") as file:
            json.dump(payload, file)

    def _remove_deployment_config(self, deployment_id: str) -> None:
        config_file = self._deployment_config_file(deployment_id)
        if os.path.exists(config_file):
            os.remove(config_file)

    async def _cleanup_container_resources(self, labels: dict[str, str]) -> None:
        deployment_id = self._get_label(labels, "deployment_id")
        if not deployment_id:
            return

        deploy_dir = os.path.join(self.code_path, deployment_id)
        output_dir = labels.get("output_path") or os.path.join(
            settings.AGENT_OUTPUT_PATH, deployment_id
        )

        await self._cleanup_deployment_dir(deploy_dir)

        safe_output_root = os.path.realpath(settings.AGENT_OUTPUT_PATH)
        safe_output_dir = os.path.realpath(output_dir)
        if safe_output_dir.startswith(safe_output_root):
            await self._cleanup_deployment_dir(safe_output_dir)

        self._remove_deployment_config(deployment_id)

    async def ping(self) -> bool:
        """Verify Docker daemon is accessible."""
        try:
            self.client.ping()
            return True
        except DockerException as exc:
            logger.error("Docker ping failed", error=str(exc))
            raise

    async def get_info(self) -> dict[str, Any]:
        """Get Docker system information."""
        try:
            return self.client.info()
        except DockerException as exc:
            logger.error("Failed to get Docker info", error=str(exc))
            raise

    async def ensure_network(self, network_name: str) -> None:
        """Ensure Docker network exists."""
        try:
            self.client.networks.get(network_name)
        except NotFound:
            logger.info("Creating Docker network", network=network_name)
            self.client.networks.create(network_name, driver="bridge", labels={"laias": "true"})

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
        """Deploy an agent container using volume mounts."""
        requirements = requirements or []
        environment_vars = environment_vars or {}
        output_config = output_config or {"postgres": True, "files": True}

        deploy_dir = os.path.join(self.code_path, deployment_id)
        output_dir = os.path.realpath(
            output_path or os.path.join(settings.AGENT_OUTPUT_PATH, deployment_id)
        )
        await self._write_agent_code(deploy_dir, flow_code, agents_yaml, requirements)
        os.makedirs(output_dir, exist_ok=True)
        self._write_deployment_config(deployment_id, output_dir, output_format, output_config)

        host_deploy_dir = deploy_dir.replace(
            settings.AGENT_CODE_PATH, settings.HOST_AGENT_CODE_PATH, 1
        )
        if output_dir.startswith(settings.AGENT_OUTPUT_PATH):
            host_output_dir = output_dir.replace(
                settings.AGENT_OUTPUT_PATH, settings.HOST_AGENT_OUTPUT_PATH, 1
            )
        else:
            host_output_dir = output_dir

        container_name = f"{settings.CONTAINER_PREFIX}{deployment_id[:12]}"
        ingest_url = (
            f"{settings.INTERNAL_ORCHESTRATOR_URL}/api/deployments/{deployment_id}/outputs/events"
        )
        env_vars = {
            "DEPLOYMENT_ID": deployment_id,
            "AGENT_ID": agent_id,
            "AGENT_NAME": agent_name,
            "LAIAS_DEPLOYMENT_ID": deployment_id,
            "LAIAS_OUTPUT_CONFIG": json.dumps(output_config),
            "LAIAS_OUTPUT_ROOT": "/app/outputs",
            "LAIAS_OUTPUT_FORMAT": output_format,
            "LAIAS_OUTPUT_PATH": output_dir,
            "LAIAS_OUTPUT_INGEST_URL": ingest_url,
            **environment_vars,
        }

        volume_mounts = {
            host_deploy_dir: {"bind": "/app/agent", "mode": "ro"},
            host_output_dir: {"bind": "/app/outputs", "mode": "rw"},
        }
        for vol in input_volumes or []:
            volume_mounts[vol["host_path"]] = {
                "bind": vol["container_path"],
                "mode": "ro",
            }

        try:
            container = self.client.containers.create(
                image=self.base_image,
                name=container_name,
                volumes=volume_mounts,
                environment=env_vars,
                cpu_period=100000,
                cpu_quota=int(cpu_limit * 100000),
                mem_limit=memory_limit,
                network=self.network,
                detach=True,
                auto_remove=False,
                restart_policy={
                    "Name": "on-failure",
                    "MaximumRetryCount": settings.CONTAINER_MAX_RESTART_COUNT,
                },
                labels={
                    "deployment_id": deployment_id,
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "laias.deployment_id": deployment_id,
                    "laias.agent_id": agent_id,
                    "laias.agent_name": agent_name,
                    "output_postgres": str(output_config.get("postgres", False)).lower(),
                    "output_files": str(output_config.get("files", False)).lower(),
                    "output_format": output_format,
                    "output_path": output_dir,
                    "laias": "agent",
                },
            )

            logger.info(
                "Container created",
                deployment_id=deployment_id,
                container_id=container.id,
                container_name=container_name,
                image=self.base_image,
            )

            return container
        except APIError as exc:
            logger.error("Container creation failed", error=str(exc))
            await self._cleanup_deployment_dir(deploy_dir)
            raise

    async def _write_agent_code(
        self,
        deploy_dir: str,
        flow_code: str,
        agents_yaml: str,
        requirements: list[str],
    ) -> None:
        """Write generated code to deployment directory."""
        os.makedirs(deploy_dir, exist_ok=True)

        flow_path = os.path.join(deploy_dir, "flow.py")
        async with aiofiles.open(flow_path, "w") as file:
            await file.write(flow_code)

        yaml_path = os.path.join(deploy_dir, "agents.yaml")
        async with aiofiles.open(yaml_path, "w") as file:
            await file.write(agents_yaml)

        if requirements:
            req_path = os.path.join(deploy_dir, "requirements.txt")
            async with aiofiles.open(req_path, "w") as file:
                await file.write("\n".join(requirements))

        logger.info("Agent code written", deploy_dir=deploy_dir)

    async def _cleanup_deployment_dir(self, deploy_dir: str) -> None:
        """Remove deployment directory."""
        try:
            if os.path.exists(deploy_dir):
                shutil.rmtree(deploy_dir)
                logger.info("Deployment directory cleaned", deploy_dir=deploy_dir)
        except Exception as exc:
            logger.warning("Failed to clean deployment directory", error=str(exc))

    async def start_container(self, container_id: str) -> None:
        """Start a stopped container."""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info("Container started", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as exc:
            logger.error("Failed to start container", container_id=container_id, error=str(exc))
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
        except APIError as exc:
            logger.error("Failed to stop container", container_id=container_id, error=str(exc))
            raise

    async def restart_container(self, container_id: str, timeout: int = 10) -> None:
        """Restart a container."""
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            logger.info("Container restarted", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as exc:
            logger.error("Failed to restart container", container_id=container_id, error=str(exc))
            raise

    async def pause_container(self, container_id: str) -> None:
        """Pause a running container."""
        try:
            container = self.client.containers.get(container_id)
            container.pause()
            logger.info("Container paused", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as exc:
            logger.error("Failed to pause container", container_id=container_id, error=str(exc))
            raise

    async def resume_container(self, container_id: str) -> None:
        """Resume a paused container."""
        try:
            container = self.client.containers.get(container_id)
            container.unpause()
            logger.info("Container resumed", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as exc:
            logger.error("Failed to resume container", container_id=container_id, error=str(exc))
            raise

    async def cancel_container(self, container_id: str, timeout: int = 10) -> None:
        """Cancel execution by stopping and removing a container."""
        try:
            container = self.client.containers.get(container_id)
            labels = dict(container.labels)

            try:
                container.stop(timeout=timeout)
            except APIError as exc:
                logger.warning(
                    "Container stop during cancel failed, forcing removal",
                    container_id=container_id,
                    error=str(exc),
                )

            container.remove(force=True)
            await self._cleanup_container_resources(labels)

            logger.info("Container cancelled", container_id=container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as exc:
            logger.error("Failed to cancel container", container_id=container_id, error=str(exc))
            raise

    async def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container and its deployment resources."""
        try:
            container = self.client.containers.get(container_id)
            labels = dict(container.labels)

            container.remove(force=force)
            await self._cleanup_container_resources(labels)

            logger.info("Container removed", container_id=container_id)

        except NotFound:
            logger.warning("Container not found for removal", container_id=container_id)
        except APIError as exc:
            logger.error("Failed to remove container", container_id=container_id, error=str(exc))
            raise

    async def get_container(
        self,
        container_id: str,
    ) -> Any | None:
        """Get a container by ID."""
        try:
            return self.client.containers.get(container_id)
        except NotFound:
            return None
        except APIError as exc:
            logger.error("Failed to get container", container_id=container_id, error=str(exc))
            raise

    async def list_containers(self, all: bool = True) -> list[dict[str, Any]]:
        """List all LAIAS agent containers."""
        try:
            containers = self.client.containers.list(all=all, filters={"label": "laias=agent"})

            return [
                {
                    "container_id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "created": container.attrs["Created"],
                    "deployment_id": self._get_label(container.labels, "deployment_id") or "",
                    "agent_id": self._get_label(container.labels, "agent_id") or "",
                    "agent_name": self._get_label(container.labels, "agent_name") or container.name,
                }
                for container in containers
            ]

        except APIError as exc:
            logger.error("Failed to list containers", error=str(exc))
            raise

    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: str | None = None,
    ) -> list[str]:
        """Get container logs."""
        try:
            container = self.client.containers.get(container_id)

            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None
            logs = container.logs(
                tail=tail if tail > 0 else "all",
                since=since_dt,
                timestamps=True,
            )

            return logs.decode("utf-8").split("\n")

        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise
        except APIError as exc:
            logger.error("Failed to get logs", container_id=container_id, error=str(exc))
            raise

    async def get_container_stats(self, container_id: str) -> dict[str, Any]:
        """Get container resource statistics."""
        try:
            container = self.client.containers.get(container_id)
            stats = cast(dict[str, Any], container.stats(stream=False))  # type: ignore[arg-type]

            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0.0

            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 0)

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
        except APIError as exc:
            logger.error("Failed to get stats", container_id=container_id, error=str(exc))
            raise

    async def cleanup_deployment(self, deployment_id: str) -> None:
        """Clean up a failed deployment."""
        deploy_dir = os.path.join(self.code_path, deployment_id)
        output_dir = os.path.join(settings.AGENT_OUTPUT_PATH, deployment_id)
        await self._cleanup_deployment_dir(deploy_dir)
        await self._cleanup_deployment_dir(output_dir)

    async def garbage_collect_containers(self) -> dict[str, Any]:
        """Remove old stopped/error containers and their deployment artifacts."""
        now = datetime.now(UTC)
        cutoff = now - timedelta(hours=settings.GC_MAX_AGE_HOURS)

        inspected_count = 0
        removed_count = 0
        skipped_count = 0
        failed_count = 0

        containers = self.client.containers.list(all=True, filters={"label": "laias=agent"})

        for container in containers:
            inspected_count += 1

            try:
                labels = dict(container.labels)
                if not any(label.startswith("laias.") for label in labels):
                    skipped_count += 1
                    continue

                state = container.attrs.get("State", {})
                status = state.get("Status", "").lower()
                error_message = state.get("Error", "")

                is_stopped_or_errored = status in {"exited", "dead"} or bool(error_message)
                if not is_stopped_or_errored:
                    skipped_count += 1
                    continue

                finished_at = self._parse_docker_datetime(state.get("FinishedAt"))
                if finished_at is None:
                    finished_at = self._parse_docker_datetime(container.attrs.get("Created"))

                if finished_at is None or finished_at > cutoff:
                    skipped_count += 1
                    continue

                container_id = container.id
                if not container_id:
                    skipped_count += 1
                    continue

                await self.remove_container(container_id, force=True)
                removed_count += 1
                logger.info(
                    "Garbage collected container",
                    container_id=container_id,
                    deployment_id=self._get_label(labels, "deployment_id"),
                    status=status,
                    finished_at=finished_at.isoformat(),
                )
            except Exception as exc:
                failed_count += 1
                logger.warning(
                    "Failed to garbage collect container",
                    container_id=container.id,
                    error=str(exc),
                )

        summary = {
            "inspected": inspected_count,
            "removed": removed_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "cutoff": cutoff.isoformat(),
        }
        logger.info("Container garbage collection completed", **summary)
        return summary

    async def close(self) -> None:
        """Close Docker SDK client connections."""
        try:
            self.client.close()
        except Exception as exc:
            logger.warning("Error closing Docker client", error=str(exc))
