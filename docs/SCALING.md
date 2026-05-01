# Horizontal Scaling Guide

This guide explains how to configure auto-scaling for AETHER-SCORE backend instances.

## Overview

Horizontal scaling allows the system to automatically adjust the number of backend instances based on load, ensuring optimal performance and cost efficiency.

## Auto-Scaling Metrics

Monitor these metrics to trigger scaling:

1. **CPU Usage**: Scale up when >70%, scale down when <30%
2. **Memory Usage**: Scale up when >80%, scale down when <40%
3. **Request Queue Length**: Scale up when queue >100 requests
4. **Response Time (P95)**: Scale up when P95 > 2 seconds
5. **Error Rate**: Scale up when error rate >5%

## Platform-Specific Configuration

### Render

Create `.render.yaml` in the project root:

```yaml
services:
  - type: web
    name: AETHER-SCORE-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
      - key: QIE_RPC_URL
        sync: false
    healthCheckPath: /health/ready
    # Auto-scaling configuration
    scaling:
      minInstances: 2
      maxInstances: 10
      targetCPUPercent: 70
      targetMemoryPercent: 80
```

### Railway

Create `railway.json` in the project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health/ready",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  },
  "scaling": {
    "minInstances": 2,
    "maxInstances": 10,
    "targetCPU": 70,
    "targetMemory": 80
  }
}
```

### AWS ECS / Fargate

Create `ecs-task-definition.json`:

```json
{
  "family": "AETHER-SCORE-backend",
  "cpu": "512",
  "memory": "1024",
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "AETHER-SCORE-backend",
      "image": "AETHER-SCORE/backend:latest",
      "portMappings": [
        {
          "containerPort": 4000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql+asyncpg://..."
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:4000/health/ready || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

Create auto-scaling policy:

```json
{
  "ServiceName": "AETHER-SCORE-backend",
  "ScalableDimension": "ecs:service:DesiredCount",
  "MinCapacity": 2,
  "MaxCapacity": 10,
  "TargetTrackingScalingPolicies": [
    {
      "TargetValue": 70.0,
      "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
      },
      "ScaleInCooldown": 300,
      "ScaleOutCooldown": 60
    },
    {
      "TargetValue": 80.0,
      "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ECSServiceAverageMemoryUtilization"
      },
      "ScaleInCooldown": 300,
      "ScaleOutCooldown": 60
    }
  ]
}
```

### Kubernetes

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: AETHER-SCORE-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: AETHER-SCORE-backend
  template:
    metadata:
      labels:
        app: AETHER-SCORE-backend
    spec:
      containers:
      - name: backend
        image: AETHER-SCORE/backend:latest
        ports:
        - containerPort: 4000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: AETHER-SCORE-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 4000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 4000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: AETHER-SCORE-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: AETHER-SCORE-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

## Scaling Policies

### Conservative (Cost-Optimized)

- **Min Instances**: 1
- **Max Instances**: 5
- **Scale Up**: CPU >80% for 5 minutes
- **Scale Down**: CPU <30% for 15 minutes
- **Use Case**: Development, low traffic

### Balanced (Recommended)

- **Min Instances**: 2
- **Max Instances**: 10
- **Scale Up**: CPU >70% OR Memory >80% OR Queue >100
- **Scale Down**: CPU <40% AND Memory <50% for 10 minutes
- **Use Case**: Production, moderate traffic

### Aggressive (High Performance)

- **Min Instances**: 3
- **Max Instances**: 20
- **Scale Up**: CPU >60% OR Response Time P95 >1s
- **Scale Down**: CPU <50% AND Memory <60% for 20 minutes
- **Use Case**: High traffic, low latency requirements

## Monitoring Scaling

### Prometheus Metrics

Monitor these metrics to track scaling:

```promql
# CPU usage per instance
avg(rate(process_cpu_seconds_total[5m])) * 100

# Memory usage per instance
avg(process_resident_memory_bytes) / 1024 / 1024

# Request queue length
avg(http_requests_in_progress)

# Response time P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Grafana Dashboard

Create a dashboard with:

1. **Current Instances**: Gauge showing active instance count
2. **CPU Usage**: Line chart per instance
3. **Memory Usage**: Line chart per instance
4. **Request Rate**: Line chart showing requests/second
5. **Response Time**: Line chart showing P50, P95, P99
6. **Scaling Events**: Table showing scale up/down events

## Best Practices

1. **Start Small**: Begin with 2-3 instances and scale based on actual load
2. **Monitor Metrics**: Track CPU, memory, response times, and error rates
3. **Set Appropriate Thresholds**: Avoid scaling too aggressively
4. **Use Cooldown Periods**: Prevent rapid scaling oscillations
5. **Test Scaling**: Load test to verify scaling behavior
6. **Database Connection Pooling**: Ensure pool size scales with instances
7. **Redis Connection Pooling**: Configure Redis for multiple connections
8. **Health Checks**: Ensure health checks are fast and accurate

## Troubleshooting

### Instances Not Scaling Up

1. Check scaling policy configuration
2. Verify metrics are being collected
3. Check if max instances limit is reached
4. Review scaling cooldown periods

### Instances Scaling Too Aggressively

1. Increase cooldown periods
2. Adjust scaling thresholds
3. Review metric collection intervals
4. Check for metric spikes or anomalies

### Uneven Load Distribution

1. Verify load balancer configuration
2. Check health check endpoints
3. Review session affinity settings
4. Monitor individual instance metrics

## Cost Optimization

1. **Right-Size Instances**: Use appropriate instance sizes
2. **Scale Down Aggressively**: Reduce instances during low traffic
3. **Reserved Instances**: Use reserved instances for baseline capacity (AWS)
4. **Spot Instances**: Use spot instances for non-critical workloads
5. **Monitor Costs**: Track costs per instance and optimize thresholds


