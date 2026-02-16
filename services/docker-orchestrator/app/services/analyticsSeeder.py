"""
Analytics seeder for generating sample data.

This creates realistic sample analytics data for testing the dashboard.
Run this to populate analytics with demo data.
"""

from datetime import datetime, timedelta
from random import randint, uniform, choices
from app.services.analytics_store import analytics_store


# Sample data
LLM_PROVIDERS = ["anthropic", "openai", "openrouter"]
MODELS = {
    "anthropic": ["claude-3-5-sonnet", "claude-3-5-haiku"],
    "openai": ["gpt-4-turbo", "gpt-3.5-turbo"],
    "openrouter": ["default"],
}
API_ENDPOINTS = [
    "/api/generate",
    "/api/deploy",
    "/api/containers",
    "/api/health",
    "/api/analytics",
]


async def seed_analytics(days: int = 30):
    """
    Seed analytics with sample data.

    Args:
        days: Number of days of historical data to generate
    """
    print(f"Seeding analytics with {days} days of sample data...")

    now = datetime.utcnow()

    # Generate data for each day
    for day_offset in range(days, 0, -1):
        date = now - timedelta(days=day_offset)

        # Generate 10-50 API calls per day
        num_calls = randint(10, 50)
        for _ in range(num_calls):
            call_time = date + timedelta(
                hours=randint(0, 23),
                minutes=randint(0, 59),
            )

            await analytics_store.add_event("api_call", {
                "endpoint": choices(API_ENDPOINTS, weights=[40, 20, 20, 10, 10])[0],
                "response_time_ms": randint(50, 500),
            }, call_time)

        # Generate 5-20 LLM calls per day
        num_llm = randint(5, 20)
        for _ in range(num_llm):
            llm_time = date + timedelta(
                hours=randint(0, 23),
                minutes=randint(0, 59),
            )
            provider = choices(LLM_PROVIDERS, weights=[50, 35, 15])[0]
            model = MODELS[provider][0]

            await analytics_store.add_event("llm_call", {
                "provider": provider,
                "model": model,
                "input_tokens": randint(100, 5000),
                "output_tokens": randint(50, 2000),
            }, llm_time)

        # Generate 1-5 deployments per day
        num_deployments = randint(1, 5)
        for _ in range(num_deployments):
            deploy_time = date + timedelta(
                hours=randint(0, 23),
                minutes=randint(0, 59),
            )
            # 85% success rate
            status = "running" if uniform(0, 1) < 0.85 else "error"

            await analytics_store.add_event("deployment", {
                "deployment_id": f"demo-{deploy_time.strftime('%Y%m%d-%H%M%S')}",
                "agent_id": f"agent-{randint(1000, 9999)}",
                "agent_name": f"Demo Agent {randint(1, 100)}",
                "status": status,
            }, deploy_time)

    store_stats = analytics_store.get_stats()
    print(f"Seeding complete!")
    print(f"  Total events: {store_stats['total_events']}")
    print(f"  Max events: {store_stats['max_events']}")
    print(f"  Utilization: {store_stats['utilization']}%")


# Monkey patch add_event to accept timestamp
async def add_event_with_time(self, event_type: str, event_data: dict, timestamp: datetime = None):
    """Add event with optional timestamp."""
    async with self._lock:
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "created_at": timestamp or datetime.utcnow(),
        }
        self._events.append(event)
        return event


# Patch the store temporarily
import app.services.analytics_store as analytics_module
original_add = analytics_module.AnalyticsStore.add_event
analytics_module.AnalyticsStore.add_event = add_event_with_time


async def run_seeder():
    """Run the seeder."""
    await seed_analytics(days=30)

    # Restore original
    analytics_module.AnalyticsStore.add_event = original_add


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_seeder())
