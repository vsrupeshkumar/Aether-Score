/**
 * Centralized network configuration for QIE testnet and mainnet.
 * 
 * This module provides a single source of truth for network-specific settings,
 * allowing the application to switch between testnet and mainnet via environment variables.
 */

export interface NetworkConfig {
  chainId: bigint;
  name: string;
  rpcUrls: string[];
  explorerUrl: string;
  nativeCurrency: {
    name: string;
    symbol: string;
    decimals: number;
  };
  isMainnet: boolean;
}

// QIE Testnet Configuration
export const QIE_TESTNET_CONFIG: NetworkConfig = {
  chainId: 1983n,
  name: "QIE Testnet",
  rpcUrls: [
    "https://rpc1testnet.qie.digital/",
  ],
  explorerUrl: "https://testnet.qie.digital",
  nativeCurrency: {
    name: "QIE",
    symbol: "QIE",
    decimals: 18,
  },
  isMainnet: false,
};

// QIE Mainnet Configuration (Confirmed values)
export const QIE_MAINNET_CONFIG: NetworkConfig = {
  chainId: 1990n,
  name: "QIEMainnet",
  rpcUrls: [
    "https://rpc1mainnet.qie.digital/",
    "https://rpc2mainnet.qie.digital/",
    "https://rpc5mainnet.qie.digital/",
  ],
  explorerUrl: "https://mainnet.qie.digital/",
  nativeCurrency: {
    name: "QIEV3",
    symbol: "QIEV3",
    decimals: 18,
  },
  isMainnet: true,
};

/**
 * Get network configuration based on environment variable.
 * 
 * Reads NEXT_PUBLIC_QIE_NETWORK environment variable:
 * - "mainnet" -> Returns QIE_MAINNET_CONFIG
 * - "testnet" or not set -> Returns QIE_TESTNET_CONFIG (default)
 * 
 * @returns NetworkConfig for the active network
 */
export function getNetworkConfig(): NetworkConfig {
  const network = (process.env.NEXT_PUBLIC_QIE_NETWORK || "testnet").toLowerCase().trim();
  
  if (network === "mainnet") {
    console.log("Using QIE Mainnet configuration", {
      chainId: QIE_MAINNET_CONFIG.chainId.toString(),
      name: QIE_MAINNET_CONFIG.name,
      rpcUrls: QIE_MAINNET_CONFIG.rpcUrls,
      explorerUrl: QIE_MAINNET_CONFIG.explorerUrl,
    });
    return QIE_MAINNET_CONFIG;
  } else {
    console.log("Using QIE Testnet configuration", {
      chainId: QIE_TESTNET_CONFIG.chainId.toString(),
      name: QIE_TESTNET_CONFIG.name,
      rpcUrls: QIE_TESTNET_CONFIG.rpcUrls,
      explorerUrl: QIE_TESTNET_CONFIG.explorerUrl,
    });
    return QIE_TESTNET_CONFIG;
  }
}

/**
 * Get primary RPC URL from network config
 */
export function getPrimaryRpcUrl(config?: NetworkConfig): string {
  const networkConfig = config || getNetworkConfig();
  return networkConfig.rpcUrls[0] || "";
}

/**
 * Get fallback RPC URLs from network config
 */
export function getFallbackRpcUrls(config?: NetworkConfig): string[] {
  const networkConfig = config || getNetworkConfig();
  return networkConfig.rpcUrls.slice(1);
}

/**
 * Get network configuration for MetaMask/EIP-3085
 */
export function getNetworkConfigForWallet(config?: NetworkConfig) {
  const networkConfig = config || getNetworkConfig();
  
  return {
    chainId: `0x${networkConfig.chainId.toString(16)}`,
    chainName: networkConfig.name,
    nativeCurrency: networkConfig.nativeCurrency,
    rpcUrls: networkConfig.rpcUrls,
    blockExplorerUrls: [networkConfig.explorerUrl],
  };
}

/**
 * Check if current network is mainnet
 */
export function isMainnet(config?: NetworkConfig): boolean {
  const networkConfig = config || getNetworkConfig();
  return networkConfig.isMainnet;
}

/**
 * Get explorer URL for a transaction
 */
export function getExplorerTxUrl(txHash: string, config?: NetworkConfig): string {
  const networkConfig = config || getNetworkConfig();
  const baseUrl = networkConfig.explorerUrl.replace(/\/$/, "");
  return `${baseUrl}/tx/${txHash}`;
}

/**
 * Get explorer URL for an address
 */
export function getExplorerAddressUrl(address: string, config?: NetworkConfig): string {
  const networkConfig = config || getNetworkConfig();
  const baseUrl = networkConfig.explorerUrl.replace(/\/$/, "");
  return `${baseUrl}/address/${address}`;
}

