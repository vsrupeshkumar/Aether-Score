"""
Explainability Engine — Phase 1 Extension

Provides:
  - SHAP-based feature attribution (wraps existing MLModel)
  - Rule-based feature contribution analysis for wallets without ML model
  - Human-readable score breakdowns
  - Score component narratives

Existing score_explanation.py and score_breakdown.py are NOT modified.
This module offers a richer, unified interface.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature contribution record
# ---------------------------------------------------------------------------

@dataclass
class FeatureContribution:
    name: str
    value: float            # actual feature value
    contribution: float     # SHAP or rule-based delta to final score
    direction: str          # "positive" | "negative" | "neutral"
    percentile: float       # 0–100 percentile vs population
    human_label: str = ""   # human-readable name, e.g. "Account Age"
    impact_level: str = ""  # "high" | "medium" | "low"

    def __post_init__(self):
        if not self.direction:
            self.direction = "positive" if self.contribution > 0 else ("negative" if self.contribution < 0 else "neutral")
        if not self.impact_level:
            abs_c = abs(self.contribution)
            self.impact_level = "high" if abs_c > 50 else ("medium" if abs_c > 15 else "low")


# ---------------------------------------------------------------------------
# Human-readable label map
# ---------------------------------------------------------------------------

FEATURE_LABELS: Dict[str, str] = {
    "balance": "Current Balance",
    "tx_count": "Transaction Count",
    "age_days": "Account Age (days)",
    "avg_tx_value": "Average Transaction Value",
    "loan_count": "Historical Loan Count",
    "repayment_ratio": "Loan Repayment Ratio",
    "defi_activity": "DeFi Protocol Usage",
    "staking_amount": "Amount Staked",
    "nft_holdings": "NFT Holdings",
    "cross_chain_activity": "Cross-Chain Activity",
    "last_activity_days": "Days Since Last Activity",
    "unique_counterparties": "Unique Counterparties",
    "inflow_outflow_ratio": "Inflow/Outflow Ratio",
    "contract_interactions": "Smart Contract Interactions",
    "governance_votes": "Governance Participation",
    "liquidations": "Past Liquidations",
    "collateral_ratio": "Collateral Ratio",
}


def _human_label(name: str) -> str:
    return FEATURE_LABELS.get(name, name.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Narrative templates
# ---------------------------------------------------------------------------

NARRATIVE_TEMPLATES = {
    "high_positive": "Your {label} is in the top {pct:.0f}% of users, contributing +{contrib:.0f} points.",
    "high_negative": "Your {label} is below average, reducing your score by {contrib:.0f} points.",
    "medium_positive": "{label} provides a moderate boost of +{contrib:.0f} points.",
    "medium_negative": "{label} is a moderate risk factor, costing {contrib:.0f} points.",
    "low_any": "{label} has a minor effect on your score ({contrib:+.0f} points).",
    "neutral": "{label} is neutral — no score impact.",
    "liquidation": "You have {value:.0f} past liquidation(s), which significantly lowers your score.",
    "inactive": "Your wallet has been inactive for {value:.0f} days. Recent activity boosts your score.",
    "high_repayment": "Your {value:.0%} loan repayment rate demonstrates excellent creditworthiness.",
}


def _narrative(contrib: FeatureContribution) -> str:
    a = abs(contrib.contribution)
    p = contrib.percentile
    v = contrib.value
    lbl = contrib.human_label

    # Special-case narratives
    if contrib.name == "liquidations" and v > 0:
        return NARRATIVE_TEMPLATES["liquidation"].format(value=v)
    if contrib.name == "last_activity_days" and v > 90:
        return NARRATIVE_TEMPLATES["inactive"].format(value=v)
    if contrib.name == "repayment_ratio" and v > 0.9:
        return NARRATIVE_TEMPLATES["high_repayment"].format(value=v)

    if a < 1:
        return NARRATIVE_TEMPLATES["neutral"].format(label=lbl)
    if a < 15:
        return NARRATIVE_TEMPLATES["low_any"].format(label=lbl, contrib=contrib.contribution)

    if contrib.direction == "positive":
        if p > 70:
            return NARRATIVE_TEMPLATES["high_positive"].format(label=lbl, pct=100 - p, contrib=a)
        return NARRATIVE_TEMPLATES["medium_positive"].format(label=lbl, contrib=a)
    else:
        if p < 30:
            return NARRATIVE_TEMPLATES["high_negative"].format(label=lbl, contrib=a)
        return NARRATIVE_TEMPLATES["medium_negative"].format(label=lbl, contrib=a)


# ---------------------------------------------------------------------------
# SHAP wrapper
# ---------------------------------------------------------------------------

class SHAPExplainer:
    """
    Thin wrapper around SHAP TreeExplainer for the XGBoost model.
    Gracefully degrades if SHAP is unavailable or model not loaded.
    """

    def __init__(self):
        self._explainer = None
        self._model = None

    def _load(self) -> bool:
        if self._explainer is not None:
            return True
        try:
            import shap
            from models.ml_model import MLModel
            ml = MLModel()
            if not ml.load_model():
                return False
            self._model = ml
            self._explainer = shap.TreeExplainer(ml.model)
            return True
        except Exception as exc:
            logger.debug("SHAP explainer unavailable: %s", exc)
            return False

    def shap_values(self, feature_vector: np.ndarray) -> Optional[np.ndarray]:
        if not self._load():
            return None
        try:
            values = self._explainer.shap_values(feature_vector.reshape(1, -1))
            return np.array(values).flatten()
        except Exception as exc:
            logger.warning("SHAP computation failed: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Rule-based fallback attribution
# ---------------------------------------------------------------------------

# Approximate weight each feature contributes to score in rule-based system
RULE_WEIGHTS: Dict[str, float] = {
    "balance": 0.15,
    "tx_count": 0.10,
    "age_days": 0.12,
    "avg_tx_value": 0.08,
    "loan_count": 0.06,
    "repayment_ratio": 0.18,
    "defi_activity": 0.07,
    "staking_amount": 0.08,
    "liquidations": -0.15,    # negative weight = higher value → lower score
    "last_activity_days": -0.08,
    "unique_counterparties": 0.05,
    "inflow_outflow_ratio": 0.06,
}


def rule_based_contributions(features: Dict[str, float], base_score: float) -> List[FeatureContribution]:
    """
    Fast approximation when SHAP model is unavailable.
    Maps feature values to score contributions using fixed rule weights.
    """
    contribs = []
    total_weight = sum(abs(w) for w in RULE_WEIGHTS.values())

    for name, weight in RULE_WEIGHTS.items():
        raw_val = float(features.get(name, 0))

        # Normalise value to 0–1 range using soft sigmoid
        norm = 1.0 / (1.0 + math.exp(-raw_val / max(abs(raw_val) + 1, 1)))

        # Contribution = weight * score_scale * normalised_value
        score_scale = base_score / 500.0  # higher base = larger absolute contribution
        contribution = weight * 200.0 * score_scale * (norm - 0.5)

        # Mock percentile based on normalised value (without population data)
        percentile = norm * 100.0

        contribs.append(FeatureContribution(
            name=name,
            value=raw_val,
            contribution=round(contribution, 2),
            direction="positive" if contribution > 0 else ("negative" if contribution < 0 else "neutral"),
            percentile=round(percentile, 1),
            human_label=_human_label(name),
        ))

    # Sort by absolute contribution descending
    contribs.sort(key=lambda c: abs(c.contribution), reverse=True)
    return contribs


# ---------------------------------------------------------------------------
# Main explainability engine
# ---------------------------------------------------------------------------

class ExplainabilityEngine:
    """
    Unified explainability interface.

    Usage
    -----
    engine = ExplainabilityEngine()
    result = engine.explain_features(features_dict, base_score=650)
    # result["contributions"], result["summary"], result["narratives"]
    """

    def __init__(self):
        self._shap = SHAPExplainer()

    def explain_features(
        self,
        features: Dict[str, float],
        base_score: float,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute feature contributions and generate human-readable explanation.

        Tries SHAP first; falls back to rule-based attribution.
        """
        # Try SHAP
        contribs = self._try_shap(features, base_score, feature_names)

        # Fall back to rule-based
        if contribs is None:
            contribs = rule_based_contributions(features, base_score)
            method = "rule_based"
        else:
            method = "shap"

        # Generate narratives
        narratives = [_narrative(c) for c in contribs if c.impact_level != "low"]

        # Top positive and negative factors
        positives = sorted([c for c in contribs if c.contribution > 0], key=lambda c: c.contribution, reverse=True)
        negatives = sorted([c for c in contribs if c.contribution < 0], key=lambda c: c.contribution)

        # One-line summary
        pos_str = ", ".join(c.human_label for c in positives[:2]) if positives else "none"
        neg_str = ", ".join(c.human_label for c in negatives[:2]) if negatives else "none"

        if negatives:
            summary = (
                f"Score boosted by {pos_str}. "
                f"Reduced due to {neg_str}."
            )
        else:
            summary = f"Score positively driven by {pos_str}."

        return {
            "method": method,
            "base_score": base_score,
            "contributions": [
                {
                    "feature": c.name,
                    "label": c.human_label,
                    "value": c.value,
                    "contribution": c.contribution,
                    "direction": c.direction,
                    "impact_level": c.impact_level,
                    "percentile": c.percentile,
                }
                for c in contribs
            ],
            "top_positive_factors": [c.human_label for c in positives[:3]],
            "top_negative_factors": [c.human_label for c in negatives[:3]],
            "narratives": narratives,
            "summary": summary,
        }

    def _try_shap(
        self,
        features: Dict[str, float],
        base_score: float,
        feature_names: Optional[List[str]] = None,
    ) -> Optional[List[FeatureContribution]]:
        names = feature_names or list(features.keys())
        vec = np.array([features.get(n, 0.0) for n in names], dtype=float)
        shap_vals = self._shap.shap_values(vec)

        if shap_vals is None:
            return None

        contribs = []
        for i, name in enumerate(names):
            sv = float(shap_vals[i]) if i < len(shap_vals) else 0.0
            raw = float(features.get(name, 0.0))
            contribs.append(FeatureContribution(
                name=name,
                value=raw,
                contribution=round(sv * 1000, 2),  # scale SHAP output to score range
                direction="positive" if sv > 0 else ("negative" if sv < 0 else "neutral"),
                percentile=50.0,  # SHAP doesn't provide percentile; use rule-based for that
                human_label=_human_label(name),
            ))

        contribs.sort(key=lambda c: abs(c.contribution), reverse=True)
        return contribs

    def score_breakdown(self, score_components: Dict[str, float]) -> Dict:
        """
        Generate a visual-friendly breakdown of score components.
        score_components: dict of component → value, e.g. {"base": 600, "staking_boost": 50, ...}
        """
        total = sum(score_components.values())
        breakdown = []
        for component, value in score_components.items():
            breakdown.append({
                "component": component,
                "label": _human_label(component),
                "value": round(value, 2),
                "percentage": round(abs(value) / max(abs(total), 1) * 100, 1),
                "direction": "positive" if value >= 0 else "negative",
            })
        breakdown.sort(key=lambda x: abs(x["value"]), reverse=True)
        return {
            "components": breakdown,
            "total_score": round(total, 2),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[ExplainabilityEngine] = None


def get_explainability_engine() -> ExplainabilityEngine:
    global _engine
    if _engine is None:
        _engine = ExplainabilityEngine()
        logger.info("ExplainabilityEngine initialised")
    return _engine
