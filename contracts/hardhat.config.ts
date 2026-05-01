import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@openzeppelin/hardhat-upgrades";
import "solidity-coverage";
import * as dotenv from "dotenv";

dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.22",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    qieTestnet: {
      url: process.env.QIE_TESTNET_RPC_URL || "https://rpc1testnet.qie.digital/",
      chainId: parseInt(process.env.QIE_TESTNET_CHAIN_ID || "1983"),
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
    qieMainnet: {
      url: process.env.QIE_MAINNET_RPC_URL || "https://rpc1mainnet.qie.digital/",
      chainId: parseInt(process.env.QIE_MAINNET_CHAIN_ID || "1990"),
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
    hardhat: {
      chainId: 1337,
    },
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD",
  },
  coverage: {
    enabled: process.env.COVERAGE !== undefined,
    exclude: [
      "test/",
      "node_modules/",
      "**/*.test.ts",
      "**/Mock*.sol",
    ],
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY || process.env.QIE_EXPLORER_API_KEY || "",
    customChains: [
      {
        network: "qieTestnet",
        chainId: parseInt(process.env.QIE_TESTNET_CHAIN_ID || "1983"),
        urls: {
          apiURL: "https://testnet.qie.digital/api",
          browserURL: "https://testnet.qie.digital"
        }
      },
      {
        network: "qieMainnet",
        chainId: parseInt(process.env.QIE_MAINNET_CHAIN_ID || "1990"),
        urls: {
          apiURL: "https://mainnet.qie.digital/api",
          browserURL: "https://mainnet.qie.digital/"
        }
      }
    ]
  },
};

export default config;

