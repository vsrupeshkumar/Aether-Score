"""
Real-Time Streaming Scoring Pipeline — Phase 1 Extension

Implements an event-driven, incremental score update system that runs
PARALLEL to the existing batch ScoringService.  The existing API is
unchanged; this pipeline feeds a separate /stream/* endpoint family.

Architecture
------------
  BlockchainEventSource  →  EventQueue  →  StreamingScorer  →  ScoreCache

Queue back-end is abstracted via QueueBackend so callers can swap between
asyncio (dev), Redis Streams (production), or any future broker.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event model
# ---------------------------------------------------------------------------

@dataclass
class ChainEvent:
    """
    Normalised representation of a blockchain event (transaction, transfer, etc.)
    that triggers an incremental score update.
    """
    event_id: str
    address: str
    event_type: str          # "transaction" | "token_transfer" | "loan_repaid" | "loan_defaulted" | "stake"
    value: float             # native token value or token amount
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def canonical_key(self) -> str:
        """Deduplication key — same address + event_id is idempotent."""
        return hashlib.sha256(f"{self.address}:{self.event_id}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Queue abstraction
# ---------------------------------------------------------------------------

class QueueBackend(ABC):
    @abstractmethod
    async def enqueue(self, event: ChainEvent) -> None: ...

    @abstractmethod
    async def dequeue(self) -> Optional[ChainEvent]: ...

    @abstractmethod
    async def size(self) -> int: ...


class AsyncioQueue(QueueBackend):
    """In-process asyncio queue — suitable for single-process deployments."""

    def __init__(self, maxsize: int = 10_000):
        self._q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._seen: set = set()

    async def enqueue(self, event: ChainEvent) -> None:
        key = event.canonical_key
        if key in self._seen:
            logger.debug("Duplicate event ignored: %s", key)
            return
        self._seen.add(key)
        # Evict oldest seen keys to prevent unbounded growth
        if len(self._seen) > 50_000:
            self._seen = set(list(self._seen)[-25_000:])
        try:
            self._q.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("StreamingScorer queue full — dropping event %s", key)

    async def dequeue(self) -> Optional[ChainEvent]:
        try:
            return self._q.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def size(self) -> int:
        return self._q.qsize()


class RedisStreamQueue(QueueBackend):
    """
    Redis Streams-backed queue for multi-process / Kubernetes deployments.
    Requires `redis.asyncio` package (included in requirements.txt as `redis`).
    """

    def __init__(
        self,
        stream_key: str = "aether:score:events",
        consumer_group: str = "scoring-workers",
        consumer_name: str = "worker-0",
        redis_url: str = "redis://localhost:6379/0",
    ):
        self.stream_key = stream_key
        self.group = consumer_group
        self.consumer = consumer_name
        self.redis_url = redis_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self.redis_url, decode_responses=True)
            try:
                await self._client.xgroup_create(self.stream_key, self.group, id="0", mkstream=True)
            except Exception:
                pass  # group already exists
        return self._client

    async def enqueue(self, event: ChainEvent) -> None:
        client = await self._get_client()
        payload = {
            "event_id": event.event_id,
            "address": event.address,
            "event_type": event.event_type,
            "value": str(event.value),
            "timestamp": event.timestamp.isoformat(),
            "metadata": json.dumps(event.metadata),
        }
        await client.xadd(self.stream_key, payload, maxlen=100_000, approximate=True)

    async def dequeue(self) -> Optional[ChainEvent]:
        client = await self._get_client()
        results = await client.xreadgroup(
            self.group, self.consumer, {self.stream_key: ">"}, count=1, block=0
        )
        if not results:
            return None
        _, messages = results[0]
        msg_id, data = messages[0]
        await client.xack(self.stream_key, self.group, msg_id)
        return ChainEvent(
            event_id=data["event_id"],
            address=data["address"],
            event_type=data["event_type"],
            value=float(data["value"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=json.loads(data.get("metadata", "{}")),
        )

    async def size(self) -> int:
        client = await self._get_client()
        info = await client.xinfo_stream(self.stream_key)
        return info.get("length", 0)


# ---------------------------------------------------------------------------
# Incremental delta model
# ---------------------------------------------------------------------------

class ScoreDeltaCalculator:
    """
    Computes incremental score deltas from a single ChainEvent without
    running the full ScoringService pipeline.

    Positive events (repayment, stake) → +delta
    Negative events (default, high-value outflow) → -delta
    """

    # Points awarded / deducted per event type
    _DELTAS: Dict[str, float] = {
        "loan_repaid": +15.0,
        "stake": +8.0,
        "stake_increase": +12.0,
        "transaction": 0.0,         # neutral — direction depends on value
        "token_transfer": 0.0,
        "loan_defaulted": -40.0,
        "loan_late": -10.0,
        "liquidation": -50.0,
        "large_outflow": -5.0,
    }

    # Threshold above which a transaction is considered a "large outflow"
    LARGE_OUTFLOW_THRESHOLD_ETH: float = 10.0

    def compute_delta(self, event: ChainEvent, current_score: float) -> float:
        base = self._DELTAS.get(event.event_type, 0.0)

        # Add small credit for regular on-chain activity
        if event.event_type == "transaction" and event.value > 0:
            base += 1.0

        # Penalise very large outflows
        if event.event_type in ("transaction", "token_transfer"):
            if event.value > self.LARGE_OUTFLOW_THRESHOLD_ETH:
                base -= 3.0

        # Dampen effect as score approaches extremes (prevent runaway)
        if base > 0 and current_score > 900:
            base *= 0.25
        elif base < 0 and current_score < 100:
            base *= 0.25

        return round(base, 2)


# ---------------------------------------------------------------------------
# Score cache
# ---------------------------------------------------------------------------

class StreamingScoreCache:
    """
    Lightweight in-memory cache of the latest streaming score per address.
    Production: back with Redis with TTL.
    """

    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def get(self, address: str) -> Optional[Dict]:
        return self._cache.get(address.lower())

    def set(self, address: str, score: float, delta: float, event_type: str) -> None:
        self._cache[address.lower()] = {
            "streaming_score": round(score, 2),
            "last_delta": delta,
            "last_event_type": event_type,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def all_scores(self) -> Dict[str, Dict]:
        return dict(self._cache)


# ---------------------------------------------------------------------------
# Main streaming scorer
# ---------------------------------------------------------------------------

class StreamingScorer:
    """
    Core engine:  consumes ChainEvents → applies incremental deltas →
    updates StreamingScoreCache.

    This runs as a background asyncio task alongside the FastAPI server.
    It does NOT touch the existing ScoringService or its endpoints.
    """

    def __init__(
        self,
        queue: Optional[QueueBackend] = None,
        initial_score: float = 500.0,
        score_floor: float = 0.0,
        score_ceiling: float = 1000.0,
    ):
        self.queue = queue or AsyncioQueue()
        self.delta_calc = ScoreDeltaCalculator()
        self.cache = StreamingScoreCache()
        self.initial_score = initial_score
        self.score_floor = score_floor
        self.score_ceiling = score_ceiling
        self._running = False
        self._processed = 0
        self._listeners: List[Callable[[str, float, float], None]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_listener(self, fn: Callable[[str, float, float], None]) -> None:
        """Register a callback(address, new_score, delta) for real-time push."""
        self._listeners.append(fn)

    async def ingest(self, event: ChainEvent) -> None:
        """Push a blockchain event into the processing queue."""
        await self.queue.enqueue(event)

    def get_score(self, address: str) -> Optional[Dict]:
        """Return latest streaming score for an address."""
        return self.cache.get(address)

    def get_all_scores(self) -> Dict[str, Dict]:
        return self.cache.all_scores()

    async def queue_size(self) -> int:
        return await self.queue.size()

    # ------------------------------------------------------------------
    # Background processing loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """
        Long-running consumer loop.
        Start with:  asyncio.create_task(streaming_scorer.run())
        """
        self._running = True
        logger.info("StreamingScorer started")
        while self._running:
            event = await self.queue.dequeue()
            if event is None:
                await asyncio.sleep(0.05)
                continue
            await self._process(event)

    async def stop(self) -> None:
        self._running = False
        logger.info("StreamingScorer stopped after %d events", self._processed)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _process(self, event: ChainEvent) -> None:
        try:
            cached = self.cache.get(event.address)
            current_score = cached["streaming_score"] if cached else self.initial_score

            delta = self.delta_calc.compute_delta(event, current_score)
            new_score = max(self.score_floor, min(self.score_ceiling, current_score + delta))

            self.cache.set(event.address, new_score, delta, event.event_type)
            self._processed += 1

            # Notify listeners (e.g. WebSocket push)
            for fn in self._listeners:
                try:
                    fn(event.address, new_score, delta)
                except Exception as exc:
                    logger.warning("Listener error: %s", exc)

            if delta != 0:
                logger.debug(
                    "Score updated",
                    extra={"address": event.address, "delta": delta, "new_score": new_score},
                )

        except Exception as exc:
            logger.error("Error processing event %s: %s", event.event_id, exc, exc_info=True)

    # ------------------------------------------------------------------
    # SSE / WebSocket stream helper
    # ------------------------------------------------------------------

    async def event_stream(self, address: str) -> AsyncGenerator[Dict, None]:
        """
        Async generator that yields score updates for a specific address.
        Suitable for Server-Sent Events or WebSocket.
        """
        last_update: Optional[str] = None
        while True:
            record = self.cache.get(address)
            if record and record.get("updated_at") != last_update:
                last_update = record["updated_at"]
                yield {"address": address, **record}
            await asyncio.sleep(1.0)


# ---------------------------------------------------------------------------
# Module-level singleton (lazy-init)
# ---------------------------------------------------------------------------

_instance: Optional[StreamingScorer] = None


def get_streaming_scorer() -> StreamingScorer:
    global _instance
    if _instance is None:
        import os
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            queue = RedisStreamQueue(redis_url=redis_url)
        else:
            queue = AsyncioQueue()
        _instance = StreamingScorer(queue=queue)
        logger.info("StreamingScorer singleton created (backend=%s)", type(queue).__name__)
    return _instance
