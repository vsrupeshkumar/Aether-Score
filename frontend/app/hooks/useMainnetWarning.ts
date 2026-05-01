'use client';

import { useCallback } from 'react';
import { isMainnet, getNetworkConfig } from '@/lib/config/network';
import { useWallet } from '@/app/contexts/WalletContext';

/**
 * Hook for mainnet transaction warnings and confirmations
 */
export function useMainnetWarning() {
  const networkConfig = getNetworkConfig();
  const isMainnetMode = isMainnet(networkConfig);
  const { provider, verifyNetwork, isCorrectNetwork } = useWallet();

  const requireMainnetConfirmation = useCallback(
    async (action: string, details?: string): Promise<boolean> => {
      // First verify network connection
      if (provider) {
        try {
          await verifyNetwork();
        } catch (error: any) {
          alert(`Network Error: ${error.message}\n\nPlease switch to ${networkConfig.name} before proceeding.`);
          return false;
        }
      }

      // Then check mainnet mode and require confirmation
      if (!isMainnetMode) {
        return true;
      }

      const message = [
        `⚠️ MAINNET TRANSACTION WARNING`,
        ``,
        `You are about to perform: ${action}`,
        details ? `Details: ${details}` : '',
        ``,
        `This will use REAL FUNDS on QIE Mainnet.`,
        ``,
        `Are you sure you want to continue?`,
      ]
        .filter(Boolean)
        .join('\n');

      const confirmed = window.confirm(message);
      return confirmed;
    },
    [isMainnetMode, provider, verifyNetwork, networkConfig]
  );

  const showMainnetWarning = useCallback(
    (message: string) => {
      if (isMainnetMode) {
        alert(`⚠️ MAINNET WARNING\n\n${message}\n\nYou are using REAL FUNDS.`);
      }
    },
    [isMainnetMode]
  );

  return {
    isMainnetMode,
    isCorrectNetwork,
    requireMainnetConfirmation,
    showMainnetWarning,
  };
}

