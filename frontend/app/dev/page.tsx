'use client';

export default function DevPage() {
  const contractAddress = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || '0x...';
  const codeSnippet = `// Install: npm install ethers
import { ethers } from 'ethers';

// Contract interface
const CONTRACT_ADDRESS = '${contractAddress}';
const CONTRACT_ABI = [
  {
    "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
    "name": "getScore",
    "outputs": [
      {"internalType": "uint16", "name": "score", "type": "uint16"},
      {"internalType": "uint8", "name": "riskBand", "type": "uint8"},
      {"internalType": "uint64", "name": "lastUpdated", "type": "uint64"}
    ],
    "stateMutability": "view",
    "type": "function"
  }
];

// Get score for a user
async function getCreditScore(userAddress: string) {
  // Use network config for RPC URL
  const rpcUrl = process.env.NEXT_PUBLIC_QIE_TESTNET_RPC_URL || 'https://rpc1testnet.qie.digital/';
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, provider);
  
  const [score, riskBand, lastUpdated] = await contract.getScore(userAddress);
  
  return {
    score: Number(score),
    riskBand: Number(riskBand),
    lastUpdated: Number(lastUpdated)
  };
}

// Usage
const userScore = await getCreditScore('0x...');
console.log(\`Score: \${userScore.score}, Risk: \${userScore.riskBand}\`);`;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
          Integration Guide
        </h1>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Quick Start
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Integrate AETHER-SCORE into your DeFi protocol in just a few lines of code.
            Read credit scores directly from the QIE blockchain.
          </p>

          <div className="bg-gray-900 rounded-lg p-6 overflow-x-auto">
            <pre className="text-sm text-green-400 font-mono">
              <code>{codeSnippet}</code>
            </pre>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Risk Bands
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 rounded-full text-sm font-semibold">
                Low Risk
              </span>
              <span className="text-gray-600 dark:text-gray-400">riskBand = 1, score â‰¥ 750</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 rounded-full text-sm font-semibold">
                Medium Risk
              </span>
              <span className="text-gray-600 dark:text-gray-400">riskBand = 2, score 500-749</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300 rounded-full text-sm font-semibold">
                High Risk
              </span>
              <span className="text-gray-600 dark:text-gray-400">riskBand = 3, score &lt; 500</span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Use Cases
          </h2>
          <ul className="space-y-3 text-gray-600 dark:text-gray-400">
            <li className="flex items-start gap-2">
              <span className="text-indigo-600 dark:text-indigo-400">âœ“</span>
              <span>Dynamic loan-to-value (LTV) ratios based on credit score</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-600 dark:text-indigo-400">âœ“</span>
              <span>Interest rate adjustments for lending protocols</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-600 dark:text-indigo-400">âœ“</span>
              <span>Collateral requirements optimization</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-600 dark:text-indigo-400">âœ“</span>
              <span>Fraud prevention and risk assessment</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}


