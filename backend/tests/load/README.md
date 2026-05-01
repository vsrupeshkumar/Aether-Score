# Load Testing

Load testing for AETHER-SCORE API using Locust.

## Setup

```bash
cd backend
pip install locust
```

## Running Load Tests

### Basic Test

```bash
locust -f tests/load/test_api_load.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to start the test.

### Command Line Test

```bash
# Run with 100 users, spawn rate 10, run for 5 minutes
locust -f tests/load/test_api_load.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### High Load Test (1000+ concurrent)

```bash
# Run with 1000 users, spawn rate 50
locust -f tests/load/test_api_load.py \
  --host=http://localhost:8000 \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m \
  --headless \
  --html=load_test_report.html
```

## Test Scenarios

- **Health Check**: Most common request (3x weight)
- **Get Score**: Read existing score (2x weight)
- **Generate Score**: Create new score (1x weight, requires auth)
- **Staking Info**: Get staking data (1x weight)
- **Oracle Price**: Get oracle price (1x weight)

## Performance Targets

- **Response Time**: < 500ms for 95th percentile
- **Error Rate**: < 1%
- **Throughput**: > 1000 requests/second
- **Concurrent Users**: Support 1000+ concurrent users

## Notes

- Load tests should be run against a test/staging environment
- Ensure rate limiting is properly configured
- Monitor backend resources (CPU, memory, database connections)
- Check for memory leaks under sustained load


