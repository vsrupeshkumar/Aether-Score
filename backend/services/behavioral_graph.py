"""
Behavioral Graph Intelligence — Phase 1 Extension

Models wallets as nodes in a directed weighted graph.
Edges are transactions; edge weight = normalised transfer value.

Features added (non-breaking):
  - Graph-based trust score via PageRank
  - Risk propagation from known-bad wallets
  - Suspicious cluster detection (community detection)
  - Centrality metrics per wallet
  - No changes to existing feature_engineering.py
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class WalletNode:
    address: str
    is_flagged: bool = False          # set by fraud_detection or manual blacklist
    risk_score: float = 0.5           # 0 = safe, 1 = very risky
    labels: List[str] = field(default_factory=list)  # e.g. "exchange", "mixer"


@dataclass
class TransactionEdge:
    from_address: str
    to_address: str
    value: float
    tx_hash: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    token: str = "native"


# ---------------------------------------------------------------------------
# Core graph engine
# ---------------------------------------------------------------------------

class WalletGraph:
    """
    Maintains a NetworkX DiGraph of wallet interactions.

    Thread-safety: not thread-safe by default; use a lock if sharing
    across concurrent coroutines.
    """

    # Propagation: how much of a flagged neighbour's risk bleeds to others
    RISK_PROPAGATION_DAMPING: float = 0.3

    # Minimum edge weight (prevents zero-weight edges distorting PageRank)
    MIN_EDGE_WEIGHT: float = 1e-6

    def __init__(self):
        self._g: nx.DiGraph = nx.DiGraph()
        self._flagged: Set[str] = set()
        self._last_updated: datetime = datetime.utcnow()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_wallet(self, node: WalletNode) -> None:
        addr = node.address.lower()
        self._g.add_node(addr, **{
            "is_flagged": node.is_flagged,
            "risk_score": node.risk_score,
            "labels": node.labels,
        })
        if node.is_flagged:
            self._flagged.add(addr)

    def add_transaction(self, edge: TransactionEdge) -> None:
        frm = edge.from_address.lower()
        to = edge.to_address.lower()

        # Ensure nodes exist
        for addr in (frm, to):
            if addr not in self._g:
                self._g.add_node(addr, is_flagged=False, risk_score=0.5, labels=[])

        # Accumulate edge weight if edge already exists
        if self._g.has_edge(frm, to):
            self._g[frm][to]["weight"] += max(edge.value, self.MIN_EDGE_WEIGHT)
            self._g[frm][to]["tx_count"] += 1
        else:
            self._g.add_edge(frm, to,
                             weight=max(edge.value, self.MIN_EDGE_WEIGHT),
                             tx_count=1,
                             first_seen=edge.timestamp.isoformat())

        self._last_updated = datetime.utcnow()

    def bulk_add_transactions(self, edges: List[TransactionEdge]) -> None:
        for e in edges:
            self.add_transaction(e)

    def flag_wallet(self, address: str, risk_score: float = 1.0) -> None:
        addr = address.lower()
        if addr in self._g:
            self._g.nodes[addr]["is_flagged"] = True
            self._g.nodes[addr]["risk_score"] = risk_score
        else:
            self._g.add_node(addr, is_flagged=True, risk_score=risk_score, labels=["flagged"])
        self._flagged.add(addr)

    # ------------------------------------------------------------------
    # Graph metrics
    # ------------------------------------------------------------------

    def node_count(self) -> int:
        return self._g.number_of_nodes()

    def edge_count(self) -> int:
        return self._g.number_of_edges()

    def neighbours(self, address: str, depth: int = 1) -> Set[str]:
        """Return all wallets within `depth` hops."""
        addr = address.lower()
        if addr not in self._g:
            return set()
        reachable = set(nx.single_source_shortest_path_length(self._g.to_undirected(), addr, cutoff=depth).keys())
        reachable.discard(addr)
        return reachable

    # ------------------------------------------------------------------
    # PageRank trust score
    # ------------------------------------------------------------------

    def compute_pagerank(
        self,
        alpha: float = 0.85,
        personalised_node: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Returns PageRank per node.

        If `personalised_node` is given, compute personalised PageRank that
        biases toward that wallet's local neighbourhood.
        """
        if self._g.number_of_nodes() == 0:
            return {}

        personalization = None
        if personalised_node:
            addr = personalised_node.lower()
            personalization = {n: (1.0 if n == addr else 0.0) for n in self._g.nodes}

        try:
            ranks = nx.pagerank(
                self._g,
                alpha=alpha,
                weight="weight",
                personalization=personalization,
                max_iter=200,
            )
        except nx.PowerIterationFailedConvergence:
            logger.warning("PageRank did not converge; falling back to uniform")
            n = self._g.number_of_nodes()
            ranks = {node: 1.0 / n for node in self._g.nodes}

        # Normalise to [0, 1] relative to max rank
        max_rank = max(ranks.values(), default=1.0)
        if max_rank > 0:
            ranks = {k: v / max_rank for k, v in ranks.items()}
        return ranks

    def trust_score(self, address: str) -> float:
        """
        0–1 trust score for a single address based on personalised PageRank.
        Higher = more central and trusted within the interaction graph.
        """
        ranks = self.compute_pagerank(personalised_node=address)
        return round(ranks.get(address.lower(), 0.5), 4)

    # ------------------------------------------------------------------
    # Risk propagation
    # ------------------------------------------------------------------

    def propagate_risk(self, max_hops: int = 3) -> Dict[str, float]:
        """
        Propagate risk from flagged nodes outward via BFS with exponential decay.

        risk(node) += sum over flagged ancestors of:
            flagged_risk * DAMPING^distance
        """
        risk_map: Dict[str, float] = {}

        for flagged in self._flagged:
            if flagged not in self._g:
                continue
            base_risk = self._g.nodes[flagged].get("risk_score", 1.0)

            # BFS outward (undirected to catch both directions)
            undirected = self._g.to_undirected()
            for node, distance in nx.single_source_shortest_path_length(
                undirected, flagged, cutoff=max_hops
            ).items():
                if node == flagged:
                    continue
                propagated = base_risk * (self.RISK_PROPAGATION_DAMPING ** distance)
                risk_map[node] = risk_map.get(node, 0.0) + propagated

        # Clamp to [0, 1]
        return {k: min(1.0, v) for k, v in risk_map.items()}

    def propagated_risk_score(self, address: str, max_hops: int = 3) -> float:
        """Return the risk score for a specific address after propagation."""
        addr = address.lower()
        if addr in self._flagged:
            return self._g.nodes[addr].get("risk_score", 1.0)
        risk_map = self.propagate_risk(max_hops)
        return round(risk_map.get(addr, 0.0), 4)

    # ------------------------------------------------------------------
    # Community / cluster detection
    # ------------------------------------------------------------------

    def detect_communities(self) -> List[FrozenSet[str]]:
        """
        Detect communities using the Louvain algorithm (via networkx).
        Falls back to connected components if python-louvain is unavailable.
        """
        if self._g.number_of_nodes() == 0:
            return []

        undirected = self._g.to_undirected()

        try:
            from networkx.algorithms import community as nx_comm
            # Greedy modularity — available in all recent networkx
            communities = list(nx_comm.greedy_modularity_communities(undirected, weight="weight"))
            return [frozenset(c) for c in communities]
        except Exception as exc:
            logger.debug("Greedy community detection failed (%s); using components", exc)
            return [frozenset(c) for c in nx.connected_components(undirected)]

    def suspicious_clusters(self, min_flagged_ratio: float = 0.2) -> List[Dict]:
        """
        Return clusters where ≥ min_flagged_ratio of members are flagged.
        These clusters warrant manual review.
        """
        communities = self.detect_communities()
        results = []
        for cluster in communities:
            flagged_in_cluster = cluster & self._flagged
            ratio = len(flagged_in_cluster) / max(len(cluster), 1)
            if ratio >= min_flagged_ratio:
                results.append({
                    "size": len(cluster),
                    "flagged_count": len(flagged_in_cluster),
                    "flagged_ratio": round(ratio, 3),
                    "members": list(cluster),
                    "flagged_members": list(flagged_in_cluster),
                })
        # Sort by flagged_ratio descending
        return sorted(results, key=lambda x: x["flagged_ratio"], reverse=True)

    # ------------------------------------------------------------------
    # Centrality
    # ------------------------------------------------------------------

    def centrality_metrics(self, address: str) -> Dict[str, float]:
        """
        Compute degree, betweenness, and closeness centrality for one wallet.
        All values normalised to [0, 1].
        """
        addr = address.lower()
        if addr not in self._g:
            return {"degree_centrality": 0.0, "betweenness_centrality": 0.0, "closeness_centrality": 0.0}

        n = self._g.number_of_nodes()
        if n < 2:
            return {"degree_centrality": 0.0, "betweenness_centrality": 0.0, "closeness_centrality": 0.0}

        degree_c = nx.degree_centrality(self._g)
        closeness_c = nx.closeness_centrality(self._g)

        # Betweenness is expensive for large graphs — sample if needed
        if n <= 500:
            between_c = nx.betweenness_centrality(self._g, normalized=True, weight="weight")
        else:
            between_c = nx.betweenness_centrality(
                self._g, normalized=True, weight="weight", k=min(100, n)
            )

        return {
            "degree_centrality": round(degree_c.get(addr, 0.0), 4),
            "betweenness_centrality": round(between_c.get(addr, 0.0), 4),
            "closeness_centrality": round(closeness_c.get(addr, 0.0), 4),
        }

    # ------------------------------------------------------------------
    # Full wallet intelligence profile
    # ------------------------------------------------------------------

    def wallet_intelligence(self, address: str) -> Dict:
        """
        Returns a combined intelligence profile for a wallet.
        Designed to be merged with the existing ScoringService result.
        """
        addr = address.lower()
        centrality = self.centrality_metrics(addr)
        trust = self.trust_score(addr)
        propagated_risk = self.propagated_risk_score(addr)
        nbrs = self.neighbours(addr, depth=1)
        flagged_nbrs = nbrs & self._flagged

        # Graph-adjusted score delta: high trust = up to +50; high risk = up to -100
        trust_bonus = trust * 50.0
        risk_penalty = propagated_risk * 100.0
        graph_adjustment = round(trust_bonus - risk_penalty, 2)

        warnings = []
        if propagated_risk > 0.5:
            warnings.append(f"Connected to {len(flagged_nbrs)} flagged wallet(s)")
        if centrality["betweenness_centrality"] > 0.5:
            warnings.append("High transaction routing centrality — potential intermediary")

        return {
            "graph_adjustment": graph_adjustment,
            "trust_score": trust,
            "propagated_risk": propagated_risk,
            "centrality": centrality,
            "direct_neighbours": len(nbrs),
            "flagged_neighbours": len(flagged_nbrs),
            "graph_warnings": warnings,
            "graph_node_count": self.node_count(),
            "graph_edge_count": self.edge_count(),
            "last_updated": self._last_updated.isoformat(),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_graph_instance: Optional[WalletGraph] = None


def get_wallet_graph() -> WalletGraph:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = WalletGraph()
        logger.info("WalletGraph singleton initialised")
    return _graph_instance
