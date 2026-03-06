import json
import os
from datetime import datetime
from typing import Dict

import aiofiles
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.requests import OutputEventIngestRequest


logger = structlog.get_logger()


def _to_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _to_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


class OutputPersistenceService:
    async def persist_event(
        self,
        db: AsyncSession,
        deployment_id: str,
        event: OutputEventIngestRequest,
    ) -> Dict[str, bool]:
        destinations = {"postgres": True, "files": True}
        if event.destinations is not None:
            destinations.update(event.destinations)

        result = {"postgres": False, "files": False}

        if destinations.get("postgres", False):
            result["postgres"] = await self._write_postgres(db, deployment_id, event)

        if destinations.get("files", False):
            result["files"] = await self._write_files(deployment_id, event)

        return result

    async def _write_postgres(
        self,
        db: AsyncSession,
        deployment_id: str,
        event: OutputEventIngestRequest,
    ) -> bool:
        event_timestamp = event.timestamp or datetime.utcnow()

        metadata = {
            "run_id": event.run_id,
            "event_type": event.event_type,
            "payload": event.payload,
        }

        try:
            await db.execute(
                text(
                    """
                    INSERT INTO execution_logs (
                        deployment_id,
                        level,
                        message,
                        source,
                        metadata,
                        timestamp
                    ) VALUES (
                        :deployment_id,
                        :level,
                        :message,
                        :source,
                        CAST(:metadata AS jsonb),
                        :timestamp
                    )
                    """
                ),
                {
                    "deployment_id": deployment_id,
                    "level": event.level,
                    "message": event.message,
                    "source": event.source,
                    "metadata": json.dumps(metadata),
                    "timestamp": event_timestamp,
                },
            )

            metric_payload = event.payload
            if event.event_type == "run_completed" and isinstance(metric_payload, dict):
                await db.execute(
                    text(
                        """
                        INSERT INTO execution_metrics (
                            deployment_id,
                            cpu_percent,
                            memory_usage_mb,
                            tokens_used,
                            api_calls,
                            estimated_cost,
                            execution_duration_seconds,
                            recorded_at
                        ) VALUES (
                            :deployment_id,
                            :cpu_percent,
                            :memory_usage_mb,
                            :tokens_used,
                            :api_calls,
                            :estimated_cost,
                            :execution_duration_seconds,
                            :recorded_at
                        )
                        """
                    ),
                    {
                        "deployment_id": deployment_id,
                        "cpu_percent": metric_payload.get("cpu_percent"),
                        "memory_usage_mb": metric_payload.get("memory_usage_mb"),
                        "tokens_used": _to_int(metric_payload.get("tokens_used", 0)),
                        "api_calls": _to_int(metric_payload.get("api_calls", 0)),
                        "estimated_cost": _to_float(metric_payload.get("estimated_cost", 0.0)),
                        "execution_duration_seconds": metric_payload.get(
                            "execution_duration_seconds"
                        ),
                        "recorded_at": event_timestamp,
                    },
                )

            await db.commit()
            return True
        except Exception as exc:
            await db.rollback()
            logger.warning(
                "Failed to persist output event to postgres",
                deployment_id=deployment_id,
                run_id=event.run_id,
                event_type=event.event_type,
                error=str(exc),
            )
            return False

    async def _write_files(self, deployment_id: str, event: OutputEventIngestRequest) -> bool:
        event_timestamp = event.timestamp or datetime.utcnow()
        run_root = os.path.join(
            settings.AGENT_OUTPUT_PATH,
            deployment_id,
            event.run_id,
        )

        try:
            os.makedirs(run_root, exist_ok=True)

            events_jsonl = os.path.join(run_root, "events.jsonl")
            summary_md = os.path.join(run_root, "summary.md")
            metrics_json = os.path.join(run_root, "metrics.json")

            event_record = {
                "timestamp": event_timestamp.isoformat(),
                "deployment_id": deployment_id,
                "run_id": event.run_id,
                "event_type": event.event_type,
                "level": event.level,
                "source": event.source,
                "message": event.message,
                "payload": event.payload,
            }

            async with aiofiles.open(events_jsonl, "a") as f:
                await f.write(json.dumps(event_record, default=str) + "\n")

            if event.event_type == "run_completed" and isinstance(event.payload, dict):
                async with aiofiles.open(metrics_json, "w") as f:
                    await f.write(json.dumps(event.payload, indent=2, default=str))

            summary_line = (
                f"- {event_timestamp.isoformat()} [{event.level}] "
                f"{event.event_type}: {event.message}\n"
            )
            if not os.path.exists(summary_md):
                async with aiofiles.open(summary_md, "w") as f:
                    await f.write(f"# Run Summary\n\nrun_id: `{event.run_id}`\n\n")

            async with aiofiles.open(summary_md, "a") as f:
                await f.write(summary_line)

            return True
        except Exception as exc:
            logger.warning(
                "Failed to persist output event to files",
                deployment_id=deployment_id,
                run_id=event.run_id,
                event_type=event.event_type,
                error=str(exc),
            )
            return False


_output_persistence_service: OutputPersistenceService | None = None


def get_output_persistence_service() -> OutputPersistenceService:
    global _output_persistence_service
    if _output_persistence_service is None:
        _output_persistence_service = OutputPersistenceService()
    return _output_persistence_service
