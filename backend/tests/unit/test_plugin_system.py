"""Unit tests for PluginSystem (services/plugin_system.py)."""

from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from services.plugin_system import (
    PluginRegistry,
    PluginResult,
    ScoringPipeline,
    ScoringPlugin,
)


# ---------------------------------------------------------------------------
# Concrete test plugins
# ---------------------------------------------------------------------------

class PositivePlugin(ScoringPlugin):
    priority = 10
    weight = 1.0

    @property
    def name(self) -> str:
        return "positive_test"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        return PluginResult(
            plugin_name=self.name,
            score_adjustment=50.0,
            confidence=1.0,
            explanation="always positive",
        )


class NegativePlugin(ScoringPlugin):
    priority = 20
    weight = 1.0

    @property
    def name(self) -> str:
        return "negative_test"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        return PluginResult(
            plugin_name=self.name,
            score_adjustment=-30.0,
            confidence=0.5,
            explanation="penalty plugin",
        )


class SkippingPlugin(ScoringPlugin):
    priority = 30
    weight = 1.0

    @property
    def name(self) -> str:
        return "skipping_test"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        return PluginResult(
            plugin_name=self.name,
            score_adjustment=100.0,
            confidence=0.0,
            skipped=True,
        )


class ErrorPlugin(ScoringPlugin):
    priority = 40
    weight = 1.0

    @property
    def name(self) -> str:
        return "error_test"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        raise RuntimeError("Test plugin error")


class ZeroWeightPlugin(ScoringPlugin):
    priority = 50
    weight = 0.0  # observer only

    @property
    def name(self) -> str:
        return "zero_weight"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        context["observed"] = True
        return PluginResult(plugin_name=self.name, score_adjustment=999.0, confidence=1.0)


# ---------------------------------------------------------------------------
# PluginRegistry tests
# ---------------------------------------------------------------------------

class TestPluginRegistry:
    def test_register_and_retrieve(self):
        reg = PluginRegistry()
        p = PositivePlugin()
        reg.register(p)
        assert reg.get("positive_test") is p

    def test_overwrite_logs_warning(self, caplog):
        import logging
        reg = PluginRegistry()
        reg.register(PositivePlugin())
        with caplog.at_level(logging.WARNING):
            reg.register(PositivePlugin())
        assert "already registered" in caplog.text

    def test_unregister(self):
        reg = PluginRegistry()
        reg.register(PositivePlugin())
        assert reg.unregister("positive_test") is True
        assert reg.get("positive_test") is None

    def test_unregister_missing_returns_false(self):
        reg = PluginRegistry()
        assert reg.unregister("nonexistent") is False

    def test_all_active_sorted_by_priority(self):
        reg = PluginRegistry()
        neg = NegativePlugin()   # priority 20
        pos = PositivePlugin()   # priority 10
        reg.register(neg)
        reg.register(pos)
        active = reg.all_active()
        assert active[0].name == "positive_test"  # lower priority first

    def test_disabled_plugin_excluded(self):
        reg = PluginRegistry()
        p = PositivePlugin()
        p.enabled = False
        reg.register(p)
        assert len(reg.all_active()) == 0

    def test_list_plugins_returns_metadata(self):
        reg = PluginRegistry()
        reg.register(PositivePlugin())
        info = reg.list_plugins()
        assert len(info) == 1
        assert info[0]["name"] == "positive_test"
        assert "version" in info[0]


# ---------------------------------------------------------------------------
# ScoringPipeline tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestScoringPipeline:
    def _make_pipeline(self, *plugins):
        reg = PluginRegistry()
        for p in plugins:
            reg.register(p)
        return ScoringPipeline(registry=reg)

    async def test_single_positive_plugin_raises_score(self):
        pipeline = self._make_pipeline(PositivePlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        assert result["final_score"] > 500.0

    async def test_single_negative_plugin_lowers_score(self):
        pipeline = self._make_pipeline(NegativePlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        assert result["final_score"] < 500.0

    async def test_mixed_plugins_weighted_correctly(self):
        # +50 @ confidence=1.0, weight=1.0 and -30 @ confidence=0.5, weight=1.0
        # weighted_adj = (50 * 1 * 1.0 + -30 * 1 * 0.5) / (1*1.0 + 1*0.5)
        #              = (50 - 15) / 1.5 = 35 / 1.5 ≈ 23.33
        pipeline = self._make_pipeline(PositivePlugin(), NegativePlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        assert result["final_score"] == pytest.approx(523.33, abs=0.1)

    async def test_skipped_plugin_excluded_from_score(self):
        pipeline = self._make_pipeline(PositivePlugin(), SkippingPlugin())
        result_with_skip = await pipeline.run("0xAddr", base_score=500.0)
        pipeline2 = self._make_pipeline(PositivePlugin())
        result_without_skip = await pipeline2.run("0xAddr", base_score=500.0)
        assert result_with_skip["final_score"] == result_without_skip["final_score"]

    async def test_error_plugin_doesnt_crash_pipeline(self):
        pipeline = self._make_pipeline(PositivePlugin(), ErrorPlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        # Error plugin should be reported but not crash
        assert result["final_score"] > 0
        error_results = [r for r in result["plugin_results"] if r["error"]]
        assert len(error_results) == 1

    async def test_zero_weight_plugin_doesnt_affect_score(self):
        pipeline = self._make_pipeline(ZeroWeightPlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        # No weight → no adjustment
        assert result["final_score"] == pytest.approx(500.0)

    async def test_zero_weight_plugin_can_modify_context(self):
        pipeline = self._make_pipeline(ZeroWeightPlugin())
        ctx = {}
        await pipeline.run("0xAddr", base_score=500.0, context=ctx)
        assert ctx.get("observed") is True

    async def test_empty_registry_returns_base_score(self):
        pipeline = self._make_pipeline()
        result = await pipeline.run("0xAddr", base_score=750.0)
        assert result["final_score"] == pytest.approx(750.0)

    async def test_score_bounded_0_1000(self):
        # Even if plugins push way over ceiling
        class HugePlugin(ScoringPlugin):
            priority = 1
            weight = 1.0

            @property
            def name(self):
                return "huge"

            async def compute(self, addr, ctx):
                return PluginResult(plugin_name=self.name, score_adjustment=5000.0, confidence=1.0)

        pipeline = self._make_pipeline(HugePlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        assert result["final_score"] <= 1000.0

    async def test_plugin_results_in_output(self):
        pipeline = self._make_pipeline(PositivePlugin(), NegativePlugin())
        result = await pipeline.run("0xAddr", base_score=500.0)
        names = [r["plugin"] for r in result["plugin_results"]]
        assert "positive_test" in names
        assert "negative_test" in names

    async def test_context_passed_to_plugins(self):
        received_context = {}

        class ContextCapture(ScoringPlugin):
            priority = 1
            weight = 0.0

            @property
            def name(self):
                return "ctx_capture"

            async def compute(self, addr, ctx):
                received_context.update(ctx)
                return PluginResult(plugin_name=self.name, score_adjustment=0.0, confidence=0.0)

        pipeline = self._make_pipeline(ContextCapture())
        await pipeline.run("0xAddr", base_score=600.0, context={"custom_key": "hello"})
        assert received_context.get("custom_key") == "hello"
        assert received_context.get("base_score") == 600.0
