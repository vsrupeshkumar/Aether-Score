"""Unit tests for StreamingScorer (services/streaming_scorer.py)."""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio

from services.streaming_scorer import (
    AsyncioQueue,
    ChainEvent,
    ScoreDeltaCalculator,
    StreamingScoreCache,
    StreamingScorer,
)


def _event(event_type: str, address: str = "0xtest", value: float = 1.0) -> ChainEvent:
    return ChainEvent(
        event_id=f"{address}-{event_type}-{value}",
        address=address,
        event_type=event_type,
        value=value,
        timestamp=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# ChainEvent
# ---------------------------------------------------------------------------

class TestChainEvent:
    def test_canonical_key_deterministic(self):
        e = _event("transaction", address="0xA", value=1.0)
        assert e.canonical_key == e.canonical_key

    def test_different_events_different_keys(self):
        e1 = _event("transaction", "0xA")
        e2 = _event("transaction", "0xB")
        assert e1.canonical_key != e2.canonical_key


# ---------------------------------------------------------------------------
# AsyncioQueue
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestAsyncioQueue:
    async def test_enqueue_dequeue(self):
        q = AsyncioQueue()
        e = _event("transaction")
        await q.enqueue(e)
        result = await q.dequeue()
        assert result is not None
        assert result.event_id == e.event_id

    async def test_empty_queue_returns_none(self):
        q = AsyncioQueue()
        result = await q.dequeue()
        assert result is None

    async def test_duplicate_event_dropped(self):
        q = AsyncioQueue()
        e = _event("transaction")
        await q.enqueue(e)
        await q.enqueue(e)  # duplicate
        assert await q.size() == 1

    async def test_size_reflects_contents(self):
        q = AsyncioQueue()
        for i in range(3):
            await q.enqueue(_event("transaction", address=f"0x{i}"))
        assert await q.size() == 3


# ---------------------------------------------------------------------------
# ScoreDeltaCalculator
# ---------------------------------------------------------------------------

class TestScoreDeltaCalculator:
    def setup_method(self):
        self.calc = ScoreDeltaCalculator()

    def test_repayment_positive_delta(self):
        d = self.calc.compute_delta(_event("loan_repaid"), 500.0)
        assert d > 0

    def test_default_negative_delta(self):
        d = self.calc.compute_delta(_event("loan_defaulted"), 500.0)
        assert d < 0

    def test_liquidation_largest_negative(self):
        d_liq = self.calc.compute_delta(_event("liquidation"), 500.0)
        d_def = self.calc.compute_delta(_event("loan_defaulted"), 500.0)
        assert d_liq <= d_def  # liquidation should be worse or equal

    def test_stake_positive(self):
        d = self.calc.compute_delta(_event("stake"), 500.0)
        assert d > 0

    def test_high_score_dampens_positive_delta(self):
        d_normal = self.calc.compute_delta(_event("loan_repaid"), 500.0)
        d_high = self.calc.compute_delta(_event("loan_repaid"), 950.0)
        assert d_high < d_normal  # dampened near ceiling

    def test_low_score_dampens_negative_delta(self):
        d_normal = self.calc.compute_delta(_event("loan_defaulted"), 500.0)
        d_low = self.calc.compute_delta(_event("loan_defaulted"), 50.0)
        assert abs(d_low) < abs(d_normal)  # dampened near floor

    def test_large_outflow_adds_penalty(self):
        large = _event("transaction", value=100.0)  # > threshold (10 ETH)
        small = _event("transaction", value=0.01)
        d_large = self.calc.compute_delta(large, 500.0)
        d_small = self.calc.compute_delta(small, 500.0)
        assert d_large < d_small


# ---------------------------------------------------------------------------
# StreamingScoreCache
# ---------------------------------------------------------------------------

class TestStreamingScoreCache:
    def test_set_and_get(self):
        cache = StreamingScoreCache()
        cache.set("0xA", 600.0, 10.0, "loan_repaid")
        record = cache.get("0xA")
        assert record is not None
        assert record["streaming_score"] == 600.0

    def test_address_normalised_lowercase(self):
        cache = StreamingScoreCache()
        cache.set("0xABCDEF", 700.0, 5.0, "stake")
        assert cache.get("0xabcdef") is not None

    def test_all_scores(self):
        cache = StreamingScoreCache()
        cache.set("0xA", 500.0, 0.0, "transaction")
        cache.set("0xB", 600.0, 0.0, "transaction")
        assert len(cache.all_scores()) == 2


# ---------------------------------------------------------------------------
# StreamingScorer integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestStreamingScorer:
    async def test_score_starts_at_initial(self):
        scorer = StreamingScorer(initial_score=500.0)
        assert scorer.get_score("0xNew") is None

    async def test_ingest_and_process(self):
        scorer = StreamingScorer(initial_score=500.0)
        event = _event("loan_repaid", address="0xUser")
        await scorer.ingest(event)
        await scorer._process(event)
        record = scorer.get_score("0xuser")
        assert record is not None
        assert record["streaming_score"] > 500.0  # repayment should boost score

    async def test_floor_respected(self):
        scorer = StreamingScorer(initial_score=10.0, score_floor=0.0)
        for _ in range(20):
            await scorer._process(_event("liquidation", address="0xPoor"))
        record = scorer.get_score("0xpoor")
        assert record["streaming_score"] >= 0.0

    async def test_ceiling_respected(self):
        scorer = StreamingScorer(initial_score=990.0, score_ceiling=1000.0)
        for _ in range(20):
            await scorer._process(_event("loan_repaid", address="0xRich"))
        record = scorer.get_score("0xrich")
        assert record["streaming_score"] <= 1000.0

    async def test_listener_called(self):
        calls = []
        scorer = StreamingScorer(initial_score=500.0)
        scorer.add_listener(lambda addr, score, delta: calls.append((addr, score, delta)))
        await scorer._process(_event("stake", address="0xStaker"))
        assert len(calls) == 1
        assert calls[0][0] == "0xstaker"

    async def test_run_stops(self):
        scorer = StreamingScorer()
        task = asyncio.create_task(scorer.run())
        await asyncio.sleep(0.1)
        await scorer.stop()
        await asyncio.wait_for(task, timeout=2.0)
        assert not scorer._running

    async def test_queue_size_reflects_ingested(self):
        scorer = StreamingScorer()
        for i in range(5):
            await scorer.ingest(_event("transaction", address=f"0x{i}"))
        size = await scorer.queue_size()
        assert size == 5

    async def test_edge_case_empty_wallet_no_crash(self):
        scorer = StreamingScorer()
        event = ChainEvent(event_id="e1", address="0xEmpty", event_type="transaction", value=0.0)
        await scorer._process(event)  # should not raise
