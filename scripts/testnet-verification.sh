#!/bin/bash

# Testnet Verification Script
# Tests all features on testnet before mainnet deployment

set -e

echo "ðŸ§ª AETHER-SCORE Testnet Verification"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# Check environment
echo "ðŸ“‹ Step 1: Checking environment..."
echo ""

if [ -z "$QIE_NETWORK" ]; then
  export QIE_NETWORK=testnet
  echo -e "${YELLOW}âš ï¸  QIE_NETWORK not set, defaulting to testnet${NC}"
fi

if [ "$QIE_NETWORK" != "testnet" ]; then
  echo -e "${RED}âŒ Error: QIE_NETWORK must be 'testnet' for testnet verification${NC}"
  echo "   Current value: $QIE_NETWORK"
  exit 1
fi

echo -e "${GREEN}âœ… Environment: QIE_NETWORK=testnet${NC}"
echo ""

# Check backend is running
echo "ðŸ“‹ Step 2: Checking backend connectivity..."
echo ""

BACKEND_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
  echo -e "${GREEN}âœ… Backend is running at $BACKEND_URL${NC}"
else
  echo -e "${YELLOW}âš ï¸  Backend not accessible at $BACKEND_URL${NC}"
  echo "   Start backend with: cd backend && python -m uvicorn app:app --reload"
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check frontend is running
echo "ðŸ“‹ Step 3: Checking frontend connectivity..."
echo ""

FRONTEND_URL="${NEXT_PUBLIC_FRONTEND_URL:-http://localhost:3000}"
if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
  echo -e "${GREEN}âœ… Frontend is running at $FRONTEND_URL${NC}"
else
  echo -e "${YELLOW}âš ï¸  Frontend not accessible at $FRONTEND_URL${NC}"
  echo "   Start frontend with: cd frontend && npm run dev"
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check RPC connectivity
echo "ðŸ“‹ Step 4: Checking RPC connectivity..."
echo ""

RPC_URL="https://rpc1testnet.qie.digital/"
if curl -s -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  "$RPC_URL" > /dev/null 2>&1; then
  echo -e "${GREEN}âœ… RPC endpoint is accessible: $RPC_URL${NC}"
else
  echo -e "${RED}âŒ RPC endpoint not accessible: $RPC_URL${NC}"
  ERRORS=$((ERRORS + 1))
fi
echo ""

# Check contract addresses
echo "ðŸ“‹ Step 5: Checking contract addresses..."
echo ""

if [ -f "backend/.env" ]; then
  if grep -q "CREDIT_PASSPORT_NFT_ADDRESS=" backend/.env && ! grep -q "CREDIT_PASSPORT_NFT_ADDRESS=0x0000" backend/.env; then
    echo -e "${GREEN}âœ… CreditPassportNFT address configured${NC}"
  else
    echo -e "${YELLOW}âš ï¸  CreditPassportNFT address not configured${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
else
  echo -e "${YELLOW}âš ï¸  backend/.env not found${NC}"
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo "=================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}âœ… Testnet verification passed!${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Test all features manually on testnet"
  echo "  2. Verify network switching works"
  echo "  3. Test error handling"
  echo "  4. Run comprehensive feature tests"
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo -e "${YELLOW}âš ï¸  Verification passed with $WARNINGS warning(s)${NC}"
  exit 0
else
  echo -e "${RED}âŒ Verification failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
  exit 1
fi


