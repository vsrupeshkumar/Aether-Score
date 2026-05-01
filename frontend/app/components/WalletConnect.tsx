'use client';

import { useState, useEffect } from 'react';
import { ethers } from 'ethers';

interface WalletConnectProps {
  onConnect: (address: string, provider: ethers.BrowserProvider) => void;
  onDisconnect: () => void;
}

export default function WalletConnect({ onConnect, onDisconnect }: WalletConnectProps) {
  const [address, setAddress] = useState<string | null>(null);
  const [balance, setBalance] = useState<string>('0');
  const [isConnecting, setIsConnecting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Don't auto-connect - always require user to click "Connect Wallet"
  }, []);

  const updateBalance = async (provider: ethers.BrowserProvider, addr: string) => {
    try {
      const balance = await provider.getBalance(addr);
      setBalance(ethers.formatEther(balance));
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const connectWallet = async () => {
    if (typeof window === 'undefined' || !window.ethereum) {
      alert('Please install MetaMask or QIE Wallet!');
      return;
    }

    setIsConnecting(true);
    try {
      const provider = new ethers.BrowserProvider(window.ethereum);
      await provider.send('eth_requestAccounts', []);
      const signer = await provider.getSigner();
      const addr = await signer.getAddress();
      
      setAddress(addr);
      updateBalance(provider, addr);
      onConnect(addr, provider);
    } catch (error) {
      console.error('Error connecting wallet:', error);
      alert('Failed to connect wallet');
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setAddress(null);
    setBalance('0');
    onDisconnect();
  };

  const copyAddress = async () => {
    if (address) {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (address) {
    return (
      <div className="flex items-center gap-3 animate-fade-in">
        {/* Connection Status Indicator */}
        <div className="flex items-center gap-2 glass px-3 py-2 rounded-lg">
          <div className="relative">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <div className="absolute inset-0 w-2 h-2 bg-green-500 rounded-full animate-ping opacity-75"></div>
          </div>
          <span className="text-xs text-text-secondary">Connected</span>
        </div>

        {/* Balance Badge */}
        <div className="glass px-4 py-2 rounded-lg">
          <p className="text-xs text-text-secondary mb-0.5">Balance</p>
          <p className="text-sm font-semibold text-white font-mono">
            {parseFloat(balance).toFixed(4)} QIE
          </p>
        </div>

        {/* Address Display */}
        <div className="glass px-4 py-2 rounded-lg flex items-center gap-2 group cursor-pointer" onClick={copyAddress}>
          <p className="text-sm font-mono text-white">
            {address.slice(0, 6)}...{address.slice(-4)}
          </p>
          <svg 
            className={`w-4 h-4 text-text-secondary transition-colors ${copied ? 'text-green-500' : 'group-hover:text-white'}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            {copied ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            )}
          </svg>
          {copied && (
            <span className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-xs text-green-400 animate-fade-in">
              Copied!
            </span>
          )}
        </div>

        {/* Disconnect Button */}
        <button
          onClick={disconnectWallet}
          className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-all text-sm font-medium border border-red-500/30 hover:border-red-500/50"
        >
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={connectWallet}
      disabled={isConnecting}
      className="btn-gradient px-8 py-3 rounded-lg font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
    >
      {isConnecting ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Connecting...
        </span>
      ) : (
        <span className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
          Connect Wallet
        </span>
      )}
    </button>
  );
}

declare global {
  interface Window {
    ethereum?: any;
  }
}
