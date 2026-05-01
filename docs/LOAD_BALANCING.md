# Load Balancing Guide

This guide explains how to configure load balancing for AETHER-SCORE backend instances.

## Overview

Load balancing distributes incoming requests across multiple backend instances to improve performance, availability, and scalability.

## Health Checks

The backend provides health check endpoints for load balancers:

- **Liveness Check**: `GET /health`
  - Returns 200 if the service is running
  - Use for basic health monitoring
  
- **Readiness Check**: `GET /health/ready`
  - Returns 200 if all dependencies are healthy
  - Returns 503 if any critical dependency is unavailable
  - Use for load balancer health checks

### Health Check Configuration

```yaml
# Example: Nginx upstream configuration
upstream AETHER-SCORE_backend {
    least_conn;  # Use least connections algorithm
    
    server backend1:4000 max_fails=3 fail_timeout=30s;
    server backend2:4000 max_fails=3 fail_timeout=30s;
    server backend3:4000 max_fails=3 fail_timeout=30s;
    
    # Health check
    health_check uri=/health/ready interval=10s;
}
```

## Load Balancer Setup

### Nginx

```nginx
upstream AETHER-SCORE_backend {
    least_conn;
    server backend1:4000;
    server backend2:4000;
    server backend3:4000;
}

server {
    listen 80;
    server_name api.AETHER-SCORE.io;
    
    location / {
        proxy_pass http://AETHER-SCORE_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout http_503;
    }
    
    location /health {
        access_log off;
        proxy_pass http://AETHER-SCORE_backend;
    }
}
```

### AWS Application Load Balancer (ALB)

1. **Target Group Configuration**:
   - Health check path: `/health/ready`
   - Health check interval: 30 seconds
   - Healthy threshold: 2
   - Unhealthy threshold: 3
   - Timeout: 5 seconds

2. **Listener Rules**:
   - Forward to target group
   - Enable sticky sessions if needed (for WebSocket support)

### Render / Railway

Both platforms provide built-in load balancing:

1. **Render**:
   - Enable "Auto-Deploy" for multiple instances
   - Configure health check path: `/health/ready`
   - Set instance count in dashboard

2. **Railway**:
   - Use Railway's built-in load balancer
   - Configure health checks in service settings
   - Scale horizontally by increasing replica count

## Session Affinity (Sticky Sessions)

If you need WebSocket support or session persistence:

```nginx
upstream AETHER-SCORE_backend {
    ip_hash;  # Sticky sessions based on IP
    server backend1:4000;
    server backend2:4000;
    server backend3:4000;
}
```

**Note**: Sticky sessions reduce load distribution efficiency. Only enable if necessary.

## SSL Termination

Terminate SSL at the load balancer for better performance:

```nginx
server {
    listen 443 ssl http2;
    server_name api.AETHER-SCORE.io;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://AETHER-SCORE_backend;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

## Monitoring

Monitor load balancer metrics:

- Request distribution across instances
- Health check success/failure rates
- Response times per instance
- Error rates

Use Prometheus metrics endpoint (`/metrics`) to track backend performance.

## Best Practices

1. **Health Checks**: Use `/health/ready` for load balancer health checks
2. **Timeouts**: Set appropriate timeouts (5-10 seconds)
3. **Retries**: Configure retry logic for failed requests
4. **Monitoring**: Monitor both load balancer and backend metrics
5. **Scaling**: Scale based on CPU, memory, and request queue length

## Troubleshooting

### Backend Not Receiving Traffic

1. Check health check endpoint: `curl http://backend:4000/health/ready`
2. Verify backend is listening on correct port
3. Check firewall rules
4. Review load balancer logs

### Uneven Traffic Distribution

1. Check backend instance health
2. Verify load balancing algorithm (round-robin, least-conn, etc.)
3. Review session affinity settings
4. Check for slow instances

### High Latency

1. Monitor backend response times
2. Check database connection pool
3. Review Redis cache performance
4. Verify network latency between load balancer and backends


