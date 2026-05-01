"""
Drift Detection & Model Integrity Monitor — Phase 1 Extension

Tracks:
  - Population Stability Index (PSI) for score distributions
  - Feature distribution drift (KS test + PSI per feature)
  - Anomalous scoring patterns (outlier alerts)

Nothing in this file modifies existing scoring or ML services.
All results are exposed via /monitoring/drift endpoints (see api/advanced_endpoints.py).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PSI calculation
# ---------------------------------------------------------------------------

def compute_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    bins: int = 10,
    epsilon: float = 1e-8,
) -> float:
    """
    Population Stability Index.

    PSI < 0.1  → no significant change
    0.1–0.2    → minor shift (monitor)
    ≥ 0.2      → significant shift (investigate / retrain)
    """
    # Compute bin boundaries from expected distribution
    breakpoints = np.linspace(0, 100, bins + 1)
    expected_percentiles = np.percentile(expected, breakpoints)
    # Ensure monotonically increasing breakpoints (handles constant distributions)
    expected_percentiles = np.unique(expected_percentiles)
    if len(expected_percentiles) < 2:
        return 0.0

    expected_freqs = np.histogram(expected, bins=expected_percentiles)[0] / max(len(expected), 1)
    actual_freqs = np.histogram(actual, bins=expected_percentiles)[0] / max(len(actual), 1)

    # Add epsilon to avoid log(0)
    expected_freqs = np.clip(expected_freqs, epsilon, None)
    actual_freqs = np.clip(actual_freqs, epsilon, None)

    psi = float(np.sum((actual_freqs - expected_freqs) * np.log(actual_freqs / expected_freqs)))
    return round(psi, 5)


# ---------------------------------------------------------------------------
# KS-test wrapper
# ---------------------------------------------------------------------------

def kolmogorov_smirnov_drift(
    reference: np.ndarray,
    current: np.ndarray,
) -> Tuple[float, float]:
    """
    Returns (statistic, p_value).
    p_value < 0.05 indicates statistically significant drift.
    """
    try:
        from scipy.stats import ks_2samp
        stat, pval = ks_2samp(reference, current)
        return round(float(stat), 5), round(float(pval), 5)
    except ImportError:
        # Fallback: compare means normalised by pooled std
        diff = abs(np.mean(current) - np.mean(reference))
        pooled_std = math.sqrt((np.var(reference) + np.var(current)) / 2 + 1e-12)
        stat = diff / pooled_std
        # Approximate p-value via z-test
        pval = max(0.0, 1.0 - math.erf(stat / math.sqrt(2)))
        return round(stat, 5), round(pval, 5)


# ---------------------------------------------------------------------------
# Feature drift record
# ---------------------------------------------------------------------------

@dataclass
class FeatureDriftResult:
    feature_name: str
    psi: float
    ks_statistic: float
    ks_p_value: float
    reference_mean: float
    current_mean: float
    reference_std: float
    current_std: float
    drift_level: str = ""  # "none" | "minor" | "major"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        if self.psi < 0.1:
            self.drift_level = "none"
        elif self.psi < 0.2:
            self.drift_level = "minor"
        else:
            self.drift_level = "major"


# ---------------------------------------------------------------------------
# Alert model
# ---------------------------------------------------------------------------

@dataclass
class DriftAlert:
    alert_type: str        # "psi_major" | "psi_minor" | "feature_drift" | "score_anomaly"
    severity: str          # "warning" | "critical"
    message: str
    details: Dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False


# ---------------------------------------------------------------------------
# Main drift detector
# ---------------------------------------------------------------------------

class DriftDetector:
    """
    Monitors model health by comparing reference (training) distributions
    against recent live distributions.

    Usage
    -----
    detector = DriftDetector()
    detector.set_reference_scores(baseline_scores)
    detector.set_reference_features("balance", baseline_balances)

    # Called periodically (e.g. hourly cron):
    report = detector.run_full_check(live_scores, live_feature_map)
    """

    PSI_WARN_THRESHOLD = 0.10
    PSI_CRIT_THRESHOLD = 0.20
    SCORE_ANOMALY_Z_THRESHOLD = 3.0  # z-score above which individual score is anomalous

    def __init__(self):
        self._ref_scores: Optional[np.ndarray] = None
        self._ref_features: Dict[str, np.ndarray] = {}
        self._alert_history: List[DriftAlert] = []
        self._alert_callbacks: List[Callable[[DriftAlert], None]] = []
        self._check_history: List[Dict] = []

    # ------------------------------------------------------------------
    # Reference data management
    # ------------------------------------------------------------------

    def set_reference_scores(self, scores: List[float]) -> None:
        """Set the baseline score distribution (typically from training set)."""
        self._ref_scores = np.array(scores, dtype=float)
        logger.info("Reference score distribution set: n=%d, mean=%.2f", len(scores), float(np.mean(scores)))

    def set_reference_feature(self, feature_name: str, values: List[float]) -> None:
        """Set baseline for a specific feature."""
        self._ref_features[feature_name] = np.array(values, dtype=float)
        logger.info("Reference feature '%s' set: n=%d", feature_name, len(values))

    def set_reference_features(self, feature_map: Dict[str, List[float]]) -> None:
        for name, vals in feature_map.items():
            self.set_reference_feature(name, vals)

    # ------------------------------------------------------------------
    # Alert callbacks
    # ------------------------------------------------------------------

    def register_alert_callback(self, fn: Callable[[DriftAlert], None]) -> None:
        """Register a function to call whenever a drift alert is raised."""
        self._alert_callbacks.append(fn)

    def _emit_alert(self, alert: DriftAlert) -> None:
        self._alert_history.append(alert)
        for fn in self._alert_callbacks:
            try:
                fn(alert)
            except Exception as exc:
                logger.warning("Alert callback error: %s", exc)
        logger.warning("DRIFT ALERT [%s] %s: %s", alert.severity.upper(), alert.alert_type, alert.message)

    # ------------------------------------------------------------------
    # Score distribution check
    # ------------------------------------------------------------------

    def check_score_distribution(self, current_scores: List[float]) -> Dict:
        if self._ref_scores is None or len(current_scores) == 0:
            return {"status": "skipped", "reason": "no reference data or empty current scores"}

        curr = np.array(current_scores, dtype=float)
        psi = compute_psi(self._ref_scores, curr)
        ks_stat, ks_pval = kolmogorov_smirnov_drift(self._ref_scores, curr)

        result = {
            "psi": psi,
            "ks_statistic": ks_stat,
            "ks_p_value": ks_pval,
            "reference_mean": round(float(np.mean(self._ref_scores)), 2),
            "current_mean": round(float(np.mean(curr)), 2),
            "reference_std": round(float(np.std(self._ref_scores)), 2),
            "current_std": round(float(np.std(curr)), 2),
            "drift_level": "none",
        }

        if psi >= self.PSI_CRIT_THRESHOLD:
            result["drift_level"] = "major"
            self._emit_alert(DriftAlert(
                alert_type="psi_major",
                severity="critical",
                message=f"Major score distribution shift detected: PSI={psi:.3f}",
                details=result,
            ))
        elif psi >= self.PSI_WARN_THRESHOLD:
            result["drift_level"] = "minor"
            self._emit_alert(DriftAlert(
                alert_type="psi_minor",
                severity="warning",
                message=f"Minor score distribution shift: PSI={psi:.3f}",
                details=result,
            ))

        return result

    # ------------------------------------------------------------------
    # Feature drift check
    # ------------------------------------------------------------------

    def check_feature_drift(self, current_feature_map: Dict[str, List[float]]) -> List[FeatureDriftResult]:
        results = []
        for name, curr_vals in current_feature_map.items():
            ref = self._ref_features.get(name)
            if ref is None or len(curr_vals) == 0:
                continue

            curr = np.array(curr_vals, dtype=float)
            psi = compute_psi(ref, curr)
            ks_stat, ks_pval = kolmogorov_smirnov_drift(ref, curr)

            dr = FeatureDriftResult(
                feature_name=name,
                psi=psi,
                ks_statistic=ks_stat,
                ks_p_value=ks_pval,
                reference_mean=round(float(np.mean(ref)), 4),
                current_mean=round(float(np.mean(curr)), 4),
                reference_std=round(float(np.std(ref)), 4),
                current_std=round(float(np.std(curr)), 4),
            )
            results.append(dr)

            if dr.drift_level == "major":
                self._emit_alert(DriftAlert(
                    alert_type="feature_drift",
                    severity="critical",
                    message=f"Feature '{name}' has major drift: PSI={psi:.3f}",
                    details={"feature": name, "psi": psi, "ks_p_value": ks_pval},
                ))
            elif dr.drift_level == "minor" and ks_pval < 0.05:
                self._emit_alert(DriftAlert(
                    alert_type="feature_drift",
                    severity="warning",
                    message=f"Feature '{name}' shows statistically significant drift",
                    details={"feature": name, "psi": psi, "ks_p_value": ks_pval},
                ))

        return results

    # ------------------------------------------------------------------
    # Anomaly detection
    # ------------------------------------------------------------------

    def detect_score_anomalies(self, scored_wallets: Dict[str, float]) -> List[Dict]:
        """Flag individual scores that are anomalously far from the reference mean."""
        if self._ref_scores is None or len(scored_wallets) == 0:
            return []

        ref_mean = float(np.mean(self._ref_scores))
        ref_std = float(np.std(self._ref_scores)) or 1.0

        anomalies = []
        for address, score in scored_wallets.items():
            z = abs(score - ref_mean) / ref_std
            if z > self.SCORE_ANOMALY_Z_THRESHOLD:
                anomalies.append({
                    "address": address,
                    "score": score,
                    "z_score": round(z, 2),
                    "direction": "high" if score > ref_mean else "low",
                })

        if anomalies:
            self._emit_alert(DriftAlert(
                alert_type="score_anomaly",
                severity="warning",
                message=f"{len(anomalies)} score anomalies detected",
                details={"count": len(anomalies), "examples": anomalies[:5]},
            ))

        return anomalies

    # ------------------------------------------------------------------
    # Full health check
    # ------------------------------------------------------------------

    def run_full_check(
        self,
        current_scores: List[float],
        current_feature_map: Optional[Dict[str, List[float]]] = None,
        scored_wallets: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        Run all drift checks and return a combined health report.
        Designed to be called from a periodic monitoring task or endpoint.
        """
        report: Dict = {
            "checked_at": datetime.utcnow().isoformat(),
            "score_distribution": {},
            "feature_drift": [],
            "anomalies": [],
            "active_alerts": [],
            "overall_health": "healthy",
        }

        report["score_distribution"] = self.check_score_distribution(current_scores)

        if current_feature_map:
            drifts = self.check_feature_drift(current_feature_map)
            report["feature_drift"] = [
                {
                    "feature": d.feature_name,
                    "psi": d.psi,
                    "ks_stat": d.ks_statistic,
                    "ks_p_value": d.ks_p_value,
                    "drift_level": d.drift_level,
                    "mean_shift": round(d.current_mean - d.reference_mean, 4),
                }
                for d in drifts
            ]

        if scored_wallets:
            report["anomalies"] = self.detect_score_anomalies(scored_wallets)

        recent_alerts = [
            a for a in self._alert_history
            if not a.resolved
        ][-20:]
        report["active_alerts"] = [
            {"type": a.alert_type, "severity": a.severity, "message": a.message, "ts": a.timestamp}
            for a in recent_alerts
        ]

        # Overall health
        critical_alerts = [a for a in recent_alerts if a.severity == "critical"]
        warn_alerts = [a for a in recent_alerts if a.severity == "warning"]
        if critical_alerts:
            report["overall_health"] = "critical"
        elif warn_alerts:
            report["overall_health"] = "degraded"

        self._check_history.append({
            "ts": report["checked_at"],
            "health": report["overall_health"],
            "score_psi": report["score_distribution"].get("psi", 0),
        })
        # Keep only last 100 checks
        self._check_history = self._check_history[-100:]

        logger.info(
            "Drift check complete: health=%s, alerts=%d critical / %d warning",
            report["overall_health"], len(critical_alerts), len(warn_alerts),
        )
        return report

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        return [
            {"type": a.alert_type, "severity": a.severity,
             "message": a.message, "ts": a.timestamp, "resolved": a.resolved}
            for a in self._alert_history[-limit:]
        ]

    def get_health_history(self, limit: int = 50) -> List[Dict]:
        return self._check_history[-limit:]

    def resolve_alert(self, index: int) -> bool:
        if 0 <= index < len(self._alert_history):
            self._alert_history[index].resolved = True
            return True
        return False


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_detector_instance: Optional[DriftDetector] = None


def get_drift_detector() -> DriftDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = DriftDetector()
        logger.info("DriftDetector singleton initialised")
    return _detector_instance
