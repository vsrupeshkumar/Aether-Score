#!/bin/bash

# Network Abstraction Verification Script
# Checks for hardcoded network values that should be in config files

set -e

echo "🔍 Verifying Network Abstraction"
echo "=================================="
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check for hardcoded chain IDs
echo "Checking for hardcoded chain IDs (1983, 1990)..."
echo ""

# Exclude config files, test files, documentation, and build artifacts
CHAIN_ID_1983=$(grep -r "1983" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=build \
  --exclude="*test*" --exclude="*Test*" \
  backend/ frontend/ contracts/ 2>/dev/null | \
  grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
  grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | \
  grep -v "migrations" | wc -l | tr -d ' ')

CHAIN_ID_1990=$(grep -r "1990" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=build \
  --exclude="*test*" --exclude="*Test*" \
  backend/ frontend/ contracts/ 2>/dev/null | \
  grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
  grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | \
  grep -v "deploy-mainnet" | grep -v "verify-mainnet" | wc -l | tr -d ' ')

if [ "$CHAIN_ID_1983" -gt 0 ]; then
  echo -e "${YELLOW}⚠️  Found $CHAIN_ID_1983 potential hardcoded references to chain ID 1983${NC}"
  echo "   Review these files:"
  grep -r "1983" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude="*test*" --exclude="*Test*" \
    backend/ frontend/ contracts/ 2>/dev/null | \
    grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
    grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | head -5
  WARNINGS=$((WARNINGS + 1))
fi

if [ "$CHAIN_ID_1990" -gt 0 ]; then
  echo -e "${YELLOW}⚠️  Found $CHAIN_ID_1990 potential hardcoded references to chain ID 1990${NC}"
  echo "   Review these files:"
  grep -r "1990" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude="*test*" --exclude="*Test*" \
    backend/ frontend/ contracts/ 2>/dev/null | \
    grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
    grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | head -5
  WARNINGS=$((WARNINGS + 1))
fi

# Check for hardcoded RPC URLs
echo ""
echo "Checking for hardcoded RPC URLs..."
echo ""

RPC_TESTNET=$(grep -r "rpc1testnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=build \
  --exclude="*test*" --exclude="*Test*" \
  backend/ frontend/ contracts/ 2>/dev/null | \
  grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
  grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | wc -l | tr -d ' ')

RPC_MAINNET=$(grep -r "rpc1mainnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=build \
  --exclude="*test*" --exclude="*Test*" \
  backend/ frontend/ contracts/ 2>/dev/null | \
  grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
  grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | wc -l | tr -d ' ')

if [ "$RPC_TESTNET" -gt 0 ]; then
  echo -e "${RED}❌ Found $RPC_TESTNET hardcoded testnet RPC URLs${NC}"
  echo "   These should use network config:"
  grep -r "rpc1testnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude="*test*" --exclude="*Test*" \
    backend/ frontend/ contracts/ 2>/dev/null | \
    grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
    grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | head -5
  ERRORS=$((ERRORS + 1))
fi

if [ "$RPC_MAINNET" -gt 0 ]; then
  echo -e "${RED}❌ Found $RPC_MAINNET hardcoded mainnet RPC URLs${NC}"
  echo "   These should use network config:"
  grep -r "rpc1mainnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude="*test*" --exclude="*Test*" \
    backend/ frontend/ contracts/ 2>/dev/null | \
    grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
    grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | head -5
  ERRORS=$((ERRORS + 1))
fi

# Check for hardcoded explorer URLs
echo ""
echo "Checking for hardcoded explorer URLs..."
echo ""

EXPLORER_TESTNET=$(grep -r "testnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=build \
  --exclude="*test*" --exclude="*Test*" \
  backend/ frontend/ contracts/ 2>/dev/null | \
  grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
  grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | \
  grep -v "deploy-all" | grep -v "verify-deployment" | wc -l | tr -d ' ')

EXPLORER_MAINNET=$(grep -r "mainnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=build \
  --exclude="*test*" --exclude="*Test*" \
  backend/ frontend/ contracts/ 2>/dev/null | \
  grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
  grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | \
  grep -v "deploy-mainnet" | grep -v "verify-mainnet" | wc -l | tr -d ' ')

if [ "$EXPLORER_TESTNET" -gt 0 ]; then
  echo -e "${RED}❌ Found $EXPLORER_TESTNET hardcoded testnet explorer URLs${NC}"
  echo "   These should use network config:"
  grep -r "testnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude="*test*" --exclude="*Test*" \
    backend/ frontend/ contracts/ 2>/dev/null | \
    grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
    grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | head -5
  ERRORS=$((ERRORS + 1))
fi

if [ "$EXPLORER_MAINNET" -gt 0 ]; then
  echo -e "${RED}❌ Found $EXPLORER_MAINNET hardcoded mainnet explorer URLs${NC}"
  echo "   These should use network config:"
  grep -r "mainnet.qie.digital" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__ \
    --exclude-dir=.git --exclude="*test*" --exclude="*Test*" \
    backend/ frontend/ contracts/ 2>/dev/null | \
    grep -v "config/network" | grep -v "lib/config/network" | grep -v "hardhat.config" | \
    grep -v ".md" | grep -v "MAINNET" | grep -v "TESTNET" | head -5
  ERRORS=$((ERRORS + 1))
fi

# Verify network config files exist
echo ""
echo "Verifying network config files..."
echo ""

if [ ! -f "backend/config/network.py" ]; then
  echo -e "${RED}❌ Missing backend/config/network.py${NC}"
  ERRORS=$((ERRORS + 1))
else
  echo -e "${GREEN}✅ backend/config/network.py exists${NC}"
fi

if [ ! -f "frontend/lib/config/network.ts" ]; then
  echo -e "${RED}❌ Missing frontend/lib/config/network.ts${NC}"
  ERRORS=$((ERRORS + 1))
else
  echo -e "${GREEN}✅ frontend/lib/config/network.ts exists${NC}"
fi

if [ ! -f "contracts/hardhat.config.ts" ]; then
  echo -e "${RED}❌ Missing contracts/hardhat.config.ts${NC}"
  ERRORS=$((ERRORS + 1))
else
  echo -e "${GREEN}✅ contracts/hardhat.config.ts exists${NC}"
fi

# Summary
echo ""
echo "=================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}✅ Network abstraction verification passed!${NC}"
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo -e "${YELLOW}⚠️  Verification passed with $WARNINGS warning(s)${NC}"
  exit 0
else
  echo -e "${RED}❌ Verification failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
  exit 1
fi

