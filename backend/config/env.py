"""
Environment variable validation and schema
"""
import os
from typing import Dict, List, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class EnvSchema:
    """Environment variable schema and validation"""
    
    # Required environment variables
    REQUIRED_VARS = {
        "CREDIT_PASSPORT_NFT_ADDRESS": {
            "description": "CreditPassportNFT contract address",
            "validate": lambda v: v.startswith("0x") and len(v) == 42,
            "error_msg": "Must be a valid Ethereum address (0x followed by 40 hex characters)"
        },
        "BACKEND_PRIVATE_KEY": {
            "description": "Backend wallet private key (or BACKEND_PRIVATE_KEY_ENCRYPTED)",
            "validate": lambda v: (v.startswith("0x") and len(v) == 66) or len(v) == 64,
            "error_msg": "Must be a valid private key",
            "alternatives": ["BACKEND_PRIVATE_KEY_ENCRYPTED"]
        },
    }
    
    # Network-specific required vars
    NETWORK_REQUIRED_VARS = {
        "mainnet": {
            "QIE_MAINNET_CHAIN_ID": {
                "description": "QIE Mainnet chain ID",
                "validate": lambda v: v == "1990",
                "error_msg": "Must be 1990 for QIE Mainnet"
            },
            "QIE_MAINNET_RPC_URLS": {
                "description": "QIE Mainnet RPC URLs (comma-separated)",
                "validate": lambda v: len(v.split(",")) >= 1,
                "error_msg": "Must provide at least one RPC URL"
            },
        },
        "testnet": {
            # Testnet vars are optional (have defaults)
        }
    }
    
    # Optional but recommended variables
    RECOMMENDED_VARS = {
        "DATABASE_URL": "Database connection string",
        "REDIS_URL": "Redis connection string",
        "SENTRY_DSN_BACKEND": "Sentry DSN for error tracking",
        "JWT_SECRET_KEY": "JWT secret for token signing",
    }
    
    @staticmethod
    def validate_environment() -> Dict[str, Any]:
        """
        Validate environment variables
        
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        network = os.getenv("QIE_NETWORK", "testnet").lower().strip()
        
        # Validate required vars
        for var_name, config in EnvSchema.REQUIRED_VARS.items():
            value = os.getenv(var_name)
            
            # Check alternatives
            if not value and "alternatives" in config:
                for alt_var in config["alternatives"]:
                    alt_value = os.getenv(alt_var)
                    if alt_value:
                        value = alt_value
                        break
            
            if not value:
                errors.append(f"Missing required environment variable: {var_name}")
                continue
            
            # Validate format if validator provided
            if "validate" in config:
                try:
                    if not config["validate"](value):
                        errors.append(
                            f"Invalid {var_name} format: {config.get('error_msg', 'Validation failed')}"
                        )
                except Exception as e:
                    errors.append(f"Error validating {var_name}: {str(e)}")
        
        # Validate network-specific vars
        if network in EnvSchema.NETWORK_REQUIRED_VARS:
            for var_name, config in EnvSchema.NETWORK_REQUIRED_VARS[network].items():
                value = os.getenv(var_name)
                if not value:
                    errors.append(f"Missing required {network} variable: {var_name}")
                    continue
                
                if "validate" in config:
                    try:
                        if not config["validate"](value):
                            errors.append(
                                f"Invalid {var_name} format: {config.get('error_msg', 'Validation failed')}"
                            )
                    except Exception as e:
                        errors.append(f"Error validating {var_name}: {str(e)}")
        
        # Check recommended vars
        for var_name, description in EnvSchema.RECOMMENDED_VARS.items():
            if not os.getenv(var_name):
                warnings.append(f"Optional environment variable not set: {var_name} ({description})")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "network": network,
        }
    
    @staticmethod
    def get_network_specific_vars(network: str) -> Dict[str, str]:
        """
        Get network-specific environment variable names
        
        Args:
            network: Network name ("testnet" or "mainnet")
            
        Returns:
            Dict mapping var names to descriptions
        """
        if network == "mainnet":
            return {
                "QIE_MAINNET_CHAIN_ID": "1990",
                "QIE_MAINNET_RPC_URLS": "https://rpc1mainnet.qie.digital/,https://rpc2mainnet.qie.digital/,https://rpc5mainnet.qie.digital/",
                "QIE_MAINNET_EXPLORER_URL": "https://mainnet.qie.digital/",
                "QIE_MAINNET_SYMBOL": "QIEV3",
                "QIE_MAINNET_NAME": "QIEMainnet",
            }
        else:
            return {
                "QIE_TESTNET_CHAIN_ID": "1983",
                "QIE_TESTNET_RPC_URLS": "https://rpc1testnet.qie.digital/",
                "QIE_TESTNET_EXPLORER_URL": "https://testnet.qie.digital",
            }


def validate_env_on_startup() -> None:
    """
    Validate environment variables on application startup
    Raises ValueError if validation fails
    """
    result = EnvSchema.validate_environment()
    
    if result["warnings"]:
        for warning in result["warnings"]:
            logger.warning(warning)
    
    if not result["valid"]:
        error_msg = (
            "Environment validation failed:\n"
            + "\n".join(f"  - {error}" for error in result["errors"])
            + "\n\nPlease set these variables in your .env file or environment."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(
        f"Environment validation passed (network: {result['network']})",
        extra={"network": result["network"], "warnings_count": len(result["warnings"])}
    )


__all__ = ["EnvSchema", "validate_env_on_startup"]

