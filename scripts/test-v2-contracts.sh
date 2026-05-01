#!/bin/bash
# Test V2 contract interactions

set -e

cd "$(dirname "$0")/.."

echo "ðŸ§ª Testing V2 Contract Interactions"
echo "==================================="
echo ""

# Test wallet address
WALLET="0x3e7716bee2d7e923cb9b572eb169edfb6cdbdab6"
CONTRACT="0x34904952E5269290B783071f1eBba51c22ef6219"
STAKING="0x3E9943694a37d26987C1af36DE169e631b30F153"

echo "ðŸ“‹ Test Configuration:"
echo "  Wallet: $WALLET"
echo "  CreditPassportNFTV2: $CONTRACT"
echo "  AETHER-SCOREStakingV2: $STAKING"
echo ""

# Test 1: Check if backend can read contract
echo "1ï¸âƒ£  Testing Backend Contract Connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   âœ“ Backend is running"
    
    # Test score generation
    echo ""
    echo "2ï¸âƒ£  Testing Score Generation..."
    RESPONSE=$(curl -s -X POST "http://localhost:8000/api/score" \
        -H "Content-Type: application/json" \
        -d "{\"walletAddress\": \"$WALLET\"}" 2>&1)
    
    if echo "$RESPONSE" | grep -q "score"; then
        echo "   âœ“ Score generation successful"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -15 || echo "$RESPONSE" | head -5
    else
        echo "   âš  Score generation response:"
        echo "$RESPONSE" | head -5
    fi
else
    echo "   âš  Backend not running. Start with: cd backend && python -m uvicorn app:app --reload"
fi

echo ""
echo "3ï¸âƒ£  Testing Staking Contract..."
if curl -s "http://localhost:8000/api/staking/$WALLET" > /dev/null 2>&1; then
    STAKING_RESPONSE=$(curl -s "http://localhost:8000/api/staking/$WALLET")
    if echo "$STAKING_RESPONSE" | grep -q "stakedAmount\|tier"; then
        echo "   âœ“ Staking info retrieved"
        echo "$STAKING_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STAKING_RESPONSE"
    else
        echo "   âš  Staking response: $STAKING_RESPONSE"
    fi
else
    echo "   âš  Staking endpoint not available"
fi

echo ""
echo "âœ… Contract tests complete!"
echo ""
echo "Next: Test in frontend UI at http://localhost:3000"


