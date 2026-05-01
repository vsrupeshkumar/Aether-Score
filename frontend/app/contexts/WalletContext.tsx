'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ethers } from 'ethers';
import { getNetworkConfig, getNetworkConfigForWallet, isMainnet } from '@/lib/config/network';

interface WalletContextType {
  address: string | null;
  provider: ethers.BrowserProvider | null;
  balance: string;
  isConnected: boolean;
  isConnecting: boolean;
  isCorrectNetwork: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  refreshBalance: () => Promise<void>;
  verifyNetwork: () => Promise<boolean>;
  switchToNetwork: () => Promise<boolean>;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

const WALLET_STORAGE_KEY = 'AETHER-SCORE_wallet_address';

// Get network configuration
const networkConfig = getNetworkConfig();
const walletConfig = getNetworkConfigForWallet(networkConfig);

// Helper function to switch to the configured network
const switchToNetwork = async (): Promise<boolean> => {
  if (typeof window === 'undefined' || !window.ethereum) {
    return false;
  }

  try {
    // Try to switch to the network
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: walletConfig.chainId }],
    });
    return true;
  } catch (switchError: any) {
    // This error code indicates that the chain has not been added to MetaMask
    if (switchError.code === 4902) {
      try {
        // Add the network
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [walletConfig],
        });
        return true;
      } catch (addError) {
        console.error(`Error adding ${networkConfig.name}:`, addError);
        alert(`Failed to add ${networkConfig.name}. Please add it manually in your wallet.`);
        return false;
      }
    } else {
      console.error(`Error switching to ${networkConfig.name}:`, switchError);
      return false;
    }
  }
};

// Helper function to check if connected to correct network
const checkNetwork = async (provider: ethers.BrowserProvider): Promise<boolean> => {
  try {
    const network = await provider.getNetwork();
    const isCorrect = network.chainId === networkConfig.chainId;
    return isCorrect;
  } catch (error) {
    console.error('Error checking network:', error);
    return false;
  }
};

// Helper function to verify network and throw if wrong (for transaction blocking)
const verifyNetworkForTransaction = async (provider: ethers.BrowserProvider): Promise<void> => {
  const network = await provider.getNetwork();
  if (network.chainId !== networkConfig.chainId) {
    const errorMessage = `Wrong network! Expected ${networkConfig.name} (Chain ID: ${networkConfig.chainId.toString()}), but connected to Chain ID: ${network.chainId.toString()}. Please switch to ${networkConfig.name} before proceeding.`;
    throw new Error(errorMessage);
  }
};

