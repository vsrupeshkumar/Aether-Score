#!/bin/bash
# Blue-Green Deployment Script for AETHER-SCORE
# This script performs zero-downtime deployments by switching traffic between blue and green environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-AETHER-SCORE-prod}
DEPLOYMENT_NAME=${DEPLOYMENT_NAME:-backend}
SERVICE_NAME=${SERVICE_NAME:-backend}
IMAGE_TAG=${IMAGE_TAG:-latest}
HEALTH_CHECK_URL=${HEALTH_CHECK_URL:-http://localhost:4000/health}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}  # 5 minutes
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Determine current active deployment (blue or green)
get_active_deployment() {
    local selector=$(kubectl get svc ${SERVICE_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "")
    if [ "$selector" == "blue" ]; then
        echo "blue"
    elif [ "$selector" == "green" ]; then
        echo "green"
    else
        echo "blue"  # Default to blue if not set
    fi
}

# Get inactive deployment
get_inactive_deployment() {
    local active=$(get_active_deployment)
    if [ "$active" == "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Deploy new version to inactive environment
deploy_inactive() {
    local target=$(get_inactive_deployment)
    local deployment="${DEPLOYMENT_NAME}-${target}"
    
    echo -e "${YELLOW}Deploying to ${target} environment...${NC}"
    
    # Update deployment with new image
    kubectl set image deployment/${deployment} \
        app=AETHER-SCORE-backend:${IMAGE_TAG} \
        -n ${NAMESPACE} \
        --record
    
    # Wait for rollout
    echo -e "${YELLOW}Waiting for ${target} deployment to be ready...${NC}"
    kubectl rollout status deployment/${deployment} -n ${NAMESPACE} --timeout=${HEALTH_CHECK_TIMEOUT}s
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Deployment to ${target} failed!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}${target} deployment is ready!${NC}"
    return 0
}

# Run health checks on deployment
health_check() {
    local target=$(get_inactive_deployment)
    local deployment="${DEPLOYMENT_NAME}-${target}"
    
    echo -e "${YELLOW}Running health checks on ${target}...${NC}"
    
    # Get pod name
    local pod_name=$(kubectl get pods -n ${NAMESPACE} -l app=AETHER-SCORE-backend,version=${target} -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        echo -e "${RED}No pod found for ${target} deployment!${NC}"
        return 1
    fi
    
    # Port forward and check health
    kubectl port-forward pod/${pod_name} 4000:4000 -n ${NAMESPACE} > /dev/null 2>&1 &
    local pf_pid=$!
    sleep 2
    
    # Check health endpoint
    local health_status=$(curl -s -o /dev/null -w "%{http_code}" ${HEALTH_CHECK_URL} || echo "000")
    kill $pf_pid 2>/dev/null || true
    
    if [ "$health_status" == "200" ]; then
        echo -e "${GREEN}Health check passed for ${target}!${NC}"
        return 0
    else
        echo -e "${RED}Health check failed for ${target} (status: ${health_status})!${NC}"
        return 1
    fi
}

# Switch traffic to new deployment
switch_traffic() {
    local target=$(get_inactive_deployment)
    
    echo -e "${YELLOW}Switching traffic to ${target}...${NC}"
    
    # Update service selector
    kubectl patch svc ${SERVICE_NAME} -n ${NAMESPACE} -p '{"spec":{"selector":{"version":"'${target}'"}}}'
    
    echo -e "${GREEN}Traffic switched to ${target}!${NC}"
    
    # Wait a bit and verify
    sleep 5
    echo -e "${YELLOW}Verifying traffic switch...${NC}"
    
    local current=$(get_active_deployment)
    if [ "$current" == "$target" ]; then
        echo -e "${GREEN}Traffic successfully switched to ${target}!${NC}"
        return 0
    else
        echo -e "${RED}Traffic switch verification failed!${NC}"
        return 1
    fi
}

# Rollback to previous deployment
rollback() {
    local previous=$(get_active_deployment)
    local current=$(get_inactive_deployment)
    
    echo -e "${RED}Rolling back to ${previous}...${NC}"
    
    # Switch traffic back
    kubectl patch svc ${SERVICE_NAME} -n ${NAMESPACE} -p '{"spec":{"selector":{"version":"'${previous}'"}}}'
    
    echo -e "${GREEN}Rolled back to ${previous}!${NC}"
}

# Cleanup old deployment (optional)
cleanup_old() {
    local old=$(get_inactive_deployment)
    local deployment="${DEPLOYMENT_NAME}-${old}"
    
    echo -e "${YELLOW}Cleaning up old ${old} deployment...${NC}"
    
    # Scale down old deployment
    kubectl scale deployment/${deployment} --replicas=0 -n ${NAMESPACE}
    
    echo -e "${GREEN}Old ${old} deployment scaled down!${NC}"
}

# Main deployment flow
main() {
    echo -e "${GREEN}Starting blue-green deployment...${NC}"
    echo -e "Active deployment: $(get_active_deployment)"
    echo -e "Target deployment: $(get_inactive_deployment)"
    echo -e "Image tag: ${IMAGE_TAG}"
    echo ""
    
    # Step 1: Deploy to inactive environment
    if ! deploy_inactive; then
        echo -e "${RED}Deployment failed!${NC}"
        exit 1
    fi
    
    # Step 2: Health checks
    if ! health_check; then
        echo -e "${RED}Health checks failed!${NC}"
        if [ "$ROLLBACK_ON_FAILURE" == "true" ]; then
            rollback
        fi
        exit 1
    fi
    
    # Step 3: Switch traffic
    if ! switch_traffic; then
        echo -e "${RED}Traffic switch failed!${NC}"
        if [ "$ROLLBACK_ON_FAILURE" == "true" ]; then
            rollback
        fi
        exit 1
    fi
    
    # Step 4: Monitor for issues (optional)
    echo -e "${YELLOW}Monitoring for 30 seconds...${NC}"
    sleep 30
    
    # Step 5: Cleanup old deployment (optional, commented out by default)
    # cleanup_old
    
    echo -e "${GREEN}Blue-green deployment completed successfully!${NC}"
    echo -e "Active deployment: $(get_active_deployment)"
}

# Run main function
main "$@"


