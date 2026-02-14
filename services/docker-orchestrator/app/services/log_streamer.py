"""
Real-time log streaming for containers.

Provides async log streaming with filtering and parsing.
"""

import asyncio
import json
from typing import AsyncGenerator, Optional, List
from datetime import datetime

import docker
from docker.errors import DockerException, NotFound
import structlog

from app.config import settings


logger = structlog.get_logger()


class LogStreamer:
    """
    Real-time log streaming for containers.

    Supports:
    - Async log streaming via generator
    - Log level filtering
    - Structured log parsing
    - Historical log retrieval + streaming
    """

    def __init__(self):
        self.client = docker.from_env()
        self._active_streams: dict = {}

    async def stream_logs(
        self,
        container_id: str,
        tail: int = 0,
        follow: bool = True,
        since: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream logs from container as async generator.

        Args:
            container_id: Container ID
            tail: Number of lines to include from history (0 = all/new)
            follow: Continue streaming for new logs (true) or just return existing (false)
            since: ISO timestamp to start from

        Yields:
            Log entry dict with keys:
            - timestamp: ISO datetime string
            - level: Log level (INFO, WARNING, ERROR, etc.)
            - message: Log message
            - source: Log source identifier
        """
        try:
            container = self.client.containers.get(container_id)
        except NotFound:
            logger.error("Container not found for streaming", container_id=container_id)
            raise

        # Track active stream for cleanup
        stream_key = f"{container_id}"
        self._active_streams[stream_key] = True

        try:
            # Get logs with timestamps
            log_generator = container.logs(
                stream=True,
                follow=follow,
                timestamps=True,
                tail=tail if tail > 0 else None,
                since=since,
            )

            for line in log_generator:
                # Check if stream should continue
                if not self._active_streams.get(stream_key):
                    break

                try:
                    decoded = line.decode("utf-8").strip()
                    if decoded:
                        yield self._parse_log_line(decoded)
                except Exception as e:
                    logger.warning("Failed to parse log line", error=str(e))
                    continue

        except DockerException as e:
            logger.error("Docker error during log streaming", error=str(e))
            raise
        finally:
            # Clean up stream tracking
            self._active_streams.pop(stream_key, None)

    def stop_stream(self, container_id: str) -> None:
        """Stop an active log stream for a container."""
        stream_key = f"{container_id}"
        self._active_streams.pop(stream_key, None)
        logger.info("Log stream stopped", container_id=container_id)

    async def get_historical_logs(
        self,
        container_id: str,
        tail: int = 100,
        level_filter: Optional[str] = None,
    ) -> List[dict]:
        """
        Get historical logs without streaming.

        Args:
            container_id: Container ID
            tail: Number of lines to retrieve
            level_filter: Only return logs of this level

        Returns:
            List of log entry dicts
        """
        try:
            container = self.client.containers.get(container_id)
        except NotFound:
            logger.error("Container not found", container_id=container_id)
            raise

        logs = container.logs(tail=tail, timestamps=True)
        decoded_logs = logs.decode("utf-8").strip().split("\n")

        result = []
        for line in decoded_logs:
            if not line:
                continue

            entry = self._parse_log_line(line)

            # Apply level filter
            if level_filter is None or entry["level"] == level_filter.upper():
                result.append(entry)

        return result

    def _parse_log_line(self, line: str) -> dict:
        """
        Parse a log line into structured format.

        Docker logs format: "2026-02-13T10:30:00.123456789Z message"

        Also handles JSON logs and detects log levels.
        """
        # Try JSON first
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                # Already structured
                return {
                    "timestamp": parsed.get("timestamp", parsed.get("time", "")),
                    "level": parsed.get("level", parsed.get("severity", "INFO")),
                    "message": parsed.get("message", parsed.get("msg", line)),
                    "source": parsed.get("source", parsed.get("logger", "container")),
                }
        except (json.JSONDecodeError, TypeError):
            pass

        # Standard Docker log format: timestamp message
        parts = line.split(" ", 1)

        if len(parts) >= 2:
            timestamp_str = parts[0]
            message = parts[1]

            # Clean up timestamp (remove nanoseconds)
            if "." in timestamp_str:
                timestamp_str = timestamp_str.split(".")[0] + "Z"

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                timestamp = timestamp.isoformat()
            except ValueError:
                timestamp = timestamp_str
        else:
            timestamp = datetime.utcnow().isoformat() + "Z"
            message = line

        # Detect log level from message
        level = self._detect_log_level(message)

        # Detect source
        source = self._detect_source(message)

        return {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "source": source,
        }

    def _detect_log_level(self, message: str) -> str:
        """Detect log level from message content."""
        message_upper = message.upper()

        # Check for level prefixes
        for lvl in ["CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "DEBUG", "TRACE"]:
            if f"[{lvl}]" in message_upper or f"{lvl}:" in message_upper:
                if lvl == "WARN":
                    return "WARNING"
                if lvl == "FATAL":
                    return "CRITICAL"
                return lvl

        # Check for level words at start
        words = message_upper.split()
        if words:
            first_word = words[0].rstrip(":")
            if first_word in ["CRITICAL", "ERROR", "WARNING", "WARN", "DEBUG", "INFO"]:
                return first_word if first_word != "WARN" else "WARNING"

        return "INFO"

    def _detect_source(self, message: str) -> str:
        """Detect log source from message patterns."""
        message_lower = message.lower()

        # Check for common patterns
        if "[flow]" in message_lower or "flow.py" in message_lower:
            return "flow"
        if "[agent]" in message_lower or "agent:" in message_lower:
            return "agent"
        if "[http]" in message_lower or "request:" in message_lower:
            return "http"
        if "[task]" in message_lower or "task:" in message_lower:
            return "task"

        return "container"

    async def stream_logs_with_filter(
        self,
        container_id: str,
        level_filter: Optional[str] = None,
        source_filter: Optional[str] = None,
        text_filter: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream logs with multiple filters.

        Args:
            container_id: Container ID
            level_filter: Only include this log level
            source_filter: Only include this source
            text_filter: Only include messages containing this text

        Yields:
            Filtered log entry dicts
        """
        async for entry in self.stream_logs(container_id):
            # Apply filters
            if level_filter and entry["level"] != level_filter.upper():
                continue

            if source_filter and entry["source"] != source_filter.lower():
                continue

            if text_filter and text_filter.lower() not in entry["message"].lower():
                continue

            yield entry


# Singleton instance
_log_streamer: Optional["LogStreamer"] = None


def get_log_streamer() -> "LogStreamer":
    """Get the log streamer singleton."""
    global _log_streamer
    if _log_streamer is None:
        from app.services.docker_service import get_docker_service
        _log_streamer = LogStreamer(get_docker_service())
    return _log_streamer