export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [balance, setBalance] = useState<string>('0');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isCorrectNetwork, setIsCorrectNetwork] = useState<boolean>(true);

  // Restore connection from localStorage on mount (but don't auto-connect)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedAddress = localStorage.getItem(WALLET_STORAGE_KEY);
      if (savedAddress && window.ethereum) {
        // Check if wallet is still connected (without requesting)
        const checkConnection = async () => {
          try {
            // Use eth_accounts which doesn't prompt, only returns already connected accounts
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            if (accounts.length > 0 && accounts[0].toLowerCase() === savedAddress.toLowerCase()) {
              // Wallet is still connected, restore state
              const prov = new ethers.BrowserProvider(window.ethereum);
              setAddress(savedAddress);
              setProvider(prov);
              // Use the refreshBalanceForAddress function (defined below)
              // We'll call it after the function is defined
              setTimeout(async () => {
                try {
                  const network = await prov.getNetwork();
                  console.log('Restored connection to network:', network.chainId.toString());
                  
                  // Check if on correct network
                  const isCorrect = network.chainId === networkConfig.chainId;
                  setIsCorrectNetwork(isCorrect);
                  if (!isCorrect) {
                    console.warn(`Not connected to ${networkConfig.name}. Current chain ID:`, network.chainId.toString());
                    const shouldSwitch = confirm(
                      `You are not connected to ${networkConfig.name} (Chain ID: ${networkConfig.chainId.toString()}). ` +
                      `Would you like to switch to ${networkConfig.name} now?`
                    );
                    if (shouldSwitch) {
                      await switchToNetwork();
                      // Reload to get updated provider
                      window.location.reload();
                      return;
                    }
                  }
                  
                  const bal = await prov.getBalance(savedAddress);
                  const formattedBalance = ethers.formatEther(bal);
                  console.log('Restored balance:', formattedBalance, 'QIE');
                  setBalance(formattedBalance);
                } catch (balanceError) {
                  console.error('Error fetching balance on restore:', balanceError);
                  // Try fallback
                  if (window.ethereum) {
                    try {
                      const balanceHex = await window.ethereum.request({
                        method: 'eth_getBalance',
                        params: [savedAddress, 'latest'],
                      });
                      const balanceWei = BigInt(balanceHex);
                      setBalance(ethers.formatEther(balanceWei.toString()));
                    } catch (fallbackError) {
                      console.error('Fallback balance fetch failed:', fallbackError);
                      setBalance('0');
                    }
                  } else {
                    setBalance('0');
                  }
                }
              }, 100);
            } else {
              // Wallet not connected, clear saved address
              localStorage.removeItem(WALLET_STORAGE_KEY);
            }
          } catch (error) {
            console.error('Error checking wallet connection:', error);
            localStorage.removeItem(WALLET_STORAGE_KEY);
          }
        };
        checkConnection();
      }
    }
  }, []);

  // Helper function to fetch balance with fallback
  const refreshBalanceForAddress = async (prov: ethers.BrowserProvider, addr: string) => {
    try {
      // Get the current network to ensure we're on the right chain
      const network = await prov.getNetwork();
      console.log('Current network:', network.chainId.toString());
      
      const bal = await prov.getBalance(addr);
      const formattedBalance = ethers.formatEther(bal);
      console.log('Balance fetched:', formattedBalance, 'QIE');
      setBalance(formattedBalance);
    } catch (error) {
      console.error('Error fetching balance via provider:', error);
      // Try to get balance using direct RPC call as fallback
      if (window.ethereum) {
        try {
          console.log('Trying fallback balance fetch for address:', addr);
          const balanceHex = await window.ethereum.request({
            method: 'eth_getBalance',
            params: [addr, 'latest'],
          });
          const balanceWei = BigInt(balanceHex);
          const formattedBalance = ethers.formatEther(balanceWei.toString());
          console.log('Fallback balance fetched:', formattedBalance, 'QIE');
          setBalance(formattedBalance);
        } catch (fallbackError) {
          console.error('Fallback balance fetch failed:', fallbackError);
          setBalance('0');
        }
      } else {
        setBalance('0');
      }
    }
  };

  const refreshBalance = async () => {
    if (address && provider) {
      await refreshBalanceForAddress(provider, address);
    }
  };

  // Listen for account changes and chain changes
  useEffect(() => {
    if (typeof window !== 'undefined' && window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          // User disconnected
          disconnect();
        } else if (accounts[0].toLowerCase() !== address?.toLowerCase()) {
          // Account changed
          setAddress(accounts[0]);
          localStorage.setItem(WALLET_STORAGE_KEY, accounts[0]);
          if (provider) {
            refreshBalance();
          }
        }
      };

      const handleChainChanged = async (chainId: string) => {
        console.log('Chain changed to:', chainId);
        const chainIdNum = BigInt(chainId);
        
        // Check if switched to correct network
        const isCorrect = chainIdNum === networkConfig.chainId;
        setIsCorrectNetwork(isCorrect);
        if (isCorrect) {
          console.log(`Switched to ${networkConfig.name} successfully`);
          // Refresh balance if connected
          if (address && provider) {
            await refreshBalance();
          }
        } else {
          console.warn(`Switched to wrong network. Expected ${networkConfig.name} (${networkConfig.chainId.toString()}), got:`, chainIdNum.toString());
          const shouldSwitch = confirm(
            `You switched to a different network (Chain ID: ${chainIdNum}). ` +
            `AETHER-SCORE requires ${networkConfig.name} (Chain ID: ${networkConfig.chainId.toString()}). ` +
            `Would you like to switch back to ${networkConfig.name}?`
          );
          if (shouldSwitch) {
            await switchToNetwork();
          }
        }
        
        // Reload the page when chain changes to ensure provider is updated
        window.location.reload();
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      return () => {
        window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum?.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, [address, provider]);

  const connect = async () => {
    if (typeof window === 'undefined' || !window.ethereum) {
      alert('Please install MetaMask or QIE Wallet!');
      return;
    }

    setIsConnecting(true);
    try {
      const prov = new ethers.BrowserProvider(window.ethereum);
      // This will prompt MetaMask for permission
      await prov.send('eth_requestAccounts', []);
      const signer = await prov.getSigner();
      const addr = await signer.getAddress();
      
      // Check if on correct network
      const isCorrect = await checkNetwork(prov);
      setIsCorrectNetwork(isCorrect);
      if (!isCorrect) {
        const network = await prov.getNetwork();
        const shouldSwitch = confirm(
          `You are not connected to ${networkConfig.name} (Chain ID: ${networkConfig.chainId.toString()}). ` +
          `Current network: Chain ID ${network.chainId}. ` +
          `Would you like to switch to ${networkConfig.name} now?`
        );
        if (shouldSwitch) {
          const switched = await switchToNetwork();
          if (switched) {
            // Reload to get updated provider
            window.location.reload();
            return;
          } else {
            alert(`Failed to switch network. Please switch manually to ${networkConfig.name}.`);
            setIsConnecting(false);
            return;
          }
        } else {
          alert(`Please switch to ${networkConfig.name} to use AETHER-SCORE.`);
          setIsConnecting(false);
          return;
        }
      }
      
      setAddress(addr);
      setProvider(prov);
      
      // Save to localStorage
      localStorage.setItem(WALLET_STORAGE_KEY, addr);
      
      // Fetch balance with error handling and retry
      await refreshBalanceForAddress(prov, addr);
    } catch (error) {
      console.error('Error connecting wallet:', error);
      if ((error as any).code === 4001) {
        alert('Please approve the connection request in MetaMask');
      } else {
        alert('Failed to connect wallet');
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnect = () => {
    setAddress(null);
    setProvider(null);
    setBalance('0');
    setIsCorrectNetwork(true);
    localStorage.removeItem(WALLET_STORAGE_KEY);
  };

  // Verify network before transactions (throws if wrong network)
  const verifyNetwork = async (): Promise<boolean> => {
    if (!provider) {
      throw new Error('Wallet not connected');
    }
    try {
      await verifyNetworkForTransaction(provider);
      setIsCorrectNetwork(true);
      return true;
    } catch (error) {
      setIsCorrectNetwork(false);
      throw error;
    }
  };

  // Switch to correct network
  const switchToCorrectNetwork = async (): Promise<boolean> => {
    const result = await switchToNetwork();
    if (result && provider) {
      const isCorrect = await checkNetwork(provider);
      setIsCorrectNetwork(isCorrect);
    }
    return result;
  };

  return (
    <WalletContext.Provider
      value={{
        address,
        provider,
        balance,
        isConnected: address !== null,
        isConnecting,
        isCorrectNetwork,
        connect,
        disconnect,
        refreshBalance,
        verifyNetwork,
        switchToNetwork: switchToCorrectNetwork,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
}

declare global {
  interface Window {
    ethereum?: any;
  }
}


