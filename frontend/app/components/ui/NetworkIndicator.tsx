'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, CheckCircle2, Network } from 'lucide-react';
import { getNetworkConfig, isMainnet, getNetworkConfigForWallet } from '@/lib/config/network';
import { useWallet } from '@/app/contexts/WalletContext';

export function NetworkIndicator() {
  const [currentChainId, setCurrentChainId] = useState<bigint | null>(null);
  const { provider, isCorrectNetwork: contextIsCorrectNetwork, switchToNetwork } = useWallet();
  const networkConfig = getNetworkConfig();
  const isMainnetMode = isMainnet(networkConfig);

  // Use context value if available, otherwise check locally
  const isCorrectNetwork = contextIsCorrectNetwork !== undefined ? contextIsCorrectNetwork : true;

  useEffect(() => {
    const checkNetwork = async () => {
      if (!provider) {
        setCurrentChainId(null);
        return;
      }

      try {
        const network = await provider.getNetwork();
        setCurrentChainId(network.chainId);
      } catch (error) {
        console.error('Error checking network:', error);
      }
    };

    checkNetwork();
    
    // Listen for chain changes
    if (typeof window !== 'undefined' && window.ethereum) {
      const handleChainChanged = () => {
        checkNetwork();
      };
      
      window.ethereum.on('chainChanged', handleChainChanged);
      return () => {
        window.ethereum?.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, [provider, networkConfig.chainId]);

  const handleSwitchNetwork = async () => {
    if (switchToNetwork) {
      await switchToNetwork();
    } else {
      // Fallback if switchToNetwork not available
      if (typeof window === 'undefined' || !window.ethereum) {
        alert('Please install MetaMask or QIE Wallet!');
        return;
      }

      try {
        const walletConfig = getNetworkConfigForWallet(networkConfig);
        
        // Try to switch to the network
        try {
          await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: walletConfig.chainId }],
          });
        } catch (switchError: any) {
          // This error code indicates that the chain has not been added to MetaMask
          if (switchError.code === 4902) {
            // Add the network
            await window.ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [walletConfig],
            });
          } else {
            throw switchError;
          }
        }
      } catch (error: any) {
        console.error('Error switching network:', error);
        alert(`Failed to switch to ${networkConfig.name}. Please switch manually in your wallet.`);
      }
    }
  };

  if (!provider) {
    return null;
  }

  return (
    <div className="flex items-center gap-2">
      {isMainnetMode && (
        <Badge variant="destructive" className="flex items-center gap-1">
          <AlertTriangle className="h-3 w-3" />
          MAINNET
        </Badge>
      )}
      
      {!isMainnetMode && (
        <Badge variant="secondary" className="flex items-center gap-1">
          <Network className="h-3 w-3" />
          TESTNET
        </Badge>
      )}

      {isCorrectNetwork ? (
        <Badge variant="outline" className="flex items-center gap-1 text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" />
          {networkConfig.name} (Chain ID: {networkConfig.chainId.toString()})
        </Badge>
      ) : (
        <div className="flex items-center gap-2">
          <Badge variant="destructive" className="flex items-center gap-1 bg-red-600 text-white border-red-700">
            <AlertTriangle className="h-4 w-4" />
            WRONG NETWORK
          </Badge>
          <Button
            size="sm"
            variant="destructive"
            onClick={handleSwitchNetwork}
            className="text-xs font-semibold"
          >
            Switch to {networkConfig.name}
          </Button>
        </div>
      )}

      {isMainnetMode && isCorrectNetwork && (
        <div className="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
          <AlertTriangle className="h-3 w-3" />
          Real funds - Use with caution
        </div>
      )}
    </div>
  );
}

