#!/bin/bash
# Environment variable validation script

set -e

ENVIRONMENT=${1:-development}
ENV_FILE="environments/.env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

echo "Validating environment: $ENVIRONMENT"
echo "Loading variables from: $ENV_FILE"

# Source the environment file
set -a
source "$ENV_FILE"
set +a

# Required variables
REQUIRED_VARS=(
    "ENVIRONMENT"
    "DATABASE_URL"
    "REDIS_URL"
    "QIE_RPC_URL"
    "CREDIT_PASSPORT_NFT_ADDRESS"
    "BACKEND_PRIVATE_KEY"
)

# Optional but recommended variables
RECOMMENDED_VARS=(
    "SENTRY_DSN_BACKEND"
    "SENTRY_DSN_FRONTEND"
    "API_KEY_ENCRYPTION_KEY"
    "JWT_SECRET_KEY"
)

# Check required variables
echo ""
echo "Checking required variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        echo "  ❌ $var is missing"
    else
        echo "  ✅ $var is set"
    fi
done

# Check recommended variables
echo ""
echo "Checking recommended variables..."
for var in "${RECOMMENDED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "  ⚠️  $var is not set (recommended)"
    else
        echo "  ✅ $var is set"
    fi
done

# Validate specific values
echo ""
echo "Validating values..."

# Check DATABASE_URL format
if [[ ! "$DATABASE_URL" =~ ^postgresql\+asyncpg:// ]]; then
    echo "  ⚠️  DATABASE_URL should start with 'postgresql+asyncpg://'"
fi

# Check REDIS_URL format
if [[ ! "$REDIS_URL" =~ ^redis:// ]]; then
    echo "  ⚠️  REDIS_URL should start with 'redis://'"
fi

# Check environment value
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "  ❌ ENVIRONMENT must be one of: development, staging, production"
    MISSING_VARS+=("ENVIRONMENT")
fi

# Check wallet address format
if [[ ! "$CREDIT_PASSPORT_NFT_ADDRESS" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
    echo "  ⚠️  CREDIT_PASSPORT_NFT_ADDRESS should be a valid Ethereum address"
fi

# Check private key format
if [[ ! "$BACKEND_PRIVATE_KEY" =~ ^0x[a-fA-F0-9]{64}$ ]] && [[ ! "$BACKEND_PRIVATE_KEY" =~ ^[a-fA-F0-9]{64}$ ]]; then
    echo "  ⚠️  BACKEND_PRIVATE_KEY should be a valid private key"
fi

# Summary
echo ""
if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo "✅ All required variables are set"
    exit 0
else
    echo "❌ Missing required variables: ${MISSING_VARS[*]}"
    exit 1
fi

