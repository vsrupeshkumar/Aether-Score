#!/bin/bash
# Environment setup script

set -e

ENVIRONMENT=${1:-development}

if [[ ! "$ENVIRONMENT" =~ ^(dev|development|staging|prod|production)$ ]]; then
    echo "Error: Invalid environment. Use: dev, staging, or prod"
    exit 1
fi

# Normalize environment name
case "$ENVIRONMENT" in
    dev|development)
        ENV_NAME="dev"
        ENV_FULL="development"
        ;;
    staging)
        ENV_NAME="staging"
        ENV_FULL="staging"
        ;;
    prod|production)
        ENV_NAME="prod"
        ENV_FULL="production"
        ;;
esac

echo "Setting up environment: $ENV_FULL"

# Check if .env file exists
ENV_FILE="environments/.env.${ENV_NAME}"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE from template..."
    cp "environments/.env.${ENV_NAME}.example" "$ENV_FILE"
    echo "✅ Created $ENV_FILE"
    echo "⚠️  Please update the values in $ENV_FILE"
fi

# Generate secrets if needed
SECRETS_FILE="environments/.env.${ENV_NAME}.secrets"
if [ ! -f "$SECRETS_FILE" ]; then
    echo "Generating secrets..."
    ./scripts/generate-secrets.sh "$ENV_NAME"
fi

# Validate environment
echo ""
echo "Validating environment configuration..."
./scripts/validate-env.sh "$ENV_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Environment setup complete!"
    echo ""
    echo "To use this environment:"
    echo "  export ENVIRONMENT=$ENV_FULL"
    echo "  source $ENV_FILE"
    echo "  source $SECRETS_FILE"
else
    echo ""
    echo "❌ Environment validation failed"
    echo "Please fix the issues above and run this script again"
    exit 1
fi

