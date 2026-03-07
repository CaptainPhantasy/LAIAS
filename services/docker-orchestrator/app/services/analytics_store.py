import asyncio
from collections import deque
from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from threading import Thread
from typing import Any, TypeVar

from sqlalchemy import delete, func, select

from app.database import async_session_factory
from app.models.database import AnalyticsEvent

T = TypeVar("T")


class AnalyticsStore:
    def __init__(self, max_events: int = 10000):
        self._max_events = max_events
        self._events: deque[dict[str, Any]] = deque(maxlen=max_events)
        self._lock = asyncio.Lock()

    @staticmethod
    def _to_event_dict(event: AnalyticsEvent) -> dict[str, Any]:
        created_at = event.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        return {
            "event_type": event.event_type,
            "event_data": event.event_data or {},
            "created_at": created_at,
        }

    async def add_event(self, event_type: str, event_data: dict[str, Any]) -> dict[str, Any]:
        record = AnalyticsEvent(
            event_type=event_type,
            event_data=event_data,
            created_at=datetime.now(UTC),
        )

        async with async_session_factory() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)

        return self._to_event_dict(record)

    async def get_events_since(self, since: datetime) -> list[dict[str, Any]]:
        statement = (
            select(AnalyticsEvent)
            .where(AnalyticsEvent.created_at >= since)
            .order_by(AnalyticsEvent.created_at.asc(), AnalyticsEvent.id.asc())
        )

        async with async_session_factory() as session:
            result = await session.execute(statement)
            events = result.scalars().all()

        return [self._to_event_dict(event) for event in events]

    async def get_events_by_type(
        self, event_type: str, since: datetime | None = None
    ) -> list[dict[str, Any]]:
        statement = select(AnalyticsEvent).where(AnalyticsEvent.event_type == event_type)
        if since is not None:
            statement = statement.where(AnalyticsEvent.created_at >= since)

        statement = statement.order_by(AnalyticsEvent.created_at.asc(), AnalyticsEvent.id.asc())

        async with async_session_factory() as session:
            result = await session.execute(statement)
            events = result.scalars().all()

        return [self._to_event_dict(event) for event in events]

    async def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        statement = (
            select(AnalyticsEvent)
            .order_by(AnalyticsEvent.created_at.desc(), AnalyticsEvent.id.desc())
            .limit(limit)
        )

        async with async_session_factory() as session:
            result = await session.execute(statement)
            events = result.scalars().all()

        event_dicts = [self._to_event_dict(event) for event in events]
        event_dicts.reverse()
        return event_dicts

    async def clear_old_events(self, older_than_days: int = 90) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)

        statement = delete(AnalyticsEvent).where(AnalyticsEvent.created_at < cutoff)

        async with async_session_factory() as session:
            result = await session.execute(statement)
            await session.commit()

        return int(result.rowcount or 0)

    async def _count_events(self) -> int:
        statement = select(func.count()).select_from(AnalyticsEvent)

        async with async_session_factory() as session:
            result = await session.execute(statement)
            total_events = result.scalar_one()

        return int(total_events)

    def _run_sync(self, coroutine: Coroutine[Any, Any, T]) -> T:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)

        output: dict[str, Any] = {}
        failure: dict[str, Exception] = {}

        def runner() -> None:
            try:
                output["value"] = asyncio.run(coroutine)
            except Exception as exc:
                failure["error"] = exc

        thread = Thread(target=runner, daemon=True)
        thread.start()
        thread.join()

        if "error" in failure:
            raise failure["error"]

        return output["value"]

    def get_stats(self) -> dict[str, int | float]:
        total_events = self._run_sync(self._count_events())
        max_events = int(self._max_events)
        utilization = round((total_events / max_events) * 100, 2) if max_events > 0 else 0.0

        return {
            "total_events": total_events,
            "max_events": max_events,
            "utilization": utilization,
        }


analytics_store = AnalyticsStore()
