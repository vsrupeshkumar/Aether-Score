'use client';

import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { Layout } from '@/components/layout/Layout';
import ChatConsole from '@/app/components/ChatConsole';
import ScoreDisplay from '@/app/components/ScoreDisplay';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/GlassCard';
import { Wallet } from 'lucide-react';
import { useWallet } from '@/contexts/WalletContext';
import { getApiUrl } from '@/lib/api';
import { getPrimaryRpcUrl, getNetworkConfig } from '@/lib/config/network';
import { useMainnetWarning } from '@/app/hooks/useMainnetWarning';
const LENDING_VAULT_ADDRESS = process.env.NEXT_PUBLIC_LENDING_VAULT_ADDRESS;

const LENDING_VAULT_ABI = [
  "function createLoan(tuple(address borrower,uint256 amount,uint256 collateralAmount,uint256 interestRate,uint256 duration,uint256 nonce,uint256 expiry) offer, bytes aiSignature) payable returns (uint256)",
  "function getBorrowerLoans(address borrower) view returns (uint256[])",
  "function calculateTotalOwed(uint256 loanId) view returns (uint256)",
  "function repayLoan(uint256 loanId) payable",
  "event LoanCreated(uint256 indexed loanId, address indexed borrower, uint256 amount, uint256 collateralAmount, uint256 interestRate)"
];

