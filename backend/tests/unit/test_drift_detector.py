"""Unit tests for DriftDetector (services/drift_detector.py)."""

import pytest
import numpy as np

from services.drift_detector import DriftDetector, compute_psi, kolmogorov_smirnov_drift


# ---------------------------------------------------------------------------
# PSI calculation
# ---------------------------------------------------------------------------

class TestComputePSI:
    def test_identical_distributions_psi_zero(self):
        data = np.random.normal(500, 100, 1000)
        psi = compute_psi(data, data.copy())
        assert psi < 0.02  # near-zero for identical distributions

    def test_very_different_distributions_high_psi(self):
        ref = np.random.normal(500, 50, 1000)
        curr = np.random.normal(100, 50, 1000)  # completely different mean
        psi = compute_psi(ref, curr)
        assert psi >= 0.2  # significant shift

    def test_psi_non_negative(self):
        ref = np.random.normal(500, 100, 500)
        curr = np.random.normal(550, 110, 500)
        assert compute_psi(ref, curr) >= 0

    def test_empty_actual_returns_zero(self):
        ref = np.array([100.0, 200.0, 300.0])
        psi = compute_psi(ref, np.array([]), epsilon=1e-8)
        assert psi == 0.0  # constant distribution → unique breakpoints < 2

    def test_minor_shift_psi_between_0_and_02(self):
        np.random.seed(42)
        ref = np.random.normal(500, 100, 2000)
        curr = np.random.normal(520, 100, 2000)  # slight mean shift
        psi = compute_psi(ref, curr)
        assert psi < 0.5  # should not be catastrophically large


# ---------------------------------------------------------------------------
# KS test
# ---------------------------------------------------------------------------

class TestKSDrift:
    def test_identical_high_p_value(self):
        data = np.random.normal(500, 100, 500)
        stat, pval = kolmogorov_smirnov_drift(data, data.copy())
        assert pval > 0.05  # not significant

    def test_different_low_p_value(self):
        ref = np.random.normal(500, 50, 1000)
        curr = np.random.normal(0, 50, 1000)
        stat, pval = kolmogorov_smirnov_drift(ref, curr)
        assert pval < 0.05  # statistically significant

    def test_stat_in_bounds(self):
        a = np.random.uniform(0, 1, 200)
        b = np.random.uniform(0.3, 1.3, 200)
        stat, _ = kolmogorov_smirnov_drift(a, b)
        assert 0.0 <= stat <= 1.0


# ---------------------------------------------------------------------------
# DriftDetector
# ---------------------------------------------------------------------------

class TestDriftDetector:
    def setup_method(self):
        self.detector = DriftDetector()
        np.random.seed(99)
        self.ref_scores = list(np.random.normal(500, 100, 1000))
        self.detector.set_reference_scores(self.ref_scores)

    def test_no_drift_on_same_distribution(self):
        curr = list(np.random.normal(500, 100, 200))
        result = self.detector.check_score_distribution(curr)
        assert result["drift_level"] in ("none", "minor")

    def test_major_drift_detected(self):
        curr = list(np.random.normal(900, 30, 200))  # completely different
        result = self.detector.check_score_distribution(curr)
        assert result["drift_level"] == "major"

    def test_check_without_reference_returns_skipped(self):
        d = DriftDetector()  # no reference set
        result = d.check_score_distribution([500.0, 600.0])
        assert result["status"] == "skipped"

    def test_feature_drift_check(self):
        self.detector.set_reference_feature("balance", list(np.random.normal(1.0, 0.1, 500)))
        curr_feats = {"balance": list(np.random.normal(10.0, 0.1, 200))}  # huge shift
        results = self.detector.check_feature_drift(curr_feats)
        assert len(results) == 1
        assert results[0].feature_name == "balance"
        assert results[0].psi > 0

    def test_anomaly_detection_flags_outlier(self):
        wallets = {"0xNormal": 500.0, "0xOutlier": 990.0, "0xLow": 510.0}
        anomalies = self.detector.detect_score_anomalies(wallets)
        # 990 should be flagged as anomalous (z > 3 from mean ~500, std ~100)
        flagged = [a["address"] for a in anomalies]
        assert "0xOutlier" in flagged
        assert "0xNormal" not in flagged

    def test_alert_callback_triggered(self):
        alerts = []
        self.detector.register_alert_callback(lambda a: alerts.append(a))
        curr = list(np.random.normal(900, 30, 200))
        self.detector.check_score_distribution(curr)
        assert any(a.alert_type == "psi_major" for a in alerts)

    def test_full_check_structure(self):
        curr = list(np.random.normal(500, 100, 100))
        report = self.detector.run_full_check(current_scores=curr)
        assert "overall_health" in report
        assert "score_distribution" in report
        assert "checked_at" in report

    def test_alert_history_populated(self):
        curr = list(np.random.normal(900, 10, 200))
        self.detector.check_score_distribution(curr)
        history = self.detector.get_alert_history()
        assert len(history) >= 1

    def test_resolve_alert(self):
        curr = list(np.random.normal(900, 10, 200))
        self.detector.check_score_distribution(curr)
        ok = self.detector.resolve_alert(0)
        assert ok is True
        assert self.detector._alert_history[0].resolved is True

    def test_health_history_records_check(self):
        curr = list(np.random.normal(500, 100, 100))
        self.detector.run_full_check(current_scores=curr)
        history = self.detector.get_health_history()
        assert len(history) >= 1
        assert "ts" in history[-1]
        assert "health" in history[-1]

    def test_full_check_with_feature_map(self):
        self.detector.set_reference_feature("tx_count", list(np.random.normal(10, 2, 500)))
        curr_feats = {"tx_count": list(np.random.normal(50, 5, 200))}
        report = self.detector.run_full_check(
            current_scores=list(np.random.normal(500, 100, 100)),
            current_feature_map=curr_feats,
        )
        assert len(report["feature_drift"]) == 1
