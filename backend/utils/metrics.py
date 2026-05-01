"""
Prometheus metrics definitions
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# API Endpoint Metrics
api_requests_total = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["endpoint", "status"]
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Blockchain Metrics
blockchain_transactions_total = Counter(
    "blockchain_transactions_total",
    "Total number of blockchain transactions",
    ["status", "contract"]
)

blockchain_transaction_duration_seconds = Histogram(
    "blockchain_transaction_duration_seconds",
    "Blockchain transaction duration in seconds",
    ["contract", "operation"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0]
)

blockchain_gas_used = Histogram(
    "blockchain_gas_used",
    "Gas used for blockchain transactions",
    ["contract", "operation"],
    buckets=[10000, 50000, 100000, 200000, 500000, 1000000]
)

blockchain_rpc_errors_total = Counter(
    "blockchain_rpc_errors_total",
    "Total number of blockchain RPC errors",
    ["error_type"]
)

# Score Computation Metrics
score_computations_total = Counter(
    "score_computations_total",
    "Total number of score computations",
    ["status"]
)

score_computation_duration_seconds = Histogram(
    "score_computation_duration_seconds",
    "Score computation duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

score_distribution = Histogram(
    "score_distribution",
    "Distribution of credit scores",
    buckets=[0, 200, 400, 600, 800, 1000]
)

# Oracle Metrics
oracle_calls_total = Counter(
    "oracle_calls_total",
    "Total number of oracle calls",
    ["oracle_type", "status"]
)

oracle_call_duration_seconds = Histogram(
    "oracle_call_duration_seconds",
    "Oracle call duration in seconds",
    ["oracle_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Error Metrics
errors_total = Counter(
    "errors_total",
    "Total number of errors",
    ["error_type", "endpoint"]
)

# Active Connections
active_requests = Gauge(
    "active_requests",
    "Number of active requests"
)

# Application Info
app_info = Info(
    "app_info",
    "Application information"
)

# Staking Metrics
staking_operations_total = Counter(
    "staking_operations_total",
    "Total number of staking operations",
    ["operation", "status"]
)

staking_amount = Gauge(
    "staking_total_amount",
    "Total amount staked",
    ["tier"]
)

# Indexer Metrics
indexer_operations_total = Counter(
    "indexer_operations_total",
    "Total number of indexer operations",
    ["operation", "status"]
)

indexer_operation_duration_seconds = Histogram(
    "indexer_operation_duration_seconds",
    "Indexer operation duration in seconds",
    ["operation"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
)

indexer_transactions_indexed = Counter(
    "indexer_transactions_indexed_total",
    "Total number of transactions indexed",
    ["status"]
)


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_api_request(endpoint: str, status: str, duration: float):
    """Record API request metrics"""
    api_requests_total.labels(endpoint=endpoint, status=status).inc()
    api_request_duration_seconds.labels(endpoint=endpoint).observe(duration)


def record_blockchain_transaction(
    status: str,
    contract: str,
    operation: str,
    duration: float,
    gas_used: Optional[int] = None
):
    """Record blockchain transaction metrics"""
    blockchain_transactions_total.labels(status=status, contract=contract).inc()
    blockchain_transaction_duration_seconds.labels(contract=contract, operation=operation).observe(duration)
    if gas_used:
        blockchain_gas_used.labels(contract=contract, operation=operation).observe(gas_used)


def record_blockchain_rpc_error(error_type: str):
    """Record blockchain RPC error"""
    blockchain_rpc_errors_total.labels(error_type=error_type).inc()


def record_score_computation(status: str, duration: float, score: Optional[int] = None):
    """Record score computation metrics"""
    score_computations_total.labels(status=status).inc()
    score_computation_duration_seconds.observe(duration)
    if score is not None:
        score_distribution.observe(score)


def record_oracle_call(oracle_type: str, status: str, duration: float):
    """Record oracle call metrics"""
    oracle_calls_total.labels(oracle_type=oracle_type, status=status).inc()
    oracle_call_duration_seconds.labels(oracle_type=oracle_type).observe(duration)


def record_error(error_type: str, endpoint: str):
    """Record error metric"""
    errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def set_app_info(version: str, environment: str):
    """Set application information"""
    app_info.info({"version": version, "environment": environment})


def get_metrics():
    """Get Prometheus metrics in text format"""
    return generate_latest()


def get_metrics_content_type():
    """Get content type for metrics endpoint"""
    return CONTENT_TYPE_LATEST


def record_indexer_operation(
    operation: str,
    status: str,
    duration: float,
    transactions_count: Optional[int] = None
):
    """Record indexer operation metrics"""
    indexer_operations_total.labels(operation=operation, status=status).inc()
    indexer_operation_duration_seconds.labels(operation=operation).observe(duration)
    if transactions_count is not None:
        indexer_transactions_indexed.labels(status=status).inc(transactions_count)


def record_blockchain_rpc_call(
    operation: str,
    status: str,
    blocks_queried: Optional[int] = None
):
    """Record blockchain RPC call metrics"""
    # This can be expanded if needed
    pass

