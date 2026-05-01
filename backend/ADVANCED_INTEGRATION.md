# AetherScore Advanced Intelligence Layer — Integration Guide

## Overview

All new modules are **additive only**. Zero existing files were modified.
Mount the new router and optionally start the streaming background task.

---

## Step 1 — Mount the v2 Router (app.py)

Add these two lines anywhere near the bottom of `app.py` (after the app is created):

```python
from api.advanced_endpoints import router as advanced_router
app.include_router(advanced_router, prefix="/api/v2")
```

This exposes all new endpoints under `/api/v2/...`.

---

## Step 2 — Mount Tracing Middleware (app.py)

Add **before** `LoggingMiddleware` so correlation IDs are available in all logs:

```python
from middleware.tracing import TracingMiddleware
app.add_middleware(TracingMiddleware)
```

Response headers will now include:
- `X-Correlation-ID` — propagated or generated per request
- `X-Request-ID` — unique per HTTP call
- `X-Response-Time` — latency in ms

---

## Step 3 — Start the Streaming Scorer (app.py lifespan)

```python
import asyncio
from services.streaming_scorer import get_streaming_scorer

@app.on_event("startup")
async def start_streaming():
    scorer = get_streaming_scorer()
    asyncio.create_task(scorer.run())

@app.on_event("shutdown")
async def stop_streaming():
    await get_streaming_scorer().stop()
```

---

## Step 4 — Seed Reference Distributions for Drift Detection

Call this once at startup (or from a management script) after loading historical scores:

```python
from services.drift_detector import get_drift_detector

detector = get_drift_detector()
detector.set_reference_scores(historical_scores_list)          # List[float]
detector.set_reference_features({"balance": [...], ...})       # Dict[str, List[float]]
```

---

## New Endpoints Reference

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/score/advanced/{address}` | Full Bayesian+temporal+volatility risk profile |
| GET  | `/api/v2/score/stream/{address}` | SSE stream of real-time score updates |
| POST | `/api/v2/score/stream/ingest` | Push a blockchain event into the streaming pipeline |
| POST | `/api/v2/score/pipeline/{address}` | Run the full plugin pipeline |
| GET  | `/api/v2/graph/wallet/{address}` | Graph trust score, risk propagation, centrality |
| POST | `/api/v2/graph/ingest` | Add transactions to the wallet graph |
| GET  | `/api/v2/graph/suspicious-clusters` | Suspicious wallet cluster report |
| POST | `/api/v2/monitoring/drift` | Run PSI + feature drift check |
| GET  | `/api/v2/monitoring/alerts` | Active drift alerts |
| POST | `/api/v2/explain` | Feature attribution + human-readable explanation |
| GET  | `/api/v2/explain/{address}` | Explanation for a live wallet |
| GET  | `/api/v2/plugins` | List registered scoring plugins |
| POST | `/api/v2/plugins/{name}/toggle` | Enable/disable a plugin |
| GET  | `/api/v2/health` | Advanced layer health check |

---

## New Module Map

```
backend/
├── services/
│   ├── advanced_risk_model.py   ← Bayesian + temporal decay + volatility
│   ├── streaming_scorer.py      ← Real-time event-driven scoring pipeline
│   ├── behavioral_graph.py      ← Wallet graph intelligence (PageRank, risk propagation)
│   ├── drift_detector.py        ← PSI + KS drift monitoring + alerts
│   ├── plugin_system.py         ← Modular plugin registry + weighted pipeline
│   └── explainability_engine.py ← SHAP + rule-based attribution + narratives
├── middleware/
│   └── tracing.py               ← Distributed tracing (correlation IDs, OTel)
├── api/
│   └── advanced_endpoints.py    ← All v2 API routes
└── tests/unit/
    ├── test_advanced_risk.py
    ├── test_behavioral_graph.py
    ├── test_drift_detector.py
    ├── test_streaming_scorer.py
    ├── test_plugin_system.py
    └── test_explainability.py
```

---

## Running Tests

```bash
cd backend
pytest tests/unit/test_advanced_risk.py -v
pytest tests/unit/test_behavioral_graph.py -v
pytest tests/unit/test_drift_detector.py -v
pytest tests/unit/test_streaming_scorer.py -v
pytest tests/unit/test_plugin_system.py -v
pytest tests/unit/test_explainability.py -v

# All new tests together
pytest tests/unit/test_advanced_risk.py tests/unit/test_behavioral_graph.py \
       tests/unit/test_drift_detector.py tests/unit/test_streaming_scorer.py \
       tests/unit/test_plugin_system.py tests/unit/test_explainability.py -v
```

---

## Registering a Custom Plugin

```python
from services.plugin_system import ScoringPlugin, PluginResult, get_plugin_registry

class MyCustomPlugin(ScoringPlugin):
    priority = 50
    weight = 0.8

    @property
    def name(self) -> str:
        return "my_custom"

    async def compute(self, address: str, context: dict) -> PluginResult:
        # ... your logic ...
        return PluginResult(
            plugin_name=self.name,
            score_adjustment=10.0,
            confidence=0.9,
            explanation="Custom adjustment based on X",
        )

get_plugin_registry().register(MyCustomPlugin())
```

---

## Environment Variables

No new required env vars. Optional:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | None | If set, StreamingScorer uses Redis Streams instead of in-process queue |
