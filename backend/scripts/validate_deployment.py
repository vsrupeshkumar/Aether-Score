#!/usr/bin/env python3
"""
Pre-deployment validation script for Render.
Validates environment variables before the application starts.
This helps catch configuration issues early in the deployment process.
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def validate_environment():
    """Validate required environment variables before deployment"""
    errors = []
    warnings = []
    
    # Required environment variables
    required_vars = {
        "BACKEND_PRIVATE_KEY": {
            "alt": "BACKEND_PRIVATE_KEY_ENCRYPTED",
            "validate": lambda v: v.startswith("0x") and len(v) == 66,
            "error_msg": "Must be a valid private key (0x followed by 64 hex characters)"
        },
        "CREDIT_PASSPORT_NFT_ADDRESS": {
            "alt": "CREDIT_PASSPORT_ADDRESS",
            "validate": lambda v: v.startswith("0x") and len(v) == 42,
            "error_msg": "Must be a valid Ethereum address (0x followed by 40 hex characters)"
        },
        "QIE_RPC_URL": {
            "alt": "QIE_TESTNET_RPC_URL",
            "validate": lambda v: v.startswith("http://") or v.startswith("https://"),
            "error_msg": "Must start with http:// or https://"
        }
    }
    
    # Check each required variable
    for var_name, config in required_vars.items():
        value = os.getenv(var_name)
        alt_value = os.getenv(config.get("alt", ""))
        
        if not value and not alt_value:
            errors.append(f"Missing required environment variable: {var_name} (or {config.get('alt', 'N/A')})")
            continue
        
        # Use the value that exists
        actual_value = value or alt_value
        actual_var = var_name if value else config.get("alt", "")
        
        # Validate format if validator provided
        if config.get("validate"):
            try:
                if not config["validate"](actual_value):
                    errors.append(
                        f"Invalid {actual_var} format: {actual_value}. {config['error_msg']}"
                    )
            except Exception as e:
                errors.append(f"Error validating {actual_var}: {str(e)}")
    
    # Optional but recommended variables
    recommended_vars = {
        "DATABASE_URL": "Database connection string",
        "REDIS_URL": "Redis connection string",
        "REDIS_CACHE_URL": "Redis cache connection string",
        "REDIS_QUEUE_URL": "Redis queue connection string",
    }
    
    for var_name, description in recommended_vars.items():
        if not os.getenv(var_name):
            warnings.append(f"Optional environment variable not set: {var_name} ({description})")
    
    # Print results
    if errors:
        print("=" * 80)
        print("DEPLOYMENT VALIDATION FAILED")
        print("=" * 80)
        print("\nErrors:")
        for error in errors:
            print(f"  ❌ {error}")
        
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        
        print("\n" + "=" * 80)
        print("Please set the required environment variables in Render's dashboard:")
        print("  Settings → Environment → Environment Variables")
        print("=" * 80)
        return False
    
    if warnings:
        print("=" * 80)
        print("DEPLOYMENT VALIDATION PASSED (with warnings)")
        print("=" * 80)
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print("=" * 80)
    else:
        print("=" * 80)
        print("DEPLOYMENT VALIDATION PASSED ✓")
        print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
