"""
Advanced Endpoints Router — Phase 2 Integration Layer

Mounts ALL new intelligence features under a versioned prefix.
Existing app.py endpoints are UNCHANGED.

Integration (add to app.py or a new include):
    from api.advanced_endpoints import router as advanced_router
    app.include_router(advanced_router, prefix="/api/v2")

Endpoints added:
    POST /api/v2/score/advanced/{address}      — full advanced risk profile
    GET  /api/v2/score/stream/{address}         — SSE streaming score
    POST /api/v2/graph/ingest                   — add transactions to wallet graph
    GET  /api/v2/graph/wallet/{address}         — graph intelligence for a wallet
    GET  /api/v2/graph/suspicious-clusters      — list suspicious wallet clusters
    GET  /api/v2/monitoring/drift               — run full drift check
    GET  /api/v2/monitoring/drift/history       — historical health checks
    GET  /api/v2/monitoring/alerts              — active drift alerts
    GET  /api/v2/explain/{address}              — explainability breakdown
    GET  /api/v2/plugins                        — list registered scoring plugins
    POST /api/v2/plugins/{name}/toggle          — enable/disable a plugin
    POST /api/v2/score/pipeline/{address}       — run full plugin pipeline
    GET  /api/v2/streaming/queue-size           — queue depth
    GET  /api/v2/streaming/scores               — all cached streaming scores
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.advanced_risk_model import AdvancedRiskModel
from services.behavioral_graph import (
    TransactionEdge,
    WalletNode,
    get_wallet_graph,
)
from services.drift_detector import get_drift_detector
from services.explainability_engine import get_explainability_engine
from services.plugin_system import get_plugin_registry, get_scoring_pipeline
from services.streaming_scorer import ChainEvent, get_streaming_scorer
from utils.validators import validate_ethereum_address

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Intelligence (v2)"])

# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

class AdvancedScoreRequest(BaseModel):
    transactions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Raw transaction list")
    loan_history: Optional[List[Dict[str, Any]]] = Field(default=None)
    balance_history: Optional[List[float]] = Field(default=None)
    base_score: Optional[float] = Field(default=None, ge=0, le=1000)


class GraphIngestRequest(BaseModel):
    transactions: List[Dict[str, Any]] = Field(..., description="List of tx dicts with from, to, value, hash, timestamp")
    flagged_addresses: Optional[List[str]] = Field(default=None)


class DriftCheckRequest(BaseModel):
    current_scores: List[float] = Field(..., description="Recent score samples for PSI check")
    current_features: Optional[Dict[str, List[float]]] = Field(default=None)
    scored_wallets: Optional[Dict[str, float]] = Field(default=None)


class ExplainRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Feature name → value map")
    base_score: float = Field(..., ge=0, le=1000)


class StreamEventRequest(BaseModel):
    event_id: str
    address: str
    event_type: str
    value: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class PipelineRequest(BaseModel):
    base_score: float = Field(..., ge=0, le=1000)
    context: Optional[Dict[str, Any]] = Field(default=None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validated_address(address: str) -> str:
    if not validate_ethereum_address(address):
        raise HTTPException(status_code=400, detail=f"Invalid Ethereum address: {address}")
    return address.lower()


# ---------------------------------------------------------------------------
# Advanced risk scoring
# ---------------------------------------------------------------------------

@router.post("/score/advanced/{address}", summary="Advanced risk profile")
async def advanced_score(address: str, body: AdvancedScoreRequest) -> Dict:
    """
    Runs the full advanced risk profile (Bayesian + temporal + volatility)
    on top of an optional provided base_score.

    If base_score is omitted, it defaults to 500.
    This endpoint does NOT call the existing ScoringService — callers should
    fetch the base score first then pass it here.
    """
    addr = _validated_address(address)
    base = body.base_score if body.base_score is not None else 500.0

    model = AdvancedRiskModel()
    profile = model.compute_full_risk_profile(
        address=addr,
        base_score=base,
        transactions=body.transactions or [],
        loan_history=body.loan_history,
        balance_history=body.balance_history,
    )
    return {"address": addr, **profile}


# ---------------------------------------------------------------------------
# Streaming score (SSE)
# ---------------------------------------------------------------------------

@router.get("/score/stream/{address}", summary="Server-Sent Events stream for real-time score")
async def stream_score(address: str):
    """
    Returns a Server-Sent Event stream.  Each update is emitted as:
        data: {"address": ..., "streaming_score": ..., "last_delta": ..., "updated_at": ...}

    Clients connect once and receive score updates as they happen.
    """
    addr = _validated_address(address)
    scorer = get_streaming_scorer()

    async def event_generator():
        async for update in scorer.event_stream(addr):
            import json
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/score/stream/ingest", summary="Ingest a blockchain event into streaming pipeline")
async def ingest_event(body: StreamEventRequest, background_tasks: BackgroundTasks) -> Dict:
    from datetime import datetime
    scorer = get_streaming_scorer()
    event = ChainEvent(
        event_id=body.event_id,
        address=body.address.lower(),
        event_type=body.event_type,
        value=body.value,
        metadata=body.metadata or {},
    )
    background_tasks.add_task(scorer.ingest, event)
    return {"status": "queued", "event_id": body.event_id}


@router.get("/streaming/queue-size", summary="Current streaming event queue depth")
async def queue_size() -> Dict:
    scorer = get_streaming_scorer()
    return {"queue_size": await scorer.queue_size()}


@router.get("/streaming/scores", summary="All cached streaming scores")
async def all_streaming_scores() -> Dict:
    scorer = get_streaming_scorer()
    return {"scores": scorer.get_all_scores()}


# ---------------------------------------------------------------------------
# Behavioral graph
# ---------------------------------------------------------------------------

@router.post("/graph/ingest", summary="Add transactions to wallet interaction graph")
async def graph_ingest(body: GraphIngestRequest, background_tasks: BackgroundTasks) -> Dict:
    """Ingest a batch of transactions to build the wallet graph."""
    from datetime import datetime

    graph = get_wallet_graph()
    edges = []
    for tx in body.transactions:
        frm = tx.get("from") or tx.get("from_address", "")
        to = tx.get("to") or tx.get("to_address", "")
        if not frm or not to:
            continue
        ts_raw = tx.get("timestamp")
        if isinstance(ts_raw, (int, float)):
            ts = datetime.utcfromtimestamp(float(ts_raw))
        else:
            ts = datetime.utcnow()
        edges.append(TransactionEdge(
            from_address=frm,
            to_address=to,
            value=float(tx.get("value", 0) or 0),
            tx_hash=tx.get("hash", tx.get("tx_hash", "")),
            timestamp=ts,
        ))

    background_tasks.add_task(graph.bulk_add_transactions, edges)

    if body.flagged_addresses:
        for addr in body.flagged_addresses:
            graph.flag_wallet(addr)

    return {"status": "accepted", "transactions_queued": len(edges)}


@router.get("/graph/wallet/{address}", summary="Graph intelligence for a wallet")
async def graph_wallet(address: str) -> Dict:
    addr = _validated_address(address)
    graph = get_wallet_graph()
    intel = graph.wallet_intelligence(addr)
    return {"address": addr, **intel}


@router.get("/graph/suspicious-clusters", summary="List suspicious wallet clusters")
async def suspicious_clusters(
    min_flagged_ratio: float = Query(default=0.2, ge=0.0, le=1.0)
) -> Dict:
    graph = get_wallet_graph()
    clusters = graph.suspicious_clusters(min_flagged_ratio=min_flagged_ratio)
    return {
        "cluster_count": len(clusters),
        "clusters": clusters[:50],  # cap response size
        "graph_nodes": graph.node_count(),
        "graph_edges": graph.edge_count(),
    }


@router.get("/graph/stats", summary="Wallet graph statistics")
async def graph_stats() -> Dict:
    graph = get_wallet_graph()
    return {
        "node_count": graph.node_count(),
        "edge_count": graph.edge_count(),
        "flagged_wallets": len(graph._flagged),
    }


# ---------------------------------------------------------------------------
# Drift detection / monitoring
# ---------------------------------------------------------------------------

@router.post("/monitoring/drift", summary="Run drift detection check")
async def run_drift_check(body: DriftCheckRequest) -> Dict:
    detector = get_drift_detector()
    report = detector.run_full_check(
        current_scores=body.current_scores,
        current_feature_map=body.current_features,
        scored_wallets=body.scored_wallets,
    )
    return report


@router.get("/monitoring/drift/history", summary="Historical drift check results")
async def drift_history(limit: int = Query(default=20, ge=1, le=100)) -> Dict:
    detector = get_drift_detector()
    return {"history": detector.get_health_history(limit=limit)}


@router.get("/monitoring/alerts", summary="Active drift alerts")
async def drift_alerts(limit: int = Query(default=50, ge=1, le=200)) -> Dict:
    detector = get_drift_detector()
    return {"alerts": detector.get_alert_history(limit=limit)}


@router.post("/monitoring/alerts/{index}/resolve", summary="Mark a drift alert as resolved")
async def resolve_alert(index: int) -> Dict:
    detector = get_drift_detector()
    ok = detector.resolve_alert(index)
    return {"resolved": ok}


# ---------------------------------------------------------------------------
# Explainability
# ---------------------------------------------------------------------------

@router.post("/explain", summary="Feature attribution and score explanation")
async def explain_score(body: ExplainRequest) -> Dict:
    engine = get_explainability_engine()
    result = engine.explain_features(body.features, body.base_score)
    return result


@router.get("/explain/{address}", summary="Explainability breakdown for a wallet (requires cached features)")
async def explain_wallet(address: str) -> Dict:
    """
    Returns explainability for a wallet if its features are available from
    the existing FeatureEngineering service.
    """
    addr = _validated_address(address)
    try:
        from services.feature_engineering import FeatureEngineering
        fe = FeatureEngineering()
        features_raw = await fe.extract_features(addr)
        # Convert WalletFeatures or dict to plain float dict
        if hasattr(features_raw, "__dict__"):
            features_dict = {k: float(v) for k, v in vars(features_raw).items() if isinstance(v, (int, float))}
        elif isinstance(features_raw, dict):
            features_dict = {k: float(v) for k, v in features_raw.items() if isinstance(v, (int, float))}
        else:
            raise ValueError("Unexpected features type")

        from services.scoring import ScoringService
        scoring = ScoringService()
        score_result = await scoring.compute_score(addr)
        base_score = float(score_result.get("score", 500))

        engine = get_explainability_engine()
        return engine.explain_features(features_dict, base_score)
    except Exception as exc:
        logger.error("Explanation failed for %s: %s", addr, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Explanation error: {exc}")


# ---------------------------------------------------------------------------
# Plugin system
# ---------------------------------------------------------------------------

@router.get("/plugins", summary="List all registered scoring plugins")
async def list_plugins() -> Dict:
    registry = get_plugin_registry()
    return {"plugins": registry.list_plugins()}


@router.post("/plugins/{name}/toggle", summary="Enable or disable a scoring plugin")
async def toggle_plugin(name: str, enabled: bool = Query(...)) -> Dict:
    registry = get_plugin_registry()
    plugin = registry.get(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    plugin.enabled = enabled
    logger.info("Plugin '%s' set enabled=%s", name, enabled)
    return {"plugin": name, "enabled": enabled}


@router.post("/score/pipeline/{address}", summary="Run full scoring plugin pipeline")
async def run_pipeline(address: str, body: PipelineRequest) -> Dict:
    """
    Runs all active plugins for the given address on top of a provided base_score.
    Returns combined final score with per-plugin breakdown.
    """
    addr = _validated_address(address)
    pipeline = get_scoring_pipeline()
    result = await pipeline.run(
        address=addr,
        base_score=body.base_score,
        context=body.context,
    )
    return {"address": addr, **result}


# ---------------------------------------------------------------------------
# Health / meta
# ---------------------------------------------------------------------------

@router.get("/health", summary="Advanced intelligence layer health")
async def advanced_health() -> Dict:
    scorer = get_streaming_scorer()
    graph = get_wallet_graph()
    registry = get_plugin_registry()
    return {
        "status": "ok",
        "streaming_queue_size": await scorer.queue_size(),
        "graph_nodes": graph.node_count(),
        "active_plugins": len(registry.all_active()),
    }
