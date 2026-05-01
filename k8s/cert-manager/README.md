# Cert-Manager Setup for AETHER-SCORE

This directory contains scripts and documentation for setting up automated SSL certificate management using Cert-Manager and Let's Encrypt.

## Prerequisites

- Kubernetes cluster with admin access
- kubectl configured to access your cluster
- Helm (optional, but recommended)
- Ingress controller (nginx-ingress) installed
- DNS records pointing to your cluster's ingress IP

## Installation

### Option 1: Using Helm (Recommended)

```bash
./k8s/cert-manager/install.sh
```

### Option 2: Manual Installation

```bash
# Install CRDs
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.crds.yaml

# Create namespace
kubectl create namespace cert-manager

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
```

## Configuration

### 1. Create ClusterIssuer

The ClusterIssuer defines how cert-manager will obtain certificates from Let's Encrypt.

```bash
kubectl apply -f k8s/overlays/prod/cluster-issuer.yaml
```

**Important:** Update the email address in `cluster-issuer.yaml` before applying.

### 2. Create Certificate Resource

The Certificate resource defines which domains should have certificates.

```bash
kubectl apply -f k8s/overlays/prod/certificate.yaml
```

### 3. Update Ingress

Ensure your Ingress resource has the cert-manager annotation:

```yaml
annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
```

The ingress should already be configured in `k8s/base/ingress.yaml`.

## Verification

### Check Cert-Manager Pods

```bash
kubectl get pods -n cert-manager
```

All pods should be in `Running` state.

### Check ClusterIssuer

```bash
kubectl get clusterissuer
```

Should show `letsencrypt-prod` and `letsencrypt-staging` as `Ready`.

### Check Certificate Status

```bash
kubectl get certificate -n AETHER-SCORE-prod
kubectl describe certificate AETHER-SCORE-tls -n AETHER-SCORE-prod
```

The certificate should show `Ready` status once issued.

### Check Certificate Secret

```bash
kubectl get secret AETHER-SCORE-tls -n AETHER-SCORE-prod
```

The secret should be created automatically by cert-manager.

## Troubleshooting

### Certificate Not Issuing

1. Check certificate status:
   ```bash
   kubectl describe certificate AETHER-SCORE-tls -n AETHER-SCORE-prod
   ```

2. Check certificate request:
   ```bash
   kubectl get certificaterequest -n AETHER-SCORE-prod
   kubectl describe certificaterequest <name> -n AETHER-SCORE-prod
   ```

3. Check challenge status:
   ```bash
   kubectl get challenge -n AETHER-SCORE-prod
   kubectl describe challenge <name> -n AETHER-SCORE-prod
   ```

### Common Issues

- **DNS not configured**: Ensure DNS records point to your ingress IP
- **Ingress not accessible**: Verify ingress controller is running and accessible
- **Rate limiting**: Let's Encrypt has rate limits. Use staging issuer for testing
- **Email not set**: Update email in ClusterIssuer before applying

## Auto-Renewal

Cert-manager automatically renews certificates 30 days before expiration. No manual intervention is required.

## Staging vs Production

- **Staging issuer** (`letsencrypt-staging`): Use for testing, higher rate limits
- **Production issuer** (`letsencrypt-prod`): Use for production, stricter rate limits

Switch between issuers by updating the `issuerRef` in the Certificate resource.

## Additional Resources

- [Cert-Manager Documentation](https://cert-manager.io/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [HTTP-01 Challenge](https://cert-manager.io/docs/configuration/acme/http01/)


