#!/bin/bash
# Generate secrets for environment configuration

set -e

ENVIRONMENT=${1:-development}
OUTPUT_FILE="environments/.env.${ENVIRONMENT}.secrets"

echo "Generating secrets for environment: $ENVIRONMENT"
echo "Output file: $OUTPUT_FILE"

# Generate random secrets
API_KEY_ENCRYPTION_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

cat > "$OUTPUT_FILE" << EOF
# Generated secrets for $ENVIRONMENT environment
# Generated on: $(date)
# IMPORTANT: Keep this file secure and never commit it to version control

# Database
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD

# Security
API_KEY_ENCRYPTION_KEY=$API_KEY_ENCRYPTION_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY

# Blockchain (fill these manually)
BACKEND_PRIVATE_KEY=
CREDIT_PASSPORT_NFT_ADDRESS=

# Monitoring (fill these manually)
SENTRY_DSN_BACKEND=
SENTRY_DSN_FRONTEND=
EOF

chmod 600 "$OUTPUT_FILE"

echo ""
echo "✅ Secrets generated successfully"
echo "📝 Review and update the following in $OUTPUT_FILE:"
echo "   - BACKEND_PRIVATE_KEY"
echo "   - CREDIT_PASSPORT_NFT_ADDRESS"
echo "   - SENTRY_DSN_BACKEND"
echo "   - SENTRY_DSN_FRONTEND"
echo ""
echo "⚠️  Remember to:"
echo "   1. Add $OUTPUT_FILE to .gitignore"
echo "   2. Store secrets securely (use a secrets manager in production)"
echo "   3. Never commit this file to version control"

