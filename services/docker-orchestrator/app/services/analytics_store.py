"""
In-memory analytics storage service.

Stores analytics events for the dashboard.
Can be extended to use PostgreSQL for persistence.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import asyncio

class AnalyticsStore:
    """
    In-memory store for analytics events.

    Events are stored in a deque with max size to prevent memory issues.
    For production, this should be replaced with PostgreSQL.
    """

    def __init__(self, max_events: int = 10000):
        self._events: deque = deque(maxlen=max_events)
        self._lock = asyncio.Lock()

    async def add_event(self, event_type: str, event_data: Dict) -> Dict:
        """
        Add an analytics event.

        Args:
            event_type: Type of event (api_call, llm_call, deployment, etc.)
            event_data: Event-specific data

        Returns:
            The created event record
        """
        async with self._lock:
            event = {
                "event_type": event_type,
                "event_data": event_data,
                "created_at": datetime.utcnow(),
            }
            self._events.append(event)
            return event

    async def get_events_since(self, since: datetime) -> List[Dict]:
        """
        Get all events since a given timestamp.

        Args:
            since: Datetime to filter from

        Returns:
            List of events
        """
        async with self._lock:
            return [
                e for e in self._events
                if e.get("created_at", datetime.min) >= since
            ]

    async def get_events_by_type(
        self, event_type: str, since: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get events of a specific type.

        Args:
            event_type: Type of event to filter
            since: Optional datetime filter

        Returns:
            List of filtered events
        """
        events = await self.get_events_since(since or datetime.min) if since else list(self._events)

        return [
            e for e in events
            if e.get("event_type") == event_type
        ]

    async def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """
        Get the most recent events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        async with self._lock:
            events = list(self._events)
            return events[-limit:] if limit < len(events) else events

    async def clear_old_events(self, older_than_days: int = 90) -> int:
        """
        Remove events older than specified days.

        Args:
            older_than_days: Remove events older than this many days

        Returns:
            Number of events removed
        """
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        removed = 0

        async with self._lock:
            original_size = len(self._events)
            self._events = deque(
                (e for e in self._events if e.get("created_at", datetime.min) >= cutoff),
                maxlen=self._events.maxlen
            )
            removed = original_size - len(self._events)

        return removed

    def get_stats(self) -> Dict:
        """
        Get storage statistics.

        Returns:
            Dict with count and max size
        """
        return {
            "total_events": len(self._events),
            "max_events": self._events.maxlen,
            "utilization": round(len(self._events) / self._events.maxlen * 100, 2),
        }


# Global singleton instance
analytics_store = AnalyticsStore()
