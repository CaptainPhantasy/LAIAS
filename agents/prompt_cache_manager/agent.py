"""
PromptCacheManager - Prompt Caching System for Long-Running Agentic Projects

Implements Anthropic-style ephemeral caching with:
- Sliding Checkpoint pattern (cache_control blocks)
- Static Prefix Rule (static content first, dynamic last)
- 5-minute TTL management with heartbeat refreshers
- Multi-tier cache support (ephemeral, session, persistent)
- Dashboard for monitoring cache efficiency and cost savings

Cost Comparison:
- Without caching: 100% token cost, lossy summarization
- With caching: 10% read cost, 90% savings, perfect fidelity
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import threading
from collections import defaultdict


class CacheTier(Enum):
    """Cache tier with different TTLs"""
    EPHEMERAL = "ephemeral"   # 5-minute TTL (Anthropic default)
    SESSION = "session"       # 24-hour TTL
    PERSISTENT = "persistent" # Project-level, no TTL


class CacheStatus(Enum):
    """Cache hit/miss status"""
    HIT = "hit"       # Cache read at 10% cost
    MISS = "miss"     # Full write at 100% cost + 25% premium
    REFRESH = "refresh"  # Heartbeat to keep alive


@dataclass
class CacheMetrics:
    """Track cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_cached: int = 0
    tokens_read_from_cache: int = 0
    tokens_written: int = 0
    cost_saved_usd: float = 0.0
    heartbeat_count: int = 0
    cache_invalidations: int = 0
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests * 100
    
    @property
    def savings_percentage(self) -> float:
        """Calculate cost savings vs no-cache"""
        if self.tokens_read_from_cache == 0:
            return 0.0
        # Cache reads cost 10%, writes cost 125% (100% + 25% premium)
        # Full price would be 100% of all tokens
        full_cost_tokens = self.tokens_read_from_cache + self.tokens_written
        # With cache: 10% of reads + 125% of writes
        cached_cost_tokens = (self.tokens_read_from_cache * 0.10) + (self.tokens_written * 1.25)
        savings = (1 - cached_cost_tokens / full_cost_tokens) * 100 if full_cost_tokens > 0 else 0
        return max(0, savings)


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    content_hash: str
    tier: CacheTier
    created_at: datetime
    last_accessed: datetime
    token_count: int
    messages: List[Dict] = field(default_factory=list)
    static_prefix_hash: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired based on tier"""
        if self.tier == CacheTier.PERSISTENT:
            return False
        elif self.tier == CacheTier.EPHEMERAL:
            ttl = timedelta(minutes=5)
        elif self.tier == CacheTier.SESSION:
            ttl = timedelta(hours=24)
        else:
            return False
        return datetime.now() - self.last_accessed > ttl
    
    def touch(self):
        """Update last accessed time"""
        self.last_accessed = datetime.now()


@dataclass
class CacheControlBlock:
    """Anthropic-style cache control block"""
    type: str = "ephemeral"  # Currently only "ephemeral" is supported
    
    def to_dict(self) -> Dict:
        return {"cache_control": {"type": self.type}}


class StaticPrefixManager:
    """
    Manages the Static Prefix Rule:
    - Static content (codebase structure, core instructions, tool definitions) at beginning
    - Dynamic content (timestamps, session-specific tasks) at the end
    
    Why: If a single character changes at the start, entire cache is invalidated.
    """
    
    def __init__(self):
        self.static_sections: Dict[str, str] = {}
        self.section_order: List[str] = []
    
    def add_static_section(self, name: str, content: str, position: int = None):
        """Add a static section that will be cached"""
        if position is not None:
            if name not in self.section_order:
                self.section_order.insert(position, name)
        else:
            if name not in self.section_order:
                self.section_order.append(name)
        self.static_sections[name] = content
    
    def build_prefix(self) -> str:
        """Build the complete static prefix in order"""
        return "\n\n".join(
            self.static_sections[name] 
            for name in self.section_order 
            if name in self.static_sections
        )
    
    def get_hash(self) -> str:
        """Get hash of static prefix for cache validation"""
        content = self.build_prefix()
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class HeartbeatManager:
    """
    Manages the 5-minute TTL workaround:
    Sends heartbeat requests every 4 minutes to keep cache alive.
    """
    
    def __init__(self, cache_manager: 'PromptCacheManager', interval_seconds: int = 240):
        self.cache_manager = cache_manager
        self.interval_seconds = interval_seconds  # 4 minutes default
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_heartbeat: Optional[datetime] = None
    
    def start(self):
        """Start heartbeat thread"""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop heartbeat thread"""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to keep cache alive"""
        while self._running and not self._stop_event.is_set():
            try:
                self._send_heartbeat()
            except Exception as e:
                print(f"Heartbeat error: {e}")
            
            # Wait for interval or until stopped
            if self._stop_event.wait(timeout=self.interval_seconds):
                break
    
    def _send_heartbeat(self):
        """Send a minimal heartbeat request to refresh cache TTL"""
        self.last_heartbeat = datetime.now()
        self.cache_manager.metrics.heartbeat_count += 1
        # Touch all active ephemeral entries
        self.cache_manager._refresh_ephemeral_entries()
        print(f"[Heartbeat] Cache TTL refreshed at {self.last_heartbeat.isoformat()}")


class PromptCacheManager:
    """
    Main Prompt Caching System
    
    Implements:
    1. Sliding Checkpoint Pattern - cache_control on last Assistant message
    2. Static Prefix Rule - static content first, dynamic last
    3. TTL Management - heartbeats every 4 minutes
    4. Multi-tier caching - ephemeral, session, persistent
    """
    
    def __init__(
        self,
        default_tier: CacheTier = CacheTier.EPHEMERAL,
        enable_heartbeat: bool = True,
        heartbeat_interval: int = 240,  # 4 minutes
        price_per_million_input: float = 3.0,  # Claude pricing
        price_per_million_cache_read: float = 0.30,  # 10% of input
        price_per_million_cache_write: float = 3.75,  # 125% of input
    ):
        self.default_tier = default_tier
        self.cache: Dict[str, CacheEntry] = {}
        self.metrics = CacheMetrics()
        self.prefix_manager = StaticPrefixManager()
        self.heartbeat_manager = HeartbeatManager(self, heartbeat_interval) if enable_heartbeat else None
        
        # Pricing (USD per million tokens)
        self.price_per_million_input = price_per_million_input
        self.price_per_million_cache_read = price_per_million_cache_read
        self.price_per_million_cache_write = price_per_million_cache_write
        
        if enable_heartbeat:
            self.heartbeat_manager.start()
    
    def shutdown(self):
        """Clean shutdown"""
        if self.heartbeat_manager:
            self.heartbeat_manager.stop()
    
    # ==================== Sliding Checkpoint Pattern ====================
    
    def build_messages_with_checkpoint(
        self,
        system_prompt: str,
        conversation_history: List[Dict],
        new_user_message: str,
        static_prefix: Optional[str] = None,
    ) -> List[Dict]:
        """
        Build messages with Sliding Checkpoint pattern.
        
        Places cache_control block on the last Assistant message to checkpoint
        the entire conversation history.
        
        Args:
            system_prompt: System instructions (static)
            conversation_history: Prior messages
            new_user_message: Current user input (dynamic)
            static_prefix: Optional static prefix for system
        
        Returns:
            Messages array with proper cache_control placement
        """
        messages = []
        
        # 1. System message with static prefix (marked for caching)
        system_content = system_prompt
        if static_prefix:
            system_content = f"{static_prefix}\n\n{system_prompt}"
        
        # Mark system for caching if it's static content
        messages.append({
            "role": "system",
            "content": system_content,
            "cache_control": {"type": "ephemeral"}
        })
        
        # 2. Conversation history
        for msg in conversation_history:
            messages.append(msg)
        
        # 3. Last Assistant message gets cache_control (THE CHECKPOINT)
        if conversation_history and conversation_history[-1].get("role") == "assistant":
            messages[-1]["cache_control"] = {"type": "ephemeral"}
        
        # 4. New user message (dynamic - no caching)
        messages.append({
            "role": "user",
            "content": new_user_message
            # NO cache_control - this is dynamic content
        })
        
        return messages
    
    # ==================== Static Prefix Rule ====================
    
    def create_api_request(
        self,
        model: str,
        static_content: Dict[str, str],
        dynamic_content: Dict[str, Any],
        conversation_history: List[Dict] = None,
    ) -> Dict:
        """
        Create API request following Static Prefix Rule.
        
        CRITICAL: Static content MUST come first. Dynamic content at the end.
        If ANY character changes in static content, entire cache is invalidated.
        
        Args:
            model: Model identifier
            static_content: Dict of {section_name: content} for static parts
            dynamic_content: Dict of {key: value} for dynamic parts (timestamps, etc)
            conversation_history: Prior messages
        """
        # Build static prefix in defined order
        for name, content in static_content.items():
            self.prefix_manager.add_static_section(name, content)
        
        static_prefix = self.prefix_manager.build_prefix()
        static_hash = self.prefix_manager.get_hash()
        
        # Build system message with static prefix
        system_message = {
            "role": "system",
            "content": static_prefix,
            "cache_control": {"type": "ephemeral"}
        }
        
        messages = [system_message]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append(msg)
            
            # Add checkpoint to last assistant message
            if conversation_history[-1].get("role") == "assistant":
                messages[-1]["cache_control"] = {"type": "ephemeral"}
        
        # Dynamic content goes in the final user message
        dynamic_str = "\n".join(f"{k}: {v}" for k, v in dynamic_content.items())
        messages.append({
            "role": "user",
            "content": f"Current context:\n{dynamic_str}"
            # NO cache_control on dynamic content
        })
        
        return {
            "model": model,
            "messages": messages,
            "metadata": {
                "static_prefix_hash": static_hash,
                "cache_tier": self.default_tier.value
            }
        }
    
    # ==================== Cache Management ====================
    
    def get_or_create(
        self,
        key: str,
        content_generator: callable,
        tier: CacheTier = None,
    ) -> tuple[CacheEntry, CacheStatus]:
        """
        Get from cache or create new entry.
        
        Returns:
            (CacheEntry, CacheStatus) tuple
        """
        tier = tier or self.default_tier
        self.metrics.total_requests += 1
        
        if key in self.cache:
            entry = self.cache[key]
            
            if entry.is_expired():
                # Cache expired - need to refresh
                del self.cache[key]
                self.metrics.cache_invalidations += 1
            else:
                # Cache hit!
                entry.touch()
                self.metrics.cache_hits += 1
                self.metrics.tokens_read_from_cache += entry.token_count
                self._update_cost_savings(entry.token_count, is_hit=True)
                return entry, CacheStatus.HIT
        
        # Cache miss - generate new
        self.metrics.cache_misses += 1
        content = content_generator()
        token_count = self._estimate_tokens(content)
        
        entry = CacheEntry(
            key=key,
            content_hash=hashlib.sha256(str(content).encode()).hexdigest()[:16],
            tier=tier,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            token_count=token_count,
            messages=content if isinstance(content, list) else [],
        )
        
        self.cache[key] = entry
        self.metrics.tokens_written += token_count
        self.metrics.tokens_cached += token_count
        self._update_cost_savings(token_count, is_hit=False)
        
        return entry, CacheStatus.MISS
    
    def _estimate_tokens(self, content: Any) -> int:
        """Estimate token count (rough: 4 chars per token)"""
        text = str(content)
        return len(text) // 4
    
    def _update_cost_savings(self, tokens: int, is_hit: bool):
        """Update cost savings metrics"""
        if is_hit:
            # Saved: full price minus cache read price
            saved = (self.price_per_million_input - self.price_per_million_cache_read) * tokens / 1_000_000
            self.metrics.cost_saved_usd += saved
        # Miss costs are tracked in tokens_written
    
    def _refresh_ephemeral_entries(self):
        """Touch all ephemeral entries to keep them alive (heartbeat)"""
        now = datetime.now()
        for entry in self.cache.values():
            if entry.tier == CacheTier.EPHEMERAL:
                entry.touch()
    
    # ==================== Dashboard ====================
    
    def get_dashboard_data(self) -> Dict:
        """Get cache performance dashboard data"""
        entries_by_tier = defaultdict(int)
        for entry in self.cache.values():
            entries_by_tier[entry.tier.value] += 1
        
        return {
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "hit_rate_percent": round(self.metrics.hit_rate, 2),
                "tokens_cached": self.metrics.tokens_cached,
                "tokens_read_from_cache": self.metrics.tokens_read_from_cache,
                "tokens_written": self.metrics.tokens_written,
                "cost_saved_usd": round(self.metrics.cost_saved_usd, 4),
                "savings_percent": round(self.metrics.savings_percentage, 2),
                "heartbeat_count": self.metrics.heartbeat_count,
                "invalidations": self.metrics.cache_invalidations,
            },
            "cache_state": {
                "total_entries": len(self.cache),
                "entries_by_tier": dict(entries_by_tier),
            },
            "heartbeat": {
                "enabled": self.heartbeat_manager is not None,
                "interval_seconds": self.heartbeat_manager.interval_seconds if self.heartbeat_manager else None,
                "last_heartbeat": self.heartbeat_manager.last_heartbeat.isoformat() if self.heartbeat_manager and self.heartbeat_manager.last_heartbeat else None,
            },
            "pricing": {
                "per_million_input": self.price_per_million_input,
                "per_million_cache_read": self.price_per_million_cache_read,
                "per_million_cache_write": self.price_per_million_cache_write,
            }
        }
    
    def print_dashboard(self):
        """Print a formatted dashboard"""
        data = self.get_dashboard_data()
        m = data["metrics"]
        
        print("\n" + "=" * 60)
        print("          PROMPT CACHE MANAGER DASHBOARD")
        print("=" * 60)
        print(f"\n  PERFORMANCE METRICS")
        print(f"  ─────────────────────────────────────")
        print(f"  Total Requests:      {m['total_requests']:,}")
        print(f"  Cache Hits:          {m['cache_hits']:,}")
        print(f"  Cache Misses:        {m['cache_misses']:,}")
        print(f"  Hit Rate:            {m['hit_rate_percent']}%")
        print(f"\n  TOKEN ECONOMICS")
        print(f"  ─────────────────────────────────────")
        print(f"  Tokens Cached:       {m['tokens_cached']:,}")
        print(f"  Tokens Read (10%):   {m['tokens_read_from_cache']:,}")
        print(f"  Tokens Written:      {m['tokens_written']:,}")
        print(f"  Cost Saved:          ${m['cost_saved_usd']}")
        print(f"  Savings vs No-Cache: {m['savings_percent']}%")
        print(f"\n  CACHE HEALTH")
        print(f"  ─────────────────────────────────────")
        print(f"  Heartbeats Sent:     {m['heartbeat_count']}")
        print(f"  Cache Invalidations: {m['invalidations']}")
        hb = data["heartbeat"]
        if hb["enabled"]:
            print(f"  Last Heartbeat:      {hb['last_heartbeat'] or 'Never'}")
        print("=" * 60 + "\n")


# ==================== Convenience Functions ====================

def create_cached_request(
    model: str,
    system_instructions: str,
    codebase_structure: str,
    tool_definitions: str,
    conversation_history: List[Dict],
    current_task: str,
    current_timestamp: str,
) -> Dict:
    """
    Convenience function to create a properly cached API request.
    
    This follows all three rules:
    1. Sliding Checkpoint - cache_control on messages
    2. Static Prefix - static content first
    3. Ready for heartbeat management
    """
    manager = PromptCacheManager(enable_heartbeat=False)  # Stateless usage
    
    static_content = {
        "codebase_structure": codebase_structure,
        "system_instructions": system_instructions,
        "tool_definitions": tool_definitions,
    }
    
    dynamic_content = {
        "current_timestamp": current_timestamp,
        "current_task": current_task,
    }
    
    return manager.create_api_request(
        model=model,
        static_content=static_content,
        dynamic_content=dynamic_content,
        conversation_history=conversation_history,
    )


# ==================== Example Usage ====================

if __name__ == "__main__":
    print("PromptCacheManager - Demo")
    print("=" * 40)
    
    # Initialize with heartbeat enabled
    manager = PromptCacheManager(
        default_tier=CacheTier.EPHEMERAL,
        enable_heartbeat=True,
        heartbeat_interval=10,  # Fast for demo
    )
    
    try:
        # Demo: Static content (would be your project context)
        static_content = {
            "project_structure": """
            /my-project
            ├── src/
            │   ├── agents/
            │   ├── utils/
            │   └── api/
            ├── tests/
            └── docs/
            """,
            "core_instructions": "You are a helpful coding assistant...",
            "tool_definitions": "Available tools: read_file, write_file, run_tests",
        }
        
        # Demo: Dynamic content (changes each session)
        dynamic_content = {
            "current_time": datetime.now().isoformat(),
            "task": "Fix the bug in auth.py",
        }
        
        # Create cached request
        request = manager.create_api_request(
            model="claude-sonnet-4-20250514",
            static_content=static_content,
            dynamic_content=dynamic_content,
        )
        
        print("\nGenerated API Request Structure:")
        print(f"  Model: {request['model']}")
        print(f"  Messages: {len(request['messages'])}")
        print(f"  Static Prefix Hash: {request['metadata']['static_prefix_hash']}")
        
        # Simulate cache operations
        print("\nSimulating cache operations...")
        
        for i in range(5):
            entry, status = manager.get_or_create(
                key=f"conversation_turn_{i}",
                content_generator=lambda: [{"role": "user", "content": f"Turn {i}"}],
            )
            print(f"  Turn {i}: {status.value}")
            time.sleep(0.1)
        
        # Print dashboard
        manager.print_dashboard()
        
    finally:
        manager.shutdown()
