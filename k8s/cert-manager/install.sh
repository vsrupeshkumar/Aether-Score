#!/bin/bash
# Install Cert-Manager for SSL certificate management

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Cert-Manager...${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if helm is available (optional, for Helm installation)
if command -v helm &> /dev/null; then
    echo -e "${YELLOW}Helm detected. Using Helm installation...${NC}"
    
    # Add cert-manager Helm repo
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Install cert-manager
    helm install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --set installCRDs=true \
        --set global.leaderElection.namespace=cert-manager \
        --wait
    
    echo -e "${GREEN}Cert-Manager installed via Helm!${NC}"
else
    echo -e "${YELLOW}Helm not found. Using kubectl installation...${NC}"
    
    # Install cert-manager CRDs
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.crds.yaml
    
    # Create cert-manager namespace
    kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
    
    # Add cert-manager Helm repo (for manifest download)
    helm repo add jetstack https://charts.jetstack.io || true
    helm repo update || true
    
    # Install cert-manager using kubectl
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    echo -e "${YELLOW}Waiting for cert-manager to be ready...${NC}"
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/instance=cert-manager \
        -n cert-manager \
        --timeout=300s
    
    echo -e "${GREEN}Cert-Manager installed via kubectl!${NC}"
fi

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
kubectl get pods -n cert-manager

echo -e "${GREEN}Cert-Manager installation complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create ClusterIssuer: kubectl apply -f k8s/overlays/prod/cluster-issuer.yaml"
echo "2. Create Certificate: kubectl apply -f k8s/overlays/prod/certificate.yaml"
echo "3. Verify certificate: kubectl get certificate -n AETHER-SCORE-prod"


