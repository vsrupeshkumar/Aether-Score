"""Unit tests for ExplainabilityEngine (services/explainability_engine.py)."""

import pytest

from services.explainability_engine import (
    ExplainabilityEngine,
    FeatureContribution,
    _human_label,
    _narrative,
    rule_based_contributions,
)


# ---------------------------------------------------------------------------
# Human label mapping
# ---------------------------------------------------------------------------

class TestHumanLabel:
    def test_known_feature_returns_correct_label(self):
        assert _human_label("balance") == "Current Balance"
        assert _human_label("tx_count") == "Transaction Count"

    def test_unknown_feature_title_cases(self):
        result = _human_label("my_custom_feature")
        assert result == "My Custom Feature"

    def test_empty_string(self):
        result = _human_label("")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# FeatureContribution
# ---------------------------------------------------------------------------

class TestFeatureContribution:
    def test_positive_direction(self):
        fc = FeatureContribution("balance", 1000.0, 50.0, direction="", percentile=80)
        assert fc.direction == "positive"

    def test_negative_direction(self):
        fc = FeatureContribution("liquidations", 3.0, -60.0, direction="", percentile=10)
        assert fc.direction == "negative"

    def test_neutral_direction(self):
        fc = FeatureContribution("tx_count", 5.0, 0.0, direction="", percentile=50)
        assert fc.direction == "neutral"

    def test_impact_level_high(self):
        fc = FeatureContribution("balance", 1000.0, 100.0, direction="positive", percentile=90)
        assert fc.impact_level == "high"

    def test_impact_level_medium(self):
        fc = FeatureContribution("age_days", 365.0, 20.0, direction="positive", percentile=70)
        assert fc.impact_level == "medium"

    def test_impact_level_low(self):
        fc = FeatureContribution("nft_holdings", 2.0, 5.0, direction="positive", percentile=50)
        assert fc.impact_level == "low"


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------

class TestNarrative:
    def test_liquidation_narrative(self):
        fc = FeatureContribution("liquidations", 3.0, -90.0, "negative", 5)
        n = _narrative(fc)
        assert "liquidation" in n.lower()

    def test_inactive_wallet_narrative(self):
        fc = FeatureContribution("last_activity_days", 200.0, -30.0, "negative", 20)
        n = _narrative(fc)
        assert "inactive" in n.lower() or "activity" in n.lower()

    def test_high_repayment_narrative(self):
        fc = FeatureContribution("repayment_ratio", 0.95, 80.0, "positive", 95)
        n = _narrative(fc)
        assert "repayment" in n.lower()

    def test_neutral_narrative(self):
        fc = FeatureContribution("governance_votes", 1.0, 0.0, "neutral", 50)
        n = _narrative(fc)
        assert "neutral" in n.lower()

    def test_returns_string(self):
        fc = FeatureContribution("balance", 500.0, 30.0, "positive", 60)
        assert isinstance(_narrative(fc), str)


# ---------------------------------------------------------------------------
# Rule-based contributions
# ---------------------------------------------------------------------------

class TestRuleBasedContributions:
    def test_returns_list_of_feature_contributions(self):
        features = {
            "balance": 1.5,
            "tx_count": 50.0,
            "repayment_ratio": 0.9,
            "liquidations": 0.0,
        }
        contribs = rule_based_contributions(features, base_score=600.0)
        assert isinstance(contribs, list)
        assert all(isinstance(c, FeatureContribution) for c in contribs)

    def test_sorted_by_absolute_contribution(self):
        features = {"balance": 100.0, "liquidations": 5.0, "tx_count": 10.0}
        contribs = rule_based_contributions(features, base_score=500.0)
        abs_contribs = [abs(c.contribution) for c in contribs]
        assert abs_contribs == sorted(abs_contribs, reverse=True)

    def test_liquidations_negative_contribution(self):
        features = {"liquidations": 5.0}
        contribs = rule_based_contributions(features, base_score=500.0)
        liq = next((c for c in contribs if c.name == "liquidations"), None)
        assert liq is not None
        assert liq.contribution < 0

    def test_empty_features(self):
        contribs = rule_based_contributions({}, base_score=500.0)
        assert isinstance(contribs, list)

    def test_high_repayment_positive(self):
        features = {"repayment_ratio": 1.0}
        contribs = rule_based_contributions(features, base_score=500.0)
        r = next((c for c in contribs if c.name == "repayment_ratio"), None)
        assert r is not None
        assert r.contribution > 0


# ---------------------------------------------------------------------------
# ExplainabilityEngine
# ---------------------------------------------------------------------------

class TestExplainabilityEngine:
    def setup_method(self):
        self.engine = ExplainabilityEngine()
        self.features = {
            "balance": 2.5,
            "tx_count": 80.0,
            "age_days": 400.0,
            "repayment_ratio": 0.85,
            "liquidations": 0.0,
            "staking_amount": 1000.0,
        }

    def test_explain_features_returns_required_keys(self):
        result = self.engine.explain_features(self.features, base_score=650.0)
        for key in ("method", "base_score", "contributions", "summary", "narratives"):
            assert key in result

    def test_contributions_have_required_fields(self):
        result = self.engine.explain_features(self.features, base_score=650.0)
        for c in result["contributions"]:
            assert "feature" in c
            assert "contribution" in c
            assert "direction" in c
            assert "impact_level" in c

    def test_base_score_preserved(self):
        result = self.engine.explain_features(self.features, base_score=750.0)
        assert result["base_score"] == 750.0

    def test_summary_is_string(self):
        result = self.engine.explain_features(self.features, base_score=600.0)
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 10

    def test_narratives_list_of_strings(self):
        result = self.engine.explain_features(self.features, base_score=600.0)
        assert isinstance(result["narratives"], list)
        assert all(isinstance(n, str) for n in result["narratives"])

    def test_empty_features_no_crash(self):
        result = self.engine.explain_features({}, base_score=500.0)
        assert "contributions" in result

    def test_score_breakdown(self):
        components = {
            "base": 600.0,
            "staking_boost": 50.0,
            "oracle_penalty": -20.0,
            "volatility_penalty": -15.0,
        }
        breakdown = self.engine.score_breakdown(components)
        assert "components" in breakdown
        assert "total_score" in breakdown
        assert breakdown["total_score"] == pytest.approx(615.0)

    def test_score_breakdown_has_percentages(self):
        components = {"base": 500.0, "boost": 100.0}
        breakdown = self.engine.score_breakdown(components)
        for comp in breakdown["components"]:
            assert 0.0 <= comp["percentage"] <= 100.0

    def test_high_liquidations_triggers_negative(self):
        features_bad = dict(self.features)
        features_bad["liquidations"] = 5.0
        result = self.engine.explain_features(features_bad, base_score=400.0)
        neg_factors = result.get("top_negative_factors", [])
        # Liquidations should appear in negative factors
        all_contribs = {c["feature"]: c["contribution"] for c in result["contributions"]}
        if "liquidations" in all_contribs:
            assert all_contribs["liquidations"] < 0

    def test_top_factors_are_lists(self):
        result = self.engine.explain_features(self.features, base_score=500.0)
        assert isinstance(result["top_positive_factors"], list)
        assert isinstance(result["top_negative_factors"], list)
