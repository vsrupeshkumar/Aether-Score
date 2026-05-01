# Metrics Documentation

## Overview

AETHER-SCORE exposes Prometheus metrics at the `/metrics` endpoint for monitoring and observability.

## Available Metrics

### HTTP Request Metrics

- `http_requests_total`: Total number of HTTP requests (labels: method, endpoint, status_code)
- `http_request_duration_seconds`: HTTP request duration in seconds (labels: method, endpoint)

### API Endpoint Metrics

- `api_requests_total`: Total number of API requests (labels: endpoint, status)
- `api_request_duration_seconds`: API request duration in seconds (labels: endpoint)

### Blockchain Metrics

- `blockchain_transactions_total`: Total number of blockchain transactions (labels: status, contract)
- `blockchain_transaction_duration_seconds`: Blockchain transaction duration (labels: contract, operation)
- `blockchain_gas_used`: Gas used for transactions (labels: contract, operation)
- `blockchain_rpc_errors_total`: Total number of blockchain RPC errors (labels: error_type)

### Score Computation Metrics

- `score_computations_total`: Total number of score computations (labels: status)
- `score_computation_duration_seconds`: Score computation duration
- `score_distribution`: Distribution of credit scores (histogram)

### Oracle Metrics

- `oracle_calls_total`: Total number of oracle calls (labels: oracle_type, status)
- `oracle_call_duration_seconds`: Oracle call duration (labels: oracle_type)

### Error Metrics

- `errors_total`: Total number of errors (labels: error_type, endpoint)

### System Metrics

- `active_requests`: Number of active requests (gauge)
- `app_info`: Application information (version, environment)

### Staking Metrics

- `staking_operations_total`: Total number of staking operations (labels: operation, status)
- `staking_total_amount`: Total amount staked (labels: tier)

## Accessing Metrics

### Endpoint

```
GET /metrics
```

### Example Response

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/api/score",method="POST",status_code="200"} 42.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/api/score",method="POST",le="0.1"} 10.0
http_request_duration_seconds_bucket{endpoint="/api/score",method="POST",le="0.5"} 35.0
http_request_duration_seconds_bucket{endpoint="/api/score",method="POST",le="1.0"} 40.0
```

## Prometheus Configuration

### Basic Scrape Config

```yaml
scrape_configs:
  - job_name: 'AETHER-SCORE'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Grafana Dashboard

A basic Grafana dashboard JSON is available at `grafana/dashboards/AETHER-SCORE.json`.

### Key Panels

1. **Request Rate**: Requests per second by endpoint
2. **Error Rate**: Error rate by endpoint and type
3. **Response Time**: P50, P95, P99 latencies
4. **Blockchain Metrics**: Transaction success rate, gas usage
5. **Score Distribution**: Histogram of credit scores
6. **Active Requests**: Current active request count

## Alerting Rules

See `prometheus/alerts.yml` for alert rule definitions.

### Key Alerts

- High error rate (>10 errors/min)
- Slow response times (P95 > 2s)
- Blockchain RPC failures
- High gas usage

## Best Practices

1. **Label Cardinality**: Keep label values limited to prevent high cardinality
2. **Histogram Buckets**: Adjust buckets based on your latency requirements
3. **Sampling**: Use appropriate sample rates for high-volume endpoints
4. **Retention**: Configure Prometheus retention based on storage capacity

## Integration with Monitoring Stack

- **Prometheus**: Scrape metrics from `/metrics` endpoint
- **Grafana**: Visualize metrics using dashboard JSON
- **Alertmanager**: Route alerts based on Prometheus alert rules
- **Sentry**: Correlate metrics with error tracking


