"""
Modular Plugin System — Phase 1 Extension

Allows external or internal scoring plugins to register themselves and
participate in the final score computation via a weighted pipeline.

Design:
  - ScoringPlugin: abstract base class each plugin implements
  - PluginRegistry: central registry; plugins self-register
  - ScoringPipeline: runs registered plugins in priority order, merges results

Existing ScoringService is unchanged — the pipeline wraps it as the
"base" plugin with the highest priority.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plugin base class
# ---------------------------------------------------------------------------

@dataclass
class PluginResult:
    """Standardised output from a scoring plugin."""
    plugin_name: str
    score_adjustment: float          # positive or negative delta to apply
    confidence: float                # 0–1; used to weight the adjustment
    metadata: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    skipped: bool = False            # set True if plugin had insufficient data
    error: Optional[str] = None


class ScoringPlugin(ABC):
    """
    Abstract base for all scoring plugins.

    Implement `compute(address, context)` to return a PluginResult.
    `context` is the shared state dict passed through the pipeline.
    """

    # Lower priority number = runs first
    priority: int = 100

    # Weight controls how much this plugin's adjustment affects the final score.
    # Sum of all active plugin weights is used for normalisation.
    weight: float = 1.0

    # Set to False to disable without unregistering
    enabled: bool = True

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult: ...

    def validate_context(self, context: Dict) -> bool:
        """Override to check required context keys before running."""
        return True


# ---------------------------------------------------------------------------
# Built-in plugin implementations
# ---------------------------------------------------------------------------

class AdvancedRiskPlugin(ScoringPlugin):
    """Wraps AdvancedRiskModel into the plugin system."""

    priority = 20
    weight = 1.5

    @property
    def name(self) -> str:
        return "advanced_risk"

    @property
    def description(self) -> str:
        return "Bayesian + temporal decay + volatility risk modeling"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        try:
            from services.advanced_risk_model import AdvancedRiskModel
            model = AdvancedRiskModel()
            base_score = context.get("base_score", 500.0)
            profile = model.compute_full_risk_profile(
                address=address,
                base_score=base_score,
                transactions=context.get("transactions", []),
                loan_history=context.get("loan_history"),
                balance_history=context.get("balance_history"),
            )
            adj = profile["total_adjustment"]
            explanation = "; ".join(profile.get("risk_factors", [])) or "No additional risk factors"
            return PluginResult(
                plugin_name=self.name,
                score_adjustment=adj,
                confidence=profile.get("risk_confidence", 0.5),
                metadata=profile.get("components", {}),
                explanation=explanation,
            )
        except Exception as exc:
            logger.error("AdvancedRiskPlugin error: %s", exc, exc_info=True)
            return PluginResult(plugin_name=self.name, score_adjustment=0.0, confidence=0.0, error=str(exc))


class GraphIntelligencePlugin(ScoringPlugin):
    """Wraps BehavioralGraph wallet intelligence into the plugin system."""

    priority = 30
    weight = 1.2

    @property
    def name(self) -> str:
        return "graph_intelligence"

    @property
    def description(self) -> str:
        return "Graph-based trust score and risk propagation from wallet interaction network"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        try:
            from services.behavioral_graph import get_wallet_graph
            graph = get_wallet_graph()

            if graph.node_count() < 2:
                return PluginResult(
                    plugin_name=self.name,
                    score_adjustment=0.0,
                    confidence=0.0,
                    skipped=True,
                    explanation="Graph has insufficient nodes for analysis",
                )

            intel = graph.wallet_intelligence(address)
            adj = intel["graph_adjustment"]
            warnings = intel.get("graph_warnings", [])
            explanation = "; ".join(warnings) if warnings else "No graph risk signals"

            return PluginResult(
                plugin_name=self.name,
                score_adjustment=adj,
                confidence=0.8,
                metadata=intel,
                explanation=explanation,
            )
        except Exception as exc:
            logger.error("GraphIntelligencePlugin error: %s", exc, exc_info=True)
            return PluginResult(plugin_name=self.name, score_adjustment=0.0, confidence=0.0, error=str(exc))


class ExplainabilityPlugin(ScoringPlugin):
    """Runs explainability engine and stores SHAP values in context."""

    priority = 90
    weight = 0.0  # read-only — does not adjust the score, only enriches context

    @property
    def name(self) -> str:
        return "explainability"

    @property
    def description(self) -> str:
        return "SHAP-based feature attribution and human-readable explanations"

    async def compute(self, address: str, context: Dict[str, Any]) -> PluginResult:
        try:
            from services.explainability_engine import get_explainability_engine
            engine = get_explainability_engine()
            features = context.get("features", {})
            if not features:
                return PluginResult(plugin_name=self.name, score_adjustment=0.0, confidence=0.0, skipped=True)

            explanation = engine.explain_features(features, context.get("base_score", 500.0))
            context["explanation"] = explanation  # Side-effect: enrich context

            return PluginResult(
                plugin_name=self.name,
                score_adjustment=0.0,
                confidence=1.0,
                metadata=explanation,
                explanation=explanation.get("summary", ""),
            )
        except Exception as exc:
            logger.error("ExplainabilityPlugin error: %s", exc, exc_info=True)
            return PluginResult(plugin_name=self.name, score_adjustment=0.0, confidence=0.0, error=str(exc))


# ---------------------------------------------------------------------------
# Plugin registry
# ---------------------------------------------------------------------------

class PluginRegistry:
    """
    Central store of all registered plugins.
    Plugins are registered by class (not instance) and instantiated on demand.
    """

    def __init__(self):
        self._plugins: Dict[str, ScoringPlugin] = {}

    def register(self, plugin: ScoringPlugin) -> None:
        if plugin.name in self._plugins:
            logger.warning("Plugin '%s' already registered — overwriting", plugin.name)
        self._plugins[plugin.name] = plugin
        logger.info("Plugin registered: %s (priority=%d, weight=%.1f)", plugin.name, plugin.priority, plugin.weight)

    def unregister(self, name: str) -> bool:
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False

    def get(self, name: str) -> Optional[ScoringPlugin]:
        return self._plugins.get(name)

    def all_active(self) -> List[ScoringPlugin]:
        return sorted(
            [p for p in self._plugins.values() if p.enabled],
            key=lambda p: p.priority,
        )

    def list_plugins(self) -> List[Dict]:
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "priority": p.priority,
                "weight": p.weight,
                "enabled": p.enabled,
            }
            for p in sorted(self._plugins.values(), key=lambda p: p.priority)
        ]


# ---------------------------------------------------------------------------
# Scoring pipeline
# ---------------------------------------------------------------------------

class ScoringPipeline:
    """
    Executes all active plugins in priority order and merges results into
    a final adjusted score.

    Merge strategy
    --------------
    final_adjustment = Σ (plugin.score_adjustment * plugin.weight * plugin.confidence)
                       ─────────────────────────────────────────────────────────────
                       Σ (plugin.weight * plugin.confidence)   [for non-zero-weight plugins]
    """

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    async def run(
        self,
        address: str,
        base_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full plugin pipeline for a given address.

        Parameters
        ----------
        address    : wallet address
        base_score : score from existing ScoringService (never modified)
        context    : shared state dict (transactions, features, loan_history …)

        Returns
        -------
        Dict with `final_score`, `adjustments`, `plugin_results`, `explanation`
        """
        ctx = context or {}
        ctx["base_score"] = base_score
        ctx["address"] = address

        plugins = self.registry.all_active()
        plugin_results: List[PluginResult] = []

        for plugin in plugins:
            try:
                result = await plugin.compute(address, ctx)
            except Exception as exc:
                logger.error("Pipeline: plugin '%s' raised: %s", plugin.name, exc, exc_info=True)
                result = PluginResult(
                    plugin_name=plugin.name,
                    score_adjustment=0.0,
                    confidence=0.0,
                    error=str(exc),
                )
            plugin_results.append(result)

        # Weighted merge (exclude zero-weight and skipped plugins from score adjustment)
        total_weighted_adj = 0.0
        total_weight = 0.0
        for res, plugin in zip(plugin_results, plugins):
            if res.skipped or res.error or plugin.weight == 0.0:
                continue
            w = plugin.weight * max(0.0, res.confidence)
            total_weighted_adj += res.score_adjustment * w
            total_weight += w

        weighted_adj = total_weighted_adj / total_weight if total_weight > 0 else 0.0
        final_score = max(0.0, min(1000.0, base_score + weighted_adj))

        return {
            "base_score": base_score,
            "final_score": round(final_score, 2),
            "weighted_adjustment": round(weighted_adj, 2),
            "plugin_results": [
                {
                    "plugin": r.plugin_name,
                    "adjustment": r.score_adjustment,
                    "confidence": r.confidence,
                    "explanation": r.explanation,
                    "skipped": r.skipped,
                    "error": r.error,
                }
                for r in plugin_results
            ],
            "explanation": ctx.get("explanation", {}),
            "ran_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# Singletons with default plugin registration
# ---------------------------------------------------------------------------

_registry: Optional[PluginRegistry] = None
_pipeline: Optional[ScoringPipeline] = None


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        # Register built-in plugins
        _registry.register(AdvancedRiskPlugin())
        _registry.register(GraphIntelligencePlugin())
        _registry.register(ExplainabilityPlugin())
        logger.info("PluginRegistry initialised with %d built-in plugins", len(_registry.all_active()))
    return _registry


def get_scoring_pipeline() -> ScoringPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ScoringPipeline(registry=get_plugin_registry())
        logger.info("ScoringPipeline initialised")
    return _pipeline
