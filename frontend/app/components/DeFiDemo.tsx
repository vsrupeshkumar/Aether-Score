'use client';

import { useState, useEffect } from 'react';
import { ethers } from 'ethers';

const DEMO_LENDER_ABI = [
  "function getLTV(address user) view returns (uint256)",
  "function calculateMaxBorrow(address user, uint256 collateralValue) view returns (uint256)"
];

interface DeFiDemoProps {
  address: string | null;
  provider: ethers.BrowserProvider | null;
  score: number | null;
  riskBand: number | null;
}

export default function DeFiDemo({ address, provider, score, riskBand }: DeFiDemoProps) {
  const [collateralValue, setCollateralValue] = useState<number>(1000);
  const [maxBorrow, setMaxBorrow] = useState<number>(0);
  const [ltvBps, setLtvBps] = useState<number>(0);
  const [interestRate, setInterestRate] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);

  const lenderAddress = process.env.NEXT_PUBLIC_DEMO_LENDER_ADDRESS;

  useEffect(() => {
    if (address && lenderAddress && provider) {
      loadLTV();
    } else if (score !== null && riskBand !== null) {
      calculateFromScore();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [address, lenderAddress, provider, score, riskBand, collateralValue]);

  const loadLTV = async () => {
    if (!address || !provider) return;

    // Check if lender contract is configured
    if (!lenderAddress || lenderAddress === '0x' || lenderAddress.startsWith('0xYour') || lenderAddress.length !== 42) {
      // Silently handle unconfigured contract - use score-based calculation
      if (score !== null && riskBand !== null) {
        calculateFromScore();
      }
      return;
    }

    setIsLoading(true);
    try {
      // Verify contract exists at address
      const code = await provider.getCode(lenderAddress);
      if (code === '0x' || code === '0x0') {
        // Silently handle undeployed contract - use score-based calculation
        if (score !== null && riskBand !== null) {
          calculateFromScore();
        }
        setIsLoading(false);
        return;
      }

      const lenderContract = new ethers.Contract(lenderAddress, DEMO_LENDER_ABI, provider);
      
      try {
        const ltv = await lenderContract.getLTV(address);
        const ltvValue = Number(ltv);
        setLtvBps(ltvValue);

        const collateralWei = ethers.parseEther(collateralValue.toString());
        const maxBorrowWei = await lenderContract.calculateMaxBorrow(address, collateralWei);
        setMaxBorrow(Number(ethers.formatEther(maxBorrowWei)));

        calculateInterestRate(ltvValue);
      } catch (contractError: any) {
        // If contract method fails (doesn't exist or returns empty), fall back to score-based
        // Suppress console errors for expected failures (contract not deployed, BAD_DATA)
        if (contractError.code !== 'BAD_DATA' && !contractError.message?.includes('could not decode')) {
          // Only log unexpected errors
          console.warn('Contract method call failed:', contractError.message);
        }
        if (score !== null && riskBand !== null) {
          calculateFromScore();
        }
      }
    } catch (error: any) {
      // Suppress expected errors (BAD_DATA, could not decode) - these are normal when contracts aren't deployed
      if (error.code !== 'BAD_DATA' && !error.message?.includes('could not decode')) {
        console.error('Error loading LTV:', error);
      }
      // Fall back to score-based calculation
      if (score !== null && riskBand !== null) {
        calculateFromScore();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const calculateFromScore = () => {
    if (score === null || riskBand === null) return;

    const ltvMap: { [key: number]: number } = {
      1: 7000,
      2: 5000,
      3: 3000,
      0: 0
    };

    const ltv = ltvMap[riskBand] || 0;
    setLtvBps(ltv);
    setMaxBorrow((collateralValue * ltv) / 10000);
    calculateInterestRate(ltv);
  };

  const calculateInterestRate = (ltv: number) => {
    if (riskBand === 1) {
      setInterestRate(5 + (7000 - ltv) / 1000);
    } else if (riskBand === 2) {
      setInterestRate(8 + (5000 - ltv) / 1000);
    } else if (riskBand === 3) {
      setInterestRate(12 + (3000 - ltv) / 1000);
    } else {
      setInterestRate(20);
    }
  };

  const riskBandInfo = {
    1: { name: 'Low Risk', color: 'from-green-400 to-emerald-500', bg: 'bg-green-500/10', border: 'border-green-500/30' },
    2: { name: 'Medium Risk', color: 'from-amber-400 to-yellow-500', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
    3: { name: 'High Risk', color: 'from-rose-400 to-red-500', bg: 'bg-rose-500/10', border: 'border-rose-500/30' },
    0: { name: 'Unknown', color: 'from-gray-400 to-gray-500', bg: 'bg-gray-500/10', border: 'border-gray-500/30' }
  };

  const currentRisk = riskBand !== null ? riskBandInfo[riskBand as keyof typeof riskBandInfo] : riskBandInfo[0];
  const ltvPercent = ltvBps / 100;
  const circumference = Math.PI * 100;
  const strokeDashoffset = circumference - (ltvPercent / 100) * circumference;

  return (
    <div className="space-y-6">
      {/* Score & Risk Display */}
      {score !== null && riskBand !== null && (
        <div className="glass rounded-xl p-6 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm mb-1">Credit Score</p>
              <p className="text-3xl font-bold text-white font-mono">{score}</p>
              <p className="text-text-muted text-xs mt-1">/ 1000</p>
            </div>
            <div className={`px-4 py-2 rounded-lg border ${currentRisk.bg} ${currentRisk.border}`}>
              <p className="text-text-secondary text-xs mb-1">Risk Band</p>
              <p className={`font-semibold bg-gradient-to-r ${currentRisk.color} bg-clip-text text-transparent`}>
                {currentRisk.name}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Collateral Slider */}
      <div className="glass rounded-xl p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold text-white">Collateral Value</h3>
          <p className="text-2xl font-bold font-mono gradient-text">
            ${collateralValue.toLocaleString()}
          </p>
        </div>
        <input
          type="range"
          min="100"
          max="100000"
          step="100"
          value={collateralValue}
          onChange={(e) => setCollateralValue(Number(e.target.value))}
          className="w-full h-3 bg-white/5 rounded-lg appearance-none cursor-pointer slider-gradient"
          style={{
            background: `linear-gradient(to right, 
              rgb(0, 212, 255) 0%, 
              rgb(124, 58, 237) ${(collateralValue / 100000) * 100}%, 
              rgba(255, 255, 255, 0.1) ${(collateralValue / 100000) * 100}%
            )`
          }}
        />
        <div className="flex justify-between text-xs text-text-muted mt-2">
          <span>$100</span>
          <span>$100,000</span>
        </div>
      </div>

      {/* LTV Visualization */}
      {!isLoading && ltvBps > 0 && (
        <div className="glass rounded-xl p-8">
          <h3 className="font-semibold text-center mb-6 text-white">Loan-to-Value Ratio</h3>
          <div className="relative w-64 h-32 mx-auto mb-6">
            <svg className="w-full h-full" viewBox="0 0 200 120">
              <defs>
                <linearGradient id="ltvGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#00d4ff" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="rgba(255, 255, 255, 0.1)"
                strokeWidth="12"
                strokeLinecap="round"
              />
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="url(#ltvGradient)"
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-1000"
                style={{
                  transform: 'rotate(180deg)',
                  transformOrigin: '100px 100px',
                  filter: 'drop-shadow(0 0 10px rgba(0, 212, 255, 0.5))'
                }}
              />
              <text
                x="100"
                y="75"
                textAnchor="middle"
                className="text-4xl font-bold fill-white font-mono"
              >
                {ltvPercent.toFixed(0)}%
              </text>
              <text
                x="100"
                y="95"
                textAnchor="middle"
                className="text-sm fill-text-secondary"
              >
                LTV
              </text>
            </svg>
          </div>
        </div>
      )}

      {/* Results Grid */}
      {isLoading ? (
        <div className="glass rounded-xl p-12 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          <p className="mt-4 text-text-secondary">Loading...</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Max Borrowable */}
          <div className="glass-hover rounded-xl p-6 border border-green-500/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="text-3xl">💰</div>
              <h3 className="font-semibold text-white">Max Borrowable</h3>
            </div>
            <p className="text-4xl font-bold font-mono text-green-400 mb-2">
              ${maxBorrow.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </p>
            <p className="text-xs text-text-secondary">
              Based on ${collateralValue.toLocaleString()} collateral
            </p>
          </div>

          {/* Interest Rate */}
          <div className="glass-hover rounded-xl p-6 border border-purple-500/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="text-3xl">📈</div>
              <h3 className="font-semibold text-white">Interest Rate</h3>
            </div>
            <p className="text-4xl font-bold font-mono text-purple-400 mb-2">
              {interestRate.toFixed(2)}%
            </p>
            <p className="text-xs text-text-secondary">
              Annual percentage yield (APY)
            </p>
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="glass rounded-xl p-6">
        <h3 className="font-semibold mb-4 text-white">How It Works</h3>
        <div className="space-y-3 text-sm text-text-secondary">
          <div className="flex items-start gap-3">
            <span className="text-cyan-400 mt-0.5">→</span>
            <span>Higher credit scores unlock higher LTV ratios (up to 70%)</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-cyan-400 mt-0.5">→</span>
            <span>Lower risk bands receive better interest rates</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-cyan-400 mt-0.5">→</span>
            <span>Staking NCRD tokens can boost your score and improve terms</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-cyan-400 mt-0.5">→</span>
            <span>This is a demo - actual lending requires collateral deposit</span>
          </div>
        </div>
      </div>
    </div>
  );
}
