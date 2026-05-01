#!/bin/bash
# Test V2 contract integration

set -e

echo "ðŸ§ª Testing AETHER-SCORE V2 Contract Integration"
echo "============================================"

cd "$(dirname "$0")/.."

# Check environment variables
echo ""
echo "ðŸ“‹ Checking environment variables..."
echo ""

if [ -f "backend/.env" ]; then
    echo "Backend .env found"
    grep -q "CREDIT_PASSPORT_NFT_ADDRESS=0x34904952E5269290B783071f1eBba51c22ef6219" backend/.env && echo "  âœ“ CREDIT_PASSPORT_NFT_ADDRESS set" || echo "  âœ— CREDIT_PASSPORT_NFT_ADDRESS not set correctly"
    grep -q "STAKING_ADDRESS=0x3E9943694a37d26987C1af36DE169e631b30F153" backend/.env && echo "  âœ“ STAKING_ADDRESS set" || echo "  âœ— STAKING_ADDRESS not set correctly"
else
    echo "  âœ— Backend .env not found"
fi

if [ -f "frontend/.env.local" ]; then
    echo "Frontend .env.local found"
    grep -q "NEXT_PUBLIC_CONTRACT_ADDRESS=0x34904952E5269290B783071f1eBba51c22ef6219" frontend/.env.local && echo "  âœ“ NEXT_PUBLIC_CONTRACT_ADDRESS set" || echo "  âœ— NEXT_PUBLIC_CONTRACT_ADDRESS not set correctly"
    grep -q "NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0x3E9943694a37d26987C1af36DE169e631b30F153" frontend/.env.local && echo "  âœ“ NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS set" || echo "  âœ— NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS not set correctly"
else
    echo "  âœ— Frontend .env.local not found"
fi

# Check ABIs
echo ""
echo "ðŸ“„ Checking ABIs..."
echo ""

[ -f "backend/abis/CreditPassportNFTV2.json" ] && echo "  âœ“ CreditPassportNFTV2.json" || echo "  âœ— CreditPassportNFTV2.json missing"
[ -f "backend/abis/AETHER-SCOREStakingV2.json" ] && echo "  âœ“ AETHER-SCOREStakingV2.json" || echo "  âœ— AETHER-SCOREStakingV2.json missing"
[ -f "backend/abis/LendingVaultV2.json" ] && echo "  âœ“ LendingVaultV2.json" || echo "  âœ— LendingVaultV2.json missing"

[ -f "frontend/abis/CreditPassportNFTV2.json" ] && echo "  âœ“ Frontend CreditPassportNFTV2.json" || echo "  âœ— Frontend CreditPassportNFTV2.json missing"

# Test contract connectivity (if backend is running)
echo ""
echo "ðŸ”— Testing contract connectivity..."
echo ""

if command -v curl &> /dev/null; then
    API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo "  âœ“ Backend is running"
        echo "  â†’ Test score generation: curl $API_URL/api/score/0x3e7716bee2d7e923cb9b572eb169edfb6cdbdab6"
    else
        echo "  âš  Backend not running (start with: cd backend && python -m uvicorn app:app --reload)"
    fi
else
    echo "  âš  curl not available, skipping connectivity test"
fi

echo ""
echo "âœ… Integration check complete!"
echo ""
echo "Next steps:"
echo "  1. Start backend: cd backend && python -m uvicorn app:app --reload"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Test score generation in the UI"
echo "  4. Test staking functionality"
echo ""


