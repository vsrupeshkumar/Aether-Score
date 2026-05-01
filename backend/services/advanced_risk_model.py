"""
Advanced Risk Modeling Layer — Phase 1 Extension

Extends existing ScoringService with:
  - Bayesian updating of default probability (Beta-Binomial conjugate model)
  - Temporal decay weighting (exponential half-life)
  - Volatility-aware penalties (CV + max-drawdown)

All methods are purely additive; nothing in this file modifies ScoringService.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bayesian prior / posterior
# ---------------------------------------------------------------------------

@dataclass
class BayesianPrior:
    """
    Beta-distribution conjugate prior for P(default).

    alpha — pseudo-count of successful repayments  (starts at 1 = weakly optimistic)
    beta  — pseudo-count of defaults               (starts at 1 = uniform prior)
    """
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def mean(self) -> float:
        """Posterior mean of default probability."""
        return self.beta / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        s = self.alpha + self.beta
        return (self.alpha * self.beta) / (s * s * (s + 1))

    def update(self, repaid: int, defaulted: int) -> "BayesianPrior":
        """Conjugate Bayesian update — returns new prior."""
        return BayesianPrior(
            alpha=self.alpha + repaid,
            beta=self.beta + defaulted,
        )

    def credible_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """Exact Beta credible interval via incomplete beta function."""
        try:
            from scipy.stats import beta as beta_dist
            return beta_dist.interval(confidence, self.alpha, self.beta)
        except ImportError:
            # Fallback: mean ± 2*std
            std = math.sqrt(self.variance)
            return (max(0.0, self.mean - 2 * std), min(1.0, self.mean + 2 * std))

    @property
    def confidence_mass(self) -> float:
        """
        0–1 score indicating how much data backs this prior.
        Saturates at 20 observed loans.
        """
        return min(1.0, (self.alpha + self.beta - 2) / 20.0)


# ---------------------------------------------------------------------------
# Temporal decay
# ---------------------------------------------------------------------------

@dataclass
class TemporalWindow:
    """
    Exponential decay: w(age) = exp(-ln2 / half_life * age_days)

    A transaction that is `half_life_days` old contributes half as much
    as a transaction that happened today.
    """
    half_life_days: float = 90.0

    def decay_weight(self, age_days: float) -> float:
        lam = math.log(2) / max(self.half_life_days, 1e-9)
        return math.exp(-lam * max(age_days, 0))

    def weighted_mean(
        self,
        values: List[float],
        timestamps: List[datetime],
        now: Optional[datetime] = None,
    ) -> float:
        if not values:
            return 0.0
        if now is None:
            now = datetime.utcnow()
        weights = [self.decay_weight((now - ts).total_seconds() / 86400) for ts in timestamps]
        total = sum(weights)
        if total < 1e-12:
            return float(np.mean(values))
        return sum(v * w for v, w in zip(values, weights)) / total

    def effective_count(
        self,
        timestamps: List[datetime],
        now: Optional[datetime] = None,
    ) -> float:
        """Sum of decay weights — a measure of 'recency-adjusted activity'."""
        if now is None:
            now = datetime.utcnow()
        return sum(self.decay_weight((now - ts).total_seconds() / 86400) for ts in timestamps)


# ---------------------------------------------------------------------------
# Volatility scorer
# ---------------------------------------------------------------------------

@dataclass
class VolatilityScorer:
    """
    Penalty = scale * (0.6 * normalised_CV  +  0.4 * normalised_drawdown)

    Coefficient of Variation (CV) = std / |mean|  measures transaction scatter.
    Max drawdown measures peak-to-trough decline in balance history.
    """
    penalty_scale: float = 80.0

    # CV >= this triggers maximum CV penalty
    cv_cap: float = 2.5

    # Drawdown >= this triggers maximum drawdown penalty
    drawdown_cap: float = 0.60

    def _cv(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = float(np.mean(values))
        if abs(mean) < 1e-12:
            return 0.0
        return float(np.std(values)) / abs(mean)

    def _max_drawdown(self, balances: List[float]) -> float:
        if len(balances) < 2:
            return 0.0
        peak = balances[0]
        max_dd = 0.0
        for b in balances[1:]:
            if b > peak:
                peak = b
            elif peak > 1e-12:
                max_dd = max(max_dd, (peak - b) / peak)
        return max_dd

    def penalty(
        self,
        tx_values: List[float],
        balance_history: Optional[List[float]] = None,
    ) -> Dict:
        cv = self._cv(tx_values)
        dd = self._max_drawdown(balance_history or [])

        cv_norm = min(1.0, cv / self.cv_cap)
        dd_norm = min(1.0, dd / self.drawdown_cap)

        total_penalty = self.penalty_scale * (0.6 * cv_norm + 0.4 * dd_norm)

        return {
            "penalty": round(total_penalty, 2),
            "coefficient_of_variation": round(cv, 4),
            "max_drawdown": round(dd, 4),
            "cv_normalised": round(cv_norm, 4),
            "drawdown_normalised": round(dd_norm, 4),
        }


# ---------------------------------------------------------------------------
# Main advanced risk model
# ---------------------------------------------------------------------------

class AdvancedRiskModel:
    """
    Plugs on top of the existing ScoringService.

    Usage
    -----
    arm = AdvancedRiskModel()

    # After ScoringService.compute_score() returns base_score:
    profile = await arm.compute_full_risk_profile(
        address   = address,
        base_score = result["score"],
        transactions = raw_txs,
        loan_history  = past_loans,
        balance_history = balance_series,
    )
    """

    def __init__(
        self,
        temporal_window: Optional[TemporalWindow] = None,
        volatility_scorer: Optional[VolatilityScorer] = None,
    ):
        self.temporal = temporal_window or TemporalWindow()
        self.volatility = volatility_scorer or VolatilityScorer()
        # In-memory prior store; production should persist to Redis/DB
        self._priors: Dict[str, BayesianPrior] = {}

    # ------------------------------------------------------------------
    # Prior management
    # ------------------------------------------------------------------

    def get_prior(self, address: str) -> BayesianPrior:
        return self._priors.setdefault(address, BayesianPrior())

    def update_prior(self, address: str, repaid: int, defaulted: int) -> BayesianPrior:
        updated = self.get_prior(address).update(repaid, defaulted)
        self._priors[address] = updated
        logger.debug("Bayesian prior updated", extra={"address": address, "alpha": updated.alpha, "beta": updated.beta})
        return updated

    def load_prior(self, address: str, alpha: float, beta: float) -> None:
        """Restore a previously persisted prior (e.g. from Redis)."""
        self._priors[address] = BayesianPrior(alpha=alpha, beta=beta)

    # ------------------------------------------------------------------
    # Bayesian component
    # ------------------------------------------------------------------

    def bayesian_adjustment(
        self,
        address: str,
        base_score: float,
        loan_history: Optional[List[Dict]] = None,
    ) -> Dict:
        prior = self.get_prior(address)

        if loan_history:
            repaid = sum(1 for l in loan_history if l.get("status") == "repaid")
            defaulted = sum(1 for l in loan_history if l.get("status") in ("defaulted", "liquidated"))
            prior = self.update_prior(address, repaid, defaulted)

        p_default = prior.mean
        ci_lo, ci_hi = prior.credible_interval(0.95)
        uncertainty = ci_hi - ci_lo

        # High default probability reduces score (max -200), high uncertainty adds a small penalty
        score_adj = -(p_default * 200.0) - (uncertainty * 30.0)

        return {
            "score_adjustment": round(score_adj, 2),
            "posterior_default_probability": round(p_default, 4),
            "credible_interval_95": {"lower": round(ci_lo, 4), "upper": round(ci_hi, 4)},
            "uncertainty": round(uncertainty, 4),
            "data_confidence": round(prior.confidence_mass, 4),
        }

    # ------------------------------------------------------------------
    # Temporal component
    # ------------------------------------------------------------------

    def temporal_analysis(self, transactions: List[Dict]) -> Dict:
        if not transactions:
            return {
                "temporal_adjusted": False,
                "effective_count": 0,
                "weighted_avg_value": 0.0,
                "recency_factor": 0.0,
                "avg_age_days": 0,
            }

        now = datetime.utcnow()
        timestamps: List[datetime] = []
        values: List[float] = []

        for tx in transactions:
            raw_ts = tx.get("timestamp") or tx.get("block_timestamp")
            if raw_ts is None:
                continue
            if isinstance(raw_ts, (int, float)):
                ts = datetime.utcfromtimestamp(float(raw_ts))
            elif isinstance(raw_ts, str):
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", ""))
                except ValueError:
                    ts = now
            elif isinstance(raw_ts, datetime):
                ts = raw_ts
            else:
                ts = now

            timestamps.append(ts)
            values.append(float(tx.get("value") or tx.get("amount") or 0))

        if not timestamps:
            return {"temporal_adjusted": False, "effective_count": 0}

        ages = [(now - ts).total_seconds() / 86400 for ts in timestamps]
        avg_age = float(np.mean(ages))

        return {
            "temporal_adjusted": True,
            "effective_count": round(self.temporal.effective_count(timestamps, now), 2),
            "weighted_avg_value": round(self.temporal.weighted_mean(values, timestamps, now), 4),
            "recency_factor": round(self.temporal.decay_weight(avg_age), 4),
            "avg_age_days": round(avg_age, 1),
            "most_recent_days_ago": round(min(ages), 1) if ages else 0,
            "total_transactions": len(timestamps),
        }

    # ------------------------------------------------------------------
    # Full profile
    # ------------------------------------------------------------------

    def compute_full_risk_profile(
        self,
        address: str,
        base_score: float,
        transactions: Optional[List[Dict]] = None,
        loan_history: Optional[List[Dict]] = None,
        balance_history: Optional[List[float]] = None,
    ) -> Dict:
        """
        Compute the complete advanced risk profile.

        Returns a dict that ADDS to the existing score result — it does NOT
        replace it.  Callers may merge this with the base ScoringService result.
        """
        txs = transactions or []
        balances = balance_history or []
        tx_values = [float(t.get("value") or t.get("amount") or 0) for t in txs]

        bayes = self.bayesian_adjustment(address, base_score, loan_history)
        temporal = self.temporal_analysis(txs)
        vol = self.volatility.penalty(tx_values, balances)

        total_adj = bayes["score_adjustment"] - vol["penalty"]
        advanced_score = max(0.0, min(1000.0, base_score + total_adj))

        risk_factors: List[str] = []
        if vol["coefficient_of_variation"] > 1.0:
            risk_factors.append(
                f"High transaction volatility (CV={vol['coefficient_of_variation']:.2f})"
            )
        if vol["max_drawdown"] > 0.3:
            risk_factors.append(
                f"Significant balance drawdown ({vol['max_drawdown'] * 100:.1f}%)"
            )
        if bayes["posterior_default_probability"] > 0.3:
            risk_factors.append(
                f"Elevated default probability ({bayes['posterior_default_probability'] * 100:.1f}%)"
            )
        if temporal.get("avg_age_days", 0) > 180:
            risk_factors.append("Low recent on-chain activity")

        return {
            "base_score": base_score,
            "advanced_score": round(advanced_score, 2),
            "total_adjustment": round(total_adj, 2),
            "risk_factors": risk_factors,
            "risk_confidence": bayes["data_confidence"],
            "components": {
                "bayesian": bayes,
                "temporal": temporal,
                "volatility": vol,
            },
        }
