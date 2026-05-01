/**
 * Test fixtures and helper data
 */

export const testAddresses = {
  user1: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0',
  user2: '0x8ba1f109551bD432803012645Hac136c22C1729',
};

export const testScores = {
  high: { score: 850, riskBand: 1 },
  medium: { score: 600, riskBand: 2 },
  low: { score: 300, riskBand: 3 },
};

export const mockApiResponses = {
  scoreGeneration: {
    address: testAddresses.user1,
    score: 750,
    baseScore: 700,
    riskBand: 1,
    explanation: 'Low risk: High transaction activity',
    transactionHash: '0x' + 'a'.repeat(64),
  },
  chatResponse: {
    response: 'Hello! I can help you with a loan.',
    loanOffer: null,
  },
};

