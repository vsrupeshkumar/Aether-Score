"""Unit tests for WalletGraph (services/behavioral_graph.py)."""

from datetime import datetime

import pytest

from services.behavioral_graph import (
    TransactionEdge,
    WalletGraph,
    WalletNode,
)


def _edge(frm: str, to: str, value: float = 1.0) -> TransactionEdge:
    return TransactionEdge(
        from_address=frm,
        to_address=to,
        value=value,
        tx_hash=f"{frm}-{to}",
        timestamp=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

class TestWalletGraphConstruction:
    def test_add_wallet_node(self):
        g = WalletGraph()
        g.add_wallet(WalletNode(address="0xA"))
        assert g.node_count() == 1

    def test_add_transaction_creates_nodes(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        assert g.node_count() == 2
        assert g.edge_count() == 1

    def test_add_duplicate_edge_accumulates_weight(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB", value=10.0))
        g.add_transaction(_edge("0xA", "0xB", value=20.0))
        assert g.edge_count() == 1
        weight = g._g["0xa"]["0xb"]["weight"]
        assert weight == pytest.approx(30.0)

    def test_flag_wallet(self):
        g = WalletGraph()
        g.add_wallet(WalletNode("0xBad"))
        g.flag_wallet("0xBad", risk_score=1.0)
        assert "0xbad" in g._flagged

    def test_bulk_add_transactions(self):
        g = WalletGraph()
        edges = [_edge(f"0x{i}", f"0x{i+1}") for i in range(5)]
        g.bulk_add_transactions(edges)
        assert g.node_count() == 6
        assert g.edge_count() == 5


# ---------------------------------------------------------------------------
# Neighbours
# ---------------------------------------------------------------------------

class TestNeighbours:
    def test_direct_neighbours(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        g.add_transaction(_edge("0xA", "0xC"))
        nbrs = g.neighbours("0xA", depth=1)
        assert {"0xb", "0xc"} == nbrs

    def test_depth_2_neighbours(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        g.add_transaction(_edge("0xB", "0xC"))
        nbrs = g.neighbours("0xA", depth=2)
        assert "0xc" in nbrs

    def test_unknown_address_returns_empty(self):
        g = WalletGraph()
        assert g.neighbours("0xUnknown") == set()


# ---------------------------------------------------------------------------
# PageRank / Trust
# ---------------------------------------------------------------------------

class TestPageRank:
    def test_pagerank_returns_all_nodes(self):
        g = WalletGraph()
        for i in range(5):
            g.add_transaction(_edge(f"0x{i}", f"0x{(i+1) % 5}"))
        ranks = g.compute_pagerank()
        assert len(ranks) == 5

    def test_pagerank_values_in_0_1(self):
        g = WalletGraph()
        for i in range(4):
            g.add_transaction(_edge(f"0x{i}", f"0x{i+1}"))
        ranks = g.compute_pagerank()
        for v in ranks.values():
            assert 0.0 <= v <= 1.0

    def test_hub_node_higher_rank(self):
        g = WalletGraph()
        # Hub 0xH receives edges from many nodes
        for i in range(6):
            g.add_transaction(_edge(f"0xS{i}", "0xH", value=10.0))
        ranks = g.compute_pagerank()
        hub_rank = ranks.get("0xh", 0)
        avg_rank = sum(ranks.values()) / len(ranks)
        assert hub_rank > avg_rank

    def test_trust_score_in_bounds(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        g.add_transaction(_edge("0xC", "0xA"))
        score = g.trust_score("0xA")
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Risk propagation
# ---------------------------------------------------------------------------

class TestRiskPropagation:
    def test_flagged_node_propagates_to_direct_neighbour(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xBad", "0xNeighbour"))
        g.flag_wallet("0xBad", risk_score=1.0)
        risk_map = g.propagate_risk(max_hops=1)
        assert "0xneighbour" in risk_map
        assert risk_map["0xneighbour"] > 0

    def test_propagation_decreases_with_distance(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xBad", "0xN1"))
        g.add_transaction(_edge("0xN1", "0xN2"))
        g.add_transaction(_edge("0xN2", "0xN3"))
        g.flag_wallet("0xBad", risk_score=1.0)
        risk_map = g.propagate_risk(max_hops=3)
        r1 = risk_map.get("0xn1", 0)
        r2 = risk_map.get("0xn2", 0)
        r3 = risk_map.get("0xn3", 0)
        assert r1 > r2 > r3

    def test_non_neighbour_gets_zero_risk(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xBad", "0xN1"))
        g.add_wallet(WalletNode("0xSafe"))
        g.flag_wallet("0xBad")
        risk_map = g.propagate_risk(max_hops=1)
        assert risk_map.get("0xsafe", 0) == 0.0

    def test_propagated_risk_score_clamped(self):
        g = WalletGraph()
        # Many flagged nodes all connected to same target
        for i in range(10):
            g.add_transaction(_edge(f"0xBad{i}", "0xVictim"))
            g.flag_wallet(f"0xBad{i}", risk_score=1.0)
        score = g.propagated_risk_score("0xVictim")
        assert score <= 1.0


# ---------------------------------------------------------------------------
# Community / suspicious clusters
# ---------------------------------------------------------------------------

class TestCommunities:
    def test_disconnected_graph_has_multiple_communities(self):
        g = WalletGraph()
        # Group A
        g.add_transaction(_edge("0xA1", "0xA2"))
        g.add_transaction(_edge("0xA2", "0xA3"))
        # Group B (disconnected)
        g.add_transaction(_edge("0xB1", "0xB2"))
        communities = g.detect_communities()
        assert len(communities) >= 2

    def test_suspicious_clusters_identifies_flagged(self):
        g = WalletGraph()
        # Cluster: 2 out of 4 nodes flagged
        for i in range(4):
            g.add_transaction(_edge(f"0xC{i}", f"0xC{(i+1)%4}"))
        g.flag_wallet("0xC0")
        g.flag_wallet("0xC1")
        clusters = g.suspicious_clusters(min_flagged_ratio=0.1)
        assert len(clusters) >= 1
        assert clusters[0]["flagged_count"] >= 2


# ---------------------------------------------------------------------------
# Centrality
# ---------------------------------------------------------------------------

class TestCentrality:
    def test_isolated_node_zero_centrality(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        g.add_wallet(WalletNode("0xIsolated"))
        metrics = g.centrality_metrics("0xIsolated")
        assert metrics["degree_centrality"] == 0.0

    def test_centrality_keys_present(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        g.add_transaction(_edge("0xB", "0xC"))
        m = g.centrality_metrics("0xB")
        assert "degree_centrality" in m
        assert "betweenness_centrality" in m
        assert "closeness_centrality" in m


# ---------------------------------------------------------------------------
# Wallet intelligence
# ---------------------------------------------------------------------------

class TestWalletIntelligence:
    def test_intelligence_keys(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xA", "0xB"))
        intel = g.wallet_intelligence("0xA")
        for key in ("graph_adjustment", "trust_score", "propagated_risk", "centrality"):
            assert key in intel

    def test_flagged_neighbour_adds_warnings(self):
        g = WalletGraph()
        g.add_transaction(_edge("0xBad", "0xUser"))
        g.flag_wallet("0xBad")
        intel = g.wallet_intelligence("0xUser")
        assert intel["flagged_neighbours"] >= 1
        assert len(intel["graph_warnings"]) >= 1

    def test_empty_graph_returns_defaults(self):
        g = WalletGraph()
        intel = g.wallet_intelligence("0xNew")
        assert intel["graph_node_count"] == 0