export default function LendPage() {
  const { address, provider, isConnected, connect } = useWallet();
  const [score, setScore] = useState<number | null>(null);
  const [riskBand, setRiskBand] = useState<number | null>(null);
  const [explanation, setExplanation] = useState<string>('');
  const [activeLoans, setActiveLoans] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadScore = async (addr: string) => {
    try {
      const response = await fetch(`${getApiUrl()}/api/score/${addr}`);
      if (response.ok) {
        const data = await response.json();
        setScore(data.score);
        setRiskBand(data.riskBand);
        setExplanation(data.explanation || '');
      } else {
        const errorData = await response.json().catch(() => ({ message: response.statusText }));
        console.error('Error loading score:', errorData.message || 'Failed to load score');
      }
    } catch (error: any) {
      console.error('Error loading score:', error);
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('Network error: Unable to connect to backend at', getApiUrl());
      }
    }
  };

  const loadActiveLoans = async (addr: string, prov: any) => {
    if (!LENDING_VAULT_ADDRESS || !prov) return;
    
    // Check if contract address is valid
    if (LENDING_VAULT_ADDRESS === '0x' || LENDING_VAULT_ADDRESS.startsWith('0xYour') || LENDING_VAULT_ADDRESS.length !== 42) {
      // Silently skip if contract not configured
      return;
    }
    
    try {
      // Verify contract exists at address
      const code = await prov.getCode(LENDING_VAULT_ADDRESS);
      if (code === '0x' || code === '0x0') {
        // Silently skip if contract not deployed
        return;
      }
      
      const contract = new ethers.Contract(LENDING_VAULT_ADDRESS, LENDING_VAULT_ABI, prov);
      
      try {
        const loanIds = await contract.getBorrowerLoans(addr);
        
        const loans = await Promise.all(
          loanIds.map(async (id: bigint) => {
            const totalOwed = await contract.calculateTotalOwed(id);
            return {
              id: Number(id),
              totalOwed: ethers.formatEther(totalOwed),
            };
          })
        );
        
        setActiveLoans(loans);
      } catch (contractError: any) {
        // Suppress expected errors (BAD_DATA, could not decode) - these are normal when contracts aren't deployed
        if (contractError.code !== 'BAD_DATA' && !contractError.message?.includes('could not decode')) {
          console.error('Error calling contract methods:', contractError);
        }
        // Set empty loans on error
        setActiveLoans([]);
      }
    } catch (error: any) {
      // Suppress expected errors
      if (error.code !== 'BAD_DATA' && !error.message?.includes('could not decode')) {
        console.error('Error loading loans:', error);
      }
      setActiveLoans([]);
    }
  };

  const { requireMainnetConfirmation } = useMainnetWarning();

  const handleAcceptOffer = async (event: CustomEvent) => {
    const { offer, signature } = event.detail;
    if (!address || !provider || !LENDING_VAULT_ADDRESS) {
      alert('Please connect wallet and ensure LendingVault is configured');
      return;
    }

    if (!signature || typeof signature !== 'string') {
      alert('Error: Invalid signature received from backend. Please try generating a new loan offer.');
      return;
    }

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
    // Safely format BigInt values for display
    const formatAmount = (value: any): string => {
      if (!value) return 'Unknown';
      try {
        // Convert to BigInt if it's a string or number
        const bigIntValue = typeof value === 'bigint' 
          ? value 
          : typeof value === 'string' 
            ? BigInt(value) 
            : BigInt(String(value));
        return ethers.formatEther(bigIntValue);
      } catch (error) {
        console.error('Error formatting amount:', error);
        return 'Unknown';
      }
    };
    
    const loanAmount = formatAmount(offer.amount);
    const collateralAmount = formatAmount(offer.collateralAmount);
    const confirmed = await requireMainnetConfirmation(
      'Create loan',
      `Loan amount: ${loanAmount} QIEV3\nCollateral: ${collateralAmount} QIEV3`
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
      
      // Check if provider is responsive before proceeding
      try {
        await provider.getBlockNumber();
      } catch (rpcError: any) {
        // If RPC is having issues, try using a fallback provider
        console.warn('Primary RPC endpoint having issues, attempting fallback...', rpcError);
        const fallbackRpcUrl = getPrimaryRpcUrl();
        const fallbackProvider = new ethers.JsonRpcProvider(fallbackRpcUrl);
        
        // Test fallback provider
        try {
          await fallbackProvider.getBlockNumber();
          // Use MetaMask signer but with fallback provider for read operations
          const signer = await provider.getSigner();
          // Create contract with signer (signer will use MetaMask for signing, but we can read from fallback)
          const contract = new ethers.Contract(LENDING_VAULT_ADDRESS, LENDING_VAULT_ABI, signer);
          
          // Continue with transaction using signer (MetaMask will handle the actual RPC calls)
          // But first, let's try the original provider one more time with a delay
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (fallbackError) {
          throw new Error(
            'RPC endpoint is currently unavailable. Please try again in a few moments. ' +
            'If the issue persists, check your network connection or try switching to a different RPC endpoint in MetaMask.'
          );
        }
      }
      
      const signer = await provider.getSigner();
      const contract = new ethers.Contract(LENDING_VAULT_ADDRESS, LENDING_VAULT_ABI, signer);
      
      // Normalize signature: ensure it has "0x" prefix and is a valid hex string
      // Backend returns signature without "0x" prefix, so we need to add it
      let normalizedSignature = signature.trim();
      
      // Remove any existing "0x" prefix to avoid duplication
      if (normalizedSignature.startsWith('0x') || normalizedSignature.startsWith('0X')) {
        normalizedSignature = normalizedSignature.slice(2);
      }
      
      // Validate it's a valid hex string (only hex characters)
      if (!/^[a-fA-F0-9]+$/.test(normalizedSignature)) {
        throw new Error(`Invalid signature format: contains non-hexadecimal characters. Signature length: ${normalizedSignature.length}`);
      }
      
      // Validate signature length (should be 128 hex chars = 64 bytes for r+s, or 130 = 65 bytes with v)
      // EIP-712 signatures are typically 65 bytes (130 hex chars) = 32 bytes r + 32 bytes s + 1 byte v
      if (normalizedSignature.length !== 128 && normalizedSignature.length !== 130) {
        throw new Error(`Invalid signature length: expected 128 or 130 hex characters, got ${normalizedSignature.length}`);
      }
      
      // Add "0x" prefix for ethers.js
      normalizedSignature = `0x${normalizedSignature}`;
      
      // Convert signature to bytes - ethers.js Contract accepts hex strings for bytes parameters
      // We'll pass the normalized hex string directly, as ethers will handle the conversion
      if (!ethers.isHexString(normalizedSignature)) {
        throw new Error('Signature is not a valid hex string after normalization');
      }
      
      // Verify signature length (should be 130 hex chars with 0x = 65 bytes for EIP-712)
      const signatureBytes = ethers.getBytes(normalizedSignature);
      if (signatureBytes.length !== 65) {
        console.warn(`Signature length is ${signatureBytes.length} bytes, expected 65. Proceeding anyway.`);
      }
      
      // Ensure offer values are properly formatted
      // For ethers.js v6, we can pass BigInt directly, but ensure all values are properly converted
      const formattedOffer = {
        borrower: offer.borrower || address,
        amount: typeof offer.amount === 'bigint' ? offer.amount : BigInt(String(offer.amount || 0)),
        collateralAmount: typeof offer.collateralAmount === 'bigint' ? offer.collateralAmount : BigInt(String(offer.collateralAmount || 0)),
        interestRate: typeof offer.interestRate === 'bigint' ? offer.interestRate : BigInt(String(offer.interestRate || 0)),
        duration: typeof offer.duration === 'bigint' ? offer.duration : BigInt(String(offer.duration || 0)),
        nonce: typeof offer.nonce === 'bigint' ? offer.nonce : BigInt(String(offer.nonce || 0)),
        expiry: typeof offer.expiry === 'bigint' ? offer.expiry : BigInt(String(offer.expiry || 0)),
      };
      
      // Pass signature as hex string - ethers.js will convert it to bytes
      // The contract expects bytes, and ethers.js Contract methods accept hex strings for bytes parameters
      const tx = await contract.createLoan(formattedOffer, normalizedSignature, {
        value: formattedOffer.collateralAmount,
      });
      
      txHash = tx.hash;
      console.log('Transaction submitted:', txHash);
      
      // Wait for confirmation with timeout (5 minutes)
      const TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes
      const confirmationPromise = tx.wait();
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Transaction confirmation timeout. Check your wallet for transaction status.')), TIMEOUT_MS)
      );
      
      await Promise.race([confirmationPromise, timeoutPromise]);
      
      // Verify provider is still connected before loading loans
      if (provider && address) {
        await loadActiveLoans(address, provider);
        alert('Loan created successfully! Check your wallet.');
      } else {
        alert('Loan transaction submitted. Please reconnect wallet to view loan status.');
      }
    } catch (error: any) {
      console.error('Error creating loan:', error);
      
      // Provide user-friendly error messages for RPC issues
      let errorMessage = 'Unknown error occurred';
      
      // Check if transaction was submitted but confirmation failed
      if (txHash) {
        errorMessage = `Transaction submitted (${txHash.slice(0, 10)}...) but confirmation failed. `;
        errorMessage += 'Please check your wallet for transaction status. ';
        if (error?.message) {
          errorMessage += `Error: ${error.message}`;
        }
      } else if (error?.code === -32002 || error?.message?.includes('RPC endpoint returned too many errors')) {
        errorMessage = 'The blockchain RPC endpoint is currently experiencing issues. Please wait a moment and try again. If the problem persists, try:\n\n1. Refreshing the page\n2. Checking your internet connection\n3. Switching to a different RPC endpoint in MetaMask';
      } else if (error?.code === 'UNKNOWN_ERROR' || error?.message?.includes('could not coalesce')) {
        errorMessage = 'Network error: Unable to connect to the blockchain. The RPC endpoint may be temporarily unavailable. Please try again in a few moments.';
      } else if (error?.code === 4001) {
        errorMessage = 'Transaction rejected by user.';
      } else if (error?.reason) {
        errorMessage = error.reason;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      alert(`Error creating loan: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleAccept = (e: Event) => handleAcceptOffer(e as CustomEvent);
    window.addEventListener('acceptOffer', handleAccept);
    return () => window.removeEventListener('acceptOffer', handleAccept);
  }, [address, provider]);

  // Load score and loans when wallet is connected
  useEffect(() => {
    if (address && provider) {
      loadScore(address);
      loadActiveLoans(address, provider);
    }
  }, [address, provider]);

  return (
    <Layout>
      <div className="min-h-screen px-8 lg:px-16 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gradient mb-2">NeuroLend: AI-Negotiated Lending</h1>
            <p className="text-muted-foreground">Chat with AI to get personalized loan terms based on your AETHER-SCORE score</p>
          </div>

          {!isConnected ? (
            <div className="max-w-md mx-auto">
              <GlassCard className="text-center p-12">
                <div className="text-6xl mb-6">ðŸ’¬</div>
                <h2 className="text-2xl font-bold mb-4 gradient-text">Connect Your Wallet</h2>
                <p className="text-muted-foreground mb-8">
                  Connect your wallet to start chatting with NeuroLend AI
                </p>
                <Button onClick={connect} variant="glow" size="lg">
                  <Wallet className="w-5 h-5" />
                  Connect Wallet
                </Button>
              </GlassCard>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Score & Active Loans */}
              <div className="space-y-6">
                {/* Score Display */}
                {score !== null && (
                  <ScoreDisplay
                    score={score}
                    riskBand={riskBand || 0}
                    explanation={explanation}
                  />
                )}

                {/* Active Loans */}
                {activeLoans.length > 0 && (
                  <GlassCard>
                    <h2 className="text-xl font-bold mb-4">Active Loans</h2>
                    <div className="space-y-3">
                      {activeLoans.map((loan) => (
                        <div key={loan.id} className="glass-hover rounded-lg p-4 border border-border/50">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">
                              Loan #{loan.id}
                            </span>
                            <span className="font-mono font-semibold">
                              {loan.totalOwed} QIE
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </GlassCard>
                )}
              </div>

              {/* Right Column: Chat Console */}
              <div className="lg:col-span-2">
                <div className="h-[600px]">
                  <ChatConsole address={address} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

