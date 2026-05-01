'use client';

import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { getExplorerTxUrl, getNetworkConfig } from '@/lib/config/network';
import { useMainnetWarning } from '@/app/hooks/useMainnetWarning';

const STAKING_ABI = [
  "function stake(uint256 amount) external",
  "function unstake(uint256 amount) external",
  "function integrationTier(address user) view returns (uint8)",
  "function stakedAmount(address user) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)"
];

const ERC20_ABI = [
  "function balanceOf(address owner) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
  "function allowance(address owner, address spender) view returns (uint256)",
  "function decimals() view returns (uint8)"
];

interface QIEStakingProps {
  address: string | null;
  provider: ethers.BrowserProvider | null;
}

export default function QIEStaking({ address, provider }: QIEStakingProps) {
  const [stakedAmount, setStakedAmount] = useState<string>('0');
  const [tier, setTier] = useState<number>(0);
  const [ncrdBalance, setNcrdBalance] = useState<string>('0');
  const [stakeAmount, setStakeAmount] = useState<string>('');
  const [unstakeAmount, setUnstakeAmount] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);

  const stakingAddress = process.env.NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS;
  const ncrdTokenAddress = process.env.NEXT_PUBLIC_NCRD_TOKEN_ADDRESS;

  const tierInfo = {
    0: { name: 'None', icon: 'âšª', color: 'from-gray-500 to-gray-600', boost: 0, threshold: 0 },
    1: { name: 'Bronze', icon: 'ðŸ¥‰', color: 'from-amber-500 to-orange-500', boost: 50, threshold: 500 },
    2: { name: 'Silver', icon: 'ðŸ¥ˆ', color: 'from-gray-400 to-gray-500', boost: 150, threshold: 2000 },
    3: { name: 'Gold', icon: 'ðŸ¥‡', color: 'from-yellow-400 to-amber-500', boost: 300, threshold: 10000 }
  };

  useEffect(() => {
    if (address && provider && stakingAddress) {
      loadStakingInfo();
    }
  }, [address, provider, stakingAddress]);

  const loadStakingInfo = async () => {
    if (!address || !provider) return;

    // Check if staking contract is configured
    if (!stakingAddress || stakingAddress === '0x' || stakingAddress.startsWith('0xYour') || stakingAddress.length !== 42) {
      // Silently handle unconfigured contract - this is expected
      setStakedAmount('0');
      setTier(0);
      return;
    }

    try {
      // Verify contract exists at address
      const code = await provider.getCode(stakingAddress);
      if (code === '0x' || code === '0x0') {
        // Silently handle undeployed contract - this is expected
        setStakedAmount('0');
        setTier(0);
        return;
      }

      const stakingContract = new ethers.Contract(stakingAddress, STAKING_ABI, provider);
      
      // Try to call methods with error handling
      let staked = 0n;
      let tierValue = 0;
      
      try {
        const result = await Promise.all([
          stakingContract.stakedAmount(address),
          stakingContract.integrationTier(address)
        ]);
        staked = result[0];
        tierValue = Number(result[1]);
      } catch (contractError: any) {
        // If contract call fails (method doesn't exist or returns empty), use defaults
        // Suppress console errors for expected failures (contract not deployed, BAD_DATA)
        if (contractError.code !== 'BAD_DATA' && !contractError.message?.includes('could not decode')) {
          // Only log unexpected errors
          console.warn('Contract method call failed:', contractError.message);
        }
        staked = 0n;
        tierValue = 0;
      }

      setStakedAmount(ethers.formatEther(staked));
      setTier(tierValue);

      if (ncrdTokenAddress && ncrdTokenAddress !== '0x' && !ncrdTokenAddress.startsWith('0xYour')) {
        try {
          const tokenCode = await provider.getCode(ncrdTokenAddress);
          if (tokenCode !== '0x' && tokenCode !== '0x0') {
            const tokenContract = new ethers.Contract(ncrdTokenAddress, ERC20_ABI, provider);
            const balance = await tokenContract.balanceOf(address);
            const decimals = await tokenContract.decimals();
            setNcrdBalance(ethers.formatUnits(balance, decimals));
          }
        } catch (tokenError) {
          console.warn('Error loading NCRD balance:', tokenError);
          setNcrdBalance('0');
        }
      }
    } catch (error: any) {
      console.error('Error loading staking info:', error);
      // Set defaults on error
      setStakedAmount('0');
      setTier(0);
    }
  };

  const { requireMainnetConfirmation } = useMainnetWarning();

  const handleStake = async () => {
    if (!address || !provider || !stakingAddress || !stakeAmount) return;

    // Verify network before transaction
    try {
      const network = await provider.getNetwork();
      const networkConfig = getNetworkConfig();
      if (network.chainId !== networkConfig.chainId) {
        throw new Error(`Wrong network! Expected ${networkConfig.name} (Chain ID: ${networkConfig.chainId.toString()}), but connected to Chain ID: ${network.chainId.toString()}.`);
      }
    } catch (error: any) {
      alert(`Network Error: ${error.message}\n\nPlease switch to the correct network before proceeding.`);
      return;
    }

    // Require mainnet confirmation
    const confirmed = await requireMainnetConfirmation(
      'Stake NCRD tokens',
      `Amount: ${stakeAmount} NCRD`
    );
    if (!confirmed) {
      return;
    }

    // Prevent double-submission
    if (isLoading) {
      console.warn('Transaction already in progress, ignoring duplicate request');
      return;
    }

    setIsLoading(true);
    let txHash: string | null = null;
    
    try {
      // Verify provider is still connected
      if (!provider || !address) {
        throw new Error('Wallet disconnected. Please reconnect and try again.');
      }
      
      // Validate stake amount
      const stakeAmountNum = parseFloat(stakeAmount);
      if (isNaN(stakeAmountNum) || stakeAmountNum <= 0) {
        throw new Error('Invalid stake amount. Please enter a positive number.');
      }
      
      const signer = await provider.getSigner();
      const stakingContract = new ethers.Contract(stakingAddress, STAKING_ABI, signer);
      const amount = ethers.parseEther(stakeAmount);

      if (ncrdTokenAddress) {
        const tokenContract = new ethers.Contract(ncrdTokenAddress, ERC20_ABI, signer);
        const allowance = await tokenContract.allowance(address, stakingAddress);
        if (allowance < amount) {
          const approveTx = await tokenContract.approve(stakingAddress, amount);
          await approveTx.wait();
        }
      }

      const tx = await stakingContract.stake(amount);
      txHash = tx.hash;
      setTxHash(txHash);
      console.log('Stake transaction submitted:', txHash);
      
      // Wait for confirmation with timeout (5 minutes)
      const TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes
      const confirmationPromise = tx.wait();
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Transaction confirmation timeout. Check your wallet for transaction status.')), TIMEOUT_MS)
      );
      
      await Promise.race([confirmationPromise, timeoutPromise]);
      
      setStakeAmount('');
      // Verify provider is still connected before loading info
      if (provider && address) {
        await loadStakingInfo();
      }
    } catch (error: any) {
      console.error('Error staking:', error);
      
      let errorMessage = error?.message || 'Unknown error occurred';
      
      // Check if transaction was submitted but confirmation failed
      if (txHash) {
        errorMessage = `Transaction submitted (${txHash.slice(0, 10)}...) but confirmation failed. `;
        errorMessage += 'Please check your wallet for transaction status.';
        if (error?.message) {
          errorMessage += ` Error: ${error.message}`;
        }
      } else if (error?.code === 4001) {
        errorMessage = 'Transaction rejected by user.';
      }
      
      alert(`Error staking: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnstake = async () => {
    if (!address || !provider || !stakingAddress || !unstakeAmount) return;

    // Verify network before transaction
    try {
      const network = await provider.getNetwork();
      const networkConfig = getNetworkConfig();
      if (network.chainId !== networkConfig.chainId) {
        throw new Error(`Wrong network! Expected ${networkConfig.name} (Chain ID: ${networkConfig.chainId.toString()}), but connected to Chain ID: ${network.chainId.toString()}.`);
      }
    } catch (error: any) {
      alert(`Network Error: ${error.message}\n\nPlease switch to the correct network before proceeding.`);
      return;
    }

    // Require mainnet confirmation
    const confirmed = await requireMainnetConfirmation(
      'Unstake NCRD tokens',
      `Amount: ${unstakeAmount} NCRD`
    );
    if (!confirmed) {
      return;
    }

    // Prevent double-submission
    if (isLoading) {
      console.warn('Transaction already in progress, ignoring duplicate request');
      return;
    }

    setIsLoading(true);
    let txHash: string | null = null;
    
    try {
      // Verify provider is still connected
      if (!provider || !address) {
        throw new Error('Wallet disconnected. Please reconnect and try again.');
      }
      
      // Validate unstake amount
      const unstakeAmountNum = parseFloat(unstakeAmount);
      if (isNaN(unstakeAmountNum) || unstakeAmountNum <= 0) {
        throw new Error('Invalid unstake amount. Please enter a positive number.');
      }
      
      const signer = await provider.getSigner();
      const stakingContract = new ethers.Contract(stakingAddress, STAKING_ABI, signer);
      const amount = ethers.parseEther(unstakeAmount);

      const tx = await stakingContract.unstake(amount);
      txHash = tx.hash;
      setTxHash(txHash);
      console.log('Unstake transaction submitted:', txHash);
      
      // Wait for confirmation with timeout (5 minutes)
      const TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes
      const confirmationPromise = tx.wait();
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Transaction confirmation timeout. Check your wallet for transaction status.')), TIMEOUT_MS)
      );
      
      await Promise.race([confirmationPromise, timeoutPromise]);
      
      setUnstakeAmount('');
      // Verify provider is still connected before loading info
      if (provider && address) {
        await loadStakingInfo();
      }
    } catch (error: any) {
      console.error('Error unstaking:', error);
      
      let errorMessage = error?.message || 'Unknown error occurred';
      
      // Check if transaction was submitted but confirmation failed
      if (txHash) {
        errorMessage = `Transaction submitted (${txHash.slice(0, 10)}...) but confirmation failed. `;
        errorMessage += 'Please check your wallet for transaction status.';
        if (error?.message) {
          errorMessage += ` Error: ${error.message}`;
        }
      } else if (error?.code === 4001) {
        errorMessage = 'Transaction rejected by user.';
      }
      
      alert(`Error unstaking: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const stakedNum = parseFloat(stakedAmount);
  const currentTier = tierInfo[tier as keyof typeof tierInfo];
  const nextTier = tier < 3 ? tierInfo[(tier + 1) as keyof typeof tierInfo] : null;
  const progressToNext = nextTier ? Math.min((stakedNum / nextTier.threshold) * 100, 100) : 100;

  if (!address) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <p className="text-text-secondary">
          Connect your wallet to view staking options.
        </p>
      </div>
    );
  }

  // Check if staking contract is configured
  const isStakingConfigured = stakingAddress && 
    stakingAddress !== '0x' && 
    !stakingAddress.startsWith('0xYour') &&
    stakingAddress.length === 42;

  if (!isStakingConfigured) {
    return (
      <div className="glass rounded-xl p-8 text-center space-y-4">
        <div className="text-6xl mb-4">âš ï¸</div>
        <h2 className="text-2xl font-bold mb-2">Staking Contract Not Configured</h2>
        <p className="text-text-secondary mb-4">
          The staking contract address is not set. To use staking features:
        </p>
        <div className="text-left bg-white/5 rounded-lg p-4 max-w-2xl mx-auto">
          <p className="text-sm text-text-secondary mb-2">1. Deploy AETHER-SCOREStaking contract (or use existing deployment)</p>
          <p className="text-sm text-text-secondary mb-2">2. Add to <code className="bg-white/10 px-2 py-1 rounded">frontend/.env.local</code>:</p>
          <pre className="bg-black/20 p-3 rounded text-xs overflow-x-auto">
{`NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0xYourStakingAddress
NEXT_PUBLIC_NCRD_TOKEN_ADDRESS=0xYourNCRDTokenAddress`}
          </pre>
          <p className="text-sm text-text-secondary mt-4">
            <strong>Note:</strong> Staking is optional. You can still use other features like credit scoring and lending.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Tier Display with Ring */}
      <div className="glass rounded-2xl p-8 text-center">
        <div className="relative w-48 h-48 mx-auto mb-6">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
            {/* Background circle */}
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke="rgba(255, 255, 255, 0.1)"
              strokeWidth="12"
            />
            {/* Progress circle */}
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke={`url(#tierGradient-${tier})`}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 80}`}
              strokeDashoffset={`${2 * Math.PI * 80 * (1 - progressToNext / 100)}`}
              className="transition-all duration-1000"
            />
            <defs>
              <linearGradient id="tierGradient-0" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#6b7280" />
                <stop offset="100%" stopColor="#4b5563" />
              </linearGradient>
              <linearGradient id="tierGradient-1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#f59e0b" />
                <stop offset="100%" stopColor="#f97316" />
              </linearGradient>
              <linearGradient id="tierGradient-2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#9ca3af" />
                <stop offset="100%" stopColor="#6b7280" />
              </linearGradient>
              <linearGradient id="tierGradient-3" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#eab308" />
                <stop offset="100%" stopColor="#f59e0b" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-5xl mb-2">{currentTier.icon}</div>
            <div className={`text-2xl font-bold bg-gradient-to-r ${currentTier.color} bg-clip-text text-transparent`}>
              {currentTier.name}
            </div>
            {currentTier.boost > 0 && (
              <div className="text-sm text-green-400 mt-1">+{currentTier.boost} boost</div>
            )}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-center glass rounded-lg p-4">
            <span className="text-text-secondary">Staked Amount</span>
            <span className="font-mono font-bold text-white text-lg">{stakedAmount} NCRD</span>
          </div>
          {ncrdTokenAddress && (
            <div className="flex justify-between items-center glass rounded-lg p-4">
              <span className="text-text-secondary">Available Balance</span>
              <span className="font-mono font-semibold text-white">{ncrdBalance} NCRD</span>
            </div>
          )}
          {nextTier && (
            <div className="glass rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-text-secondary text-sm">Progress to {nextTier.name}</span>
                <span className="text-sm font-semibold text-white">{progressToNext.toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r ${nextTier.color} rounded-full transition-all duration-1000`}
                  style={{ width: `${progressToNext}%` }}
                />
              </div>
              <p className="text-xs text-text-muted mt-2">
                Need {(nextTier.threshold - stakedNum).toFixed(2)} more NCRD for {nextTier.name} tier
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Stake/Unstake Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Stake */}
        <div className="glass rounded-xl p-6">
          <h3 className="font-semibold mb-4 text-white">Stake NCRD</h3>
          <div className="space-y-3">
            <input
              type="number"
              value={stakeAmount}
              onChange={(e) => setStakeAmount(e.target.value)}
              placeholder="Amount to stake"
              className="w-full px-4 py-3 glass rounded-lg text-white placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              disabled={isLoading}
            />
            <button
              onClick={handleStake}
              disabled={isLoading || !stakeAmount}
              className="w-full btn-gradient px-6 py-3 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Staking...' : 'Stake'}
            </button>
          </div>
        </div>

        {/* Unstake */}
        <div className="glass rounded-xl p-6">
          <h3 className="font-semibold mb-4 text-white">Unstake NCRD</h3>
          <div className="space-y-3">
            <input
              type="number"
              value={unstakeAmount}
              onChange={(e) => setUnstakeAmount(e.target.value)}
              placeholder="Amount to unstake"
              className="w-full px-4 py-3 glass rounded-lg text-white placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-red-500/50"
              disabled={isLoading}
            />
            <button
              onClick={handleUnstake}
              disabled={isLoading || !unstakeAmount}
              className="w-full px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg font-semibold border border-red-500/30 hover:border-red-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? 'Unstaking...' : 'Unstake'}
            </button>
          </div>
        </div>
      </div>

      {/* Transaction Hash */}
      {txHash && (
        <div className="glass rounded-lg p-4 border border-green-500/30 animate-fade-in">
          <p className="text-sm text-green-400">
            Transaction: <a 
              href={getExplorerTxUrl(txHash)} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="underline hover:text-green-300"
            >
              {txHash.slice(0, 10)}...{txHash.slice(-8)}
            </a>
          </p>
        </div>
      )}

      {/* Tier Benefits */}
      <div className="glass rounded-xl p-6">
        <h3 className="font-semibold mb-4 text-white">Tier Benefits</h3>
        <div className="grid md:grid-cols-3 gap-4">
          {[1, 2, 3].map((t) => {
            const info = tierInfo[t as keyof typeof tierInfo];
            return (
              <div 
                key={t}
                className={`glass-hover rounded-lg p-4 border ${tier >= t ? `border-${info.color.split(' ')[1]}/30` : 'border-white/10'}`}
              >
                <div className="text-3xl mb-2">{info.icon}</div>
                <div className={`font-semibold mb-1 bg-gradient-to-r ${info.color} bg-clip-text text-transparent`}>
                  {info.name}
                </div>
                <div className="text-sm text-text-secondary mb-2">
                  {info.threshold.toLocaleString()} NCRD
                </div>
                <div className="text-xs text-green-400 font-semibold">
                  +{info.boost} score boost
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

