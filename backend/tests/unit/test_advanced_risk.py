"""Unit tests for AdvancedRiskModel (services/advanced_risk_model.py)."""

from datetime import datetime, timedelta

import pytest

from services.advanced_risk_model import (
    AdvancedRiskModel,
    BayesianPrior,
    TemporalWindow,
    VolatilityScorer,
)


# ---------------------------------------------------------------------------
# BayesianPrior
# ---------------------------------------------------------------------------

class TestBayesianPrior:
    def test_default_uninformed_prior(self):
        prior = BayesianPrior()
        assert prior.alpha == 1.0
        assert prior.beta == 1.0
        assert prior.mean == 0.5  # uniform prior

    def test_update_repayments_lower_default_prob(self):
        prior = BayesianPrior()
        updated = prior.update(repaid=9, defaulted=1)
        assert updated.mean < 0.5  # more repayments → lower default probability

    def test_update_defaults_raise_prob(self):
        prior = BayesianPrior()
        updated = prior.update(repaid=1, defaulted=9)
        assert updated.mean > 0.5

    def test_credible_interval_contains_mean(self):
        prior = BayesianPrior(alpha=5, beta=2)
        lo, hi = prior.credible_interval(0.95)
        assert lo < prior.mean < hi

    def test_confidence_mass_increases_with_data(self):
        p0 = BayesianPrior()  # 0 observations
        p10 = BayesianPrior(alpha=6, beta=6)  # 10 observations
        p20 = BayesianPrior(alpha=11, beta=11)  # 20 observations
        assert p0.confidence_mass < p10.confidence_mass <= p20.confidence_mass

    def test_conjugate_property(self):
        prior = BayesianPrior(alpha=2, beta=3)
        updated = prior.update(repaid=4, defaulted=2)
        assert updated.alpha == 6
        assert updated.beta == 5


# ---------------------------------------------------------------------------
# TemporalWindow
# ---------------------------------------------------------------------------

class TestTemporalWindow:
    def test_zero_age_weight_is_one(self):
        tw = TemporalWindow(half_life_days=90)
        assert tw.decay_weight(0) == pytest.approx(1.0)

    def test_half_life_weight_is_half(self):
        tw = TemporalWindow(half_life_days=90)
        assert tw.decay_weight(90) == pytest.approx(0.5, abs=1e-6)

    def test_older_has_lower_weight(self):
        tw = TemporalWindow(half_life_days=90)
        assert tw.decay_weight(30) > tw.decay_weight(60) > tw.decay_weight(120)

    def test_weighted_mean_recent_dominates(self):
        tw = TemporalWindow(half_life_days=30)
        now = datetime.utcnow()
        # Recent tx with value 1000, old tx with value 0
        values = [1000.0, 0.0]
        timestamps = [now - timedelta(days=1), now - timedelta(days=180)]
        wmean = tw.weighted_mean(values, timestamps, now=now)
        assert wmean > 500  # recent high-value tx dominates

    def test_effective_count_with_single_recent(self):
        tw = TemporalWindow(half_life_days=90)
        now = datetime.utcnow()
        count = tw.effective_count([now], now=now)
        assert count == pytest.approx(1.0)

    def test_weighted_mean_empty(self):
        tw = TemporalWindow()
        assert tw.weighted_mean([], [], now=datetime.utcnow()) == 0.0


# ---------------------------------------------------------------------------
# VolatilityScorer
# ---------------------------------------------------------------------------

class TestVolatilityScorer:
    def test_zero_volatility_no_penalty(self):
        vs = VolatilityScorer()
        result = vs.penalty([100.0, 100.0, 100.0], [500.0, 500.0])
        assert result["penalty"] == pytest.approx(0.0, abs=0.1)

    def test_high_cv_increases_penalty(self):
        vs = VolatilityScorer()
        low_vol = vs.penalty([100.0] * 10, [])
        high_vol = vs.penalty([1.0, 1000.0, 0.5, 999.0] * 3, [])
        assert high_vol["penalty"] > low_vol["penalty"]

    def test_max_drawdown_on_declining_balance(self):
        vs = VolatilityScorer()
        balances = [1000.0, 800.0, 600.0, 200.0]
        result = vs.penalty([], balances)
        # drawdown = (1000 - 200) / 1000 = 0.8
        assert result["max_drawdown"] == pytest.approx(0.8, abs=0.01)

    def test_penalty_capped_at_scale(self):
        vs = VolatilityScorer(penalty_scale=80)
        result = vs.penalty([1.0, 1e9, 2.0, 1e9], [1000.0, 100.0, 10.0])
        assert result["penalty"] <= 80.0

    def test_empty_inputs_no_error(self):
        vs = VolatilityScorer()
        result = vs.penalty([], [])
        assert result["penalty"] == 0.0


# ---------------------------------------------------------------------------
# AdvancedRiskModel (integration)
# ---------------------------------------------------------------------------

class TestAdvancedRiskModel:
    def test_full_profile_returns_expected_keys(self):
        model = AdvancedRiskModel()
        profile = model.compute_full_risk_profile(
            address="0xabc",
            base_score=600.0,
        )
        assert "base_score" in profile
        assert "advanced_score" in profile
        assert "total_adjustment" in profile
        assert "components" in profile
        assert "risk_factors" in profile

    def test_advanced_score_within_bounds(self):
        model = AdvancedRiskModel()
        profile = model.compute_full_risk_profile(
            address="0xdef",
            base_score=800.0,
            balance_history=[1000.0, 100.0, 10.0],
        )
        assert 0.0 <= profile["advanced_score"] <= 1000.0

    def test_known_defaulter_lowers_score(self):
        model = AdvancedRiskModel()
        loan_history = [{"status": "defaulted"}] * 5 + [{"status": "repaid"}]
        profile = model.compute_full_risk_profile(
            address="0xbad",
            base_score=500.0,
            loan_history=loan_history,
        )
        assert profile["advanced_score"] < 500.0

    def test_good_repayment_history_softens_penalty(self):
        model = AdvancedRiskModel()
        good_loans = [{"status": "repaid"}] * 10
        profile = model.compute_full_risk_profile(
            address="0xgood",
            base_score=500.0,
            loan_history=good_loans,
        )
        # Bayesian adjustment with no defaults should be minimal
        assert profile["components"]["bayesian"]["posterior_default_probability"] < 0.3

    def test_prior_persistence_across_calls(self):
        model = AdvancedRiskModel()
        model.update_prior("0xpersist", repaid=5, defaulted=1)
        prior = model.get_prior("0xpersist")
        assert prior.alpha == 6.0
        assert prior.beta == 2.0

    def test_temporal_analysis_with_transactions(self):
        now = datetime.utcnow()
        txs = [
            {"timestamp": (now - timedelta(days=5)).isoformat(), "value": 100},
            {"timestamp": (now - timedelta(days=200)).isoformat(), "value": 50},
        ]
        model = AdvancedRiskModel()
        temporal = model.temporal_analysis(txs)
        assert temporal["temporal_adjusted"] is True
        assert temporal["total_transactions"] == 2
        # Recent tx is more recent than 200 days
        assert temporal["most_recent_days_ago"] < 10

    def test_risk_factors_populated_for_bad_wallet(self):
        model = AdvancedRiskModel()
        profile = model.compute_full_risk_profile(
            address="0xrisk",
            base_score=300.0,
            transactions=[{"value": 0.001, "timestamp": "2020-01-01"}],
            balance_history=[1000.0, 500.0, 10.0, 1.0],
            loan_history=[{"status": "defaulted"}] * 4,
        )
        assert len(profile["risk_factors"]) > 0
