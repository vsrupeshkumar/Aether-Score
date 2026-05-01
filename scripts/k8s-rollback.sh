#!/bin/bash
# Kubernetes rollback script for AETHER-SCORE deployments

set -e

NAMESPACE=${1:-AETHER-SCORE-prod}
DEPLOYMENT=${2:-backend}
REVISION=${3:-}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AETHER-SCORE Kubernetes Rollback Script${NC}"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Deployment: $DEPLOYMENT"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${RED}Error: Namespace '$NAMESPACE' not found.${NC}"
    exit 1
fi

# Check if deployment exists
if ! kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" &> /dev/null; then
    echo -e "${RED}Error: Deployment '$DEPLOYMENT' not found in namespace '$NAMESPACE'.${NC}"
    exit 1
fi

# Show rollout history
echo -e "${YELLOW}Rollout History:${NC}"
kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE"
echo ""

# If no revision specified, rollback to previous
if [ -z "$REVISION" ]; then
    echo -e "${YELLOW}Rolling back to previous revision...${NC}"
    kubectl rollout undo deployment/"$DEPLOYMENT" -n "$NAMESPACE"
else
    echo -e "${YELLOW}Rolling back to revision $REVISION...${NC}"
    kubectl rollout undo deployment/"$DEPLOYMENT" --to-revision="$REVISION" -n "$NAMESPACE"
fi

# Wait for rollout to complete
echo -e "${YELLOW}Waiting for rollout to complete...${NC}"
if kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=300s; then
    echo -e "${GREEN}âœ“ Rollback successful!${NC}"
    
    # Show current status
    echo ""
    echo -e "${YELLOW}Current Deployment Status:${NC}"
    kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE"
    echo ""
    
    # Show pods
    echo -e "${YELLOW}Pod Status:${NC}"
    kubectl get pods -l app="$DEPLOYMENT" -n "$NAMESPACE"
    echo ""
    
    # Show current revision
    CURRENT_REVISION=$(kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE" | grep "^\s*[0-9]" | head -1 | awk '{print $1}')
    echo -e "${GREEN}Current revision: $CURRENT_REVISION${NC}"
else
    echo -e "${RED}âœ— Rollback failed or timed out!${NC}"
    echo ""
    echo -e "${YELLOW}Debugging information:${NC}"
    kubectl describe deployment "$DEPLOYMENT" -n "$NAMESPACE" | tail -20
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
    exit 1
fi


