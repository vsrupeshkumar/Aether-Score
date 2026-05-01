#!/bin/bash
# Rollback all AETHER-SCORE services

set -e

NAMESPACE=${1:-AETHER-SCORE-prod}
ROLLBACK_REVISION=${2:-}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Rolling back all AETHER-SCORE services${NC}"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo ""

# Services to rollback (in order)
SERVICES=("backend" "frontend" "worker")

for service in "${SERVICES[@]}"; do
    echo -e "${YELLOW}Rolling back $service...${NC}"
    
    if [ -z "$ROLLBACK_REVISION" ]; then
        ./scripts/k8s-rollback.sh "$NAMESPACE" "$service"
    else
        ./scripts/k8s-rollback.sh "$NAMESPACE" "$service" "$ROLLBACK_REVISION"
    fi
    
    echo ""
done

echo -e "${GREEN}âœ“ All services rolled back successfully!${NC}"

# Verify health
echo ""
echo -e "${YELLOW}Verifying service health...${NC}"
sleep 5

# Check backend health
if curl -f https://api.AETHER-SCORE.io/health &> /dev/null; then
    echo -e "${GREEN}âœ“ Backend health check passed${NC}"
else
    echo -e "${YELLOW}âš  Backend health check failed (may need more time)${NC}"
fi

# Check frontend
if curl -f https://AETHER-SCORE.io &> /dev/null; then
    echo -e "${GREEN}âœ“ Frontend is accessible${NC}"
else
    echo -e "${YELLOW}âš  Frontend check failed (may need more time)${NC}"
fi


