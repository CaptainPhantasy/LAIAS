"""
Resource monitoring for containers.

Provides real-time CPU, memory, and network metrics.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import docker
from docker.errors import NotFound
import structlog

from app.services.docker_service import DockerService
from app.models.responses import MetricsResponse


logger = structlog.get_logger()


class ResourceMonitor:
    """
    Real-time resource monitoring for containers.

    Provides:
    - CPU usage percentage
    - Memory usage and limits
    - Network I/O statistics
    - Container uptime
    """

    def __init__(self):
        self.docker_service = DockerService()
        self._cache: Dict[str, tuple] = {}  # (stats, timestamp)
        self._cache_ttl = 5  # seconds

    async def get_metrics(self, container_id: str) -> MetricsResponse:
        """
        Get current resource metrics for a container.

        Returns:
            MetricsResponse with all metrics
        """
        # Check cache first
        cached = self._get_from_cache(container_id)
        if cached:
            return cached

        # Fetch fresh stats
        container = await self.docker_service.get_container(container_id)
        if not container:
            raise NotFound(f"Container {container_id} not found")

        container.reload()

        # Get stats
        stats = await self.docker_service.get_container_stats(container_id)

        # Calculate uptime
        created = datetime.fromisoformat(container.attrs["Created"].replace("Z", "+00:00"))
        uptime_seconds = int((datetime.utcnow() - created).total_seconds())

        # Build response
        metrics = MetricsResponse(
            container_id=container_id,
            cpu_percent=stats["cpu_percent"],
            memory_usage_mb=stats["memory_usage_mb"],
            memory_limit_mb=stats["memory_limit_mb"],
            network_rx_bytes=stats["network_rx_bytes"],
            network_tx_bytes=stats["network_tx_bytes"],
            uptime_seconds=uptime_seconds,
            timestamp=datetime.utcnow(),
        )

        # Cache the result
        self._add_to_cache(container_id, metrics)

        return metrics

    async def get_metrics_batch(
        self, container_ids: List[str]
    ) -> Dict[str, MetricsResponse]:
        """
        Get metrics for multiple containers concurrently.

        Args:
            container_ids: List of container IDs

        Returns:
            Dict mapping container_id to MetricsResponse
        """
        tasks = [
            self._get_metrics_safe(cid)
            for cid in container_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics_map = {}
        for cid, result in zip(container_ids, results):
            if isinstance(result, Exception):
                logger.warning(
                    "Failed to get metrics",
                    container_id=cid,
                    error=str(result),
                )
                continue
            if result:
                metrics_map[cid] = result

        return metrics_map

    async def _get_metrics_safe(
        self, container_id: str
    ) -> Optional[MetricsResponse]:
        """Get metrics safely, returning None on error."""
        try:
            return await self.get_metrics(container_id)
        except Exception:
            return None

    async def get_metrics_history(
        self,
        container_id: str,
        duration_seconds: int = 300,
        interval_seconds: int = 5,
    ) -> List[MetricsResponse]:
        """
        Get historical metrics for a container.

        Note: Docker doesn't store historical stats, so this
        samples current state. For true history, use Prometheus/cAdvisor.

        Args:
            container_id: Container ID
            duration_seconds: How long to sample
            interval_seconds: Sample interval

        Returns:
            List of MetricsResponse snapshots
        """
        snapshots = []
        iterations = duration_seconds // interval_seconds

        for _ in range(iterations):
            try:
                snapshot = await self.get_metrics(container_id)
                snapshots.append(snapshot)
            except Exception as e:
                logger.warning("Failed to sample metrics", error=str(e))

            await asyncio.sleep(interval_seconds)

        return snapshots

    async def get_resource_summary(
        self, container_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate resource summary for all or specified containers.

        Returns:
            Dict with totals and averages
        """
        if container_ids is None:
            containers = await self.docker_service.list_containers(all=True)
            container_ids = [c["container_id"] for c in containers]

        metrics = await self.get_metrics_batch(container_ids)

        if not metrics:
            return {
                "container_count": 0,
                "total_cpu_percent": 0.0,
                "avg_cpu_percent": 0.0,
                "total_memory_mb": 0.0,
                "total_network_rx": 0,
                "total_network_tx": 0,
            }

        total_cpu = sum(m.cpu_percent for m in metrics.values())
        total_memory = sum(m.memory_usage_mb for m in metrics.values())
        total_rx = sum(m.network_rx_bytes for m in metrics.values())
        total_tx = sum(m.network_tx_bytes for m in metrics.values())

        return {
            "container_count": len(metrics),
            "total_cpu_percent": round(total_cpu, 2),
            "avg_cpu_percent": round(total_cpu / len(metrics), 2),
            "total_memory_mb": round(total_memory, 2),
            "total_network_rx": total_rx,
            "total_network_tx": total_tx,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    async def detect_high_usage(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 90.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect containers with high resource usage.

        Args:
            cpu_threshold: CPU percentage threshold
            memory_threshold: Memory percentage threshold

        Returns:
            List of containers exceeding thresholds
        """
        containers = await self.docker_service.list_containers(all=True)
        running_ids = [
            c["container_id"]
            for c in containers
            if c["status"] == "running"
        ]

        metrics = await self.get_metrics_batch(running_ids)
        alerts = []

        for cid, m in metrics.items():
            container = await self.docker_service.get_container(cid)
            if not container:
                continue

            # Calculate memory percentage
            memory_percent = (m.memory_usage_mb / m.memory_limit_mb) * 100

            issues = []
            if m.cpu_percent > cpu_threshold:
                issues.append(f"CPU {m.cpu_percent:.1f}% > {cpu_threshold}%")
            if memory_percent > memory_threshold:
                issues.append(f"Memory {memory_percent:.1f}% > {memory_threshold}%")

            if issues:
                alerts.append({
                    "container_id": cid,
                    "container_name": container.name,
                    "deployment_id": container.labels.get("deployment_id", ""),
                    "issues": issues,
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": round(memory_percent, 1),
                })

        return alerts

    def _get_from_cache(self, container_id: str) -> Optional[MetricsResponse]:
        """Get metrics from cache if not expired."""
        if container_id in self._cache:
            metrics, timestamp = self._cache[container_id]
            age = (datetime.utcnow() - timestamp).total_seconds()
            if age < self._cache_ttl:
                return metrics
        return None

    def _add_to_cache(self, container_id: str, metrics: MetricsResponse) -> None:
        """Add metrics to cache."""
        self._cache[container_id] = (metrics, datetime.utcnow())

    def clear_cache(self, container_id: Optional[str] = None) -> None:
        """Clear cache for a container or all containers."""
        if container_id:
            self._cache.pop(container_id, None)
        else:
            self._cache.clear()

    async def get_rate_metrics(
        self,
        container_id: str,
        interval_seconds: int = 1,
    ) -> Dict[str, float]:
        """
        Calculate rate-based metrics (bytes/sec, etc.).

        Args:
            container_id: Container ID
            interval_seconds: Seconds between samples

        Returns:
            Dict with rates
        """
        # Get first sample
        metrics1 = await self.get_metrics(container_id)
        await asyncio.sleep(interval_seconds)

        # Get second sample (force cache refresh)
        self.clear_cache(container_id)
        metrics2 = await self.get_metrics(container_id)

        # Calculate rates
        rx_rate = (metrics2.network_rx_bytes - metrics1.network_rx_bytes) / interval_seconds
        tx_rate = (metrics2.network_tx_bytes - metrics1.network_tx_bytes) / interval_seconds

        return {
            "network_rx_bytes_per_sec": max(0, rx_rate),
            "network_tx_bytes_per_sec": max(0, tx_rate),
            "interval_seconds": interval_seconds,
        }
