#!/usr/bin/env python3
"""
Test security features
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

def test_imports():
    """Test that all security modules can be imported"""
    print("Testing imports...")
    try:
        from utils.validators import validate_ethereum_address
        from utils.sanitizers import sanitize_chat_message
        from utils.secrets_manager import get_secrets_manager
        from utils.jwt_handler import create_access_token, verify_token
        from utils.api_keys import validate_api_key
        from utils.wallet_verification import verify_wallet_signature
        from utils.audit_logger import log_audit_event
        from middleware.auth import get_current_user
        from middleware.rate_limit import limiter
        print("âœ… All imports successful")
        return True
    except Exception as e:
        print(f"âŒ Import error: {e}")
        return False

def test_validators():
    """Test input validators"""
    print("\nTesting validators...")
    try:
        from utils.validators import validate_ethereum_address, validate_score, validate_risk_band
        
        # Test valid address
        addr = validate_ethereum_address("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0")
        print(f"âœ… Address validation: {addr[:10]}...")
        
        # Test invalid address
        try:
            validate_ethereum_address("invalid")
            print("âŒ Should have raised error")
            return False
        except ValueError:
            print("âœ… Invalid address correctly rejected")
        
        # Test score validation
        score = validate_score(500)
        print(f"âœ… Score validation: {score}")
        
        # Test risk band
        band = validate_risk_band(2)
        print(f"âœ… Risk band validation: {band}")
        
        return True
    except Exception as e:
        print(f"âŒ Validator error: {e}")
        return False

def test_secrets_manager():
    """Test secrets manager"""
    print("\nTesting secrets manager...")
    try:
        from utils.secrets_manager import get_secrets_manager
        
        manager = get_secrets_manager()
        
        # Test encryption/decryption
        test_value = "test-secret-value"
        encrypted = manager.encrypt(test_value)
        decrypted = manager.decrypt(encrypted)
        
        if decrypted == test_value:
            print("âœ… Encryption/decryption working")
            return True
        else:
            print("âŒ Decryption failed")
            return False
    except Exception as e:
        print(f"âŒ Secrets manager error: {e}")
        return False

def test_jwt():
    """Test JWT token generation"""
    print("\nTesting JWT...")
    try:
        from utils.jwt_handler import create_access_token, verify_token
        
        # Create token
        token = create_access_token({"sub": "0x1234567890123456789012345678901234567890", "role": "user"})
        print(f"âœ… Token created: {token[:20]}...")
        
        # Verify token
        payload = verify_token(token)
        if payload and payload.get("sub") == "0x1234567890123456789012345678901234567890":
            print("âœ… Token verification working")
            return True
        else:
            print("âŒ Token verification failed")
            return False
    except Exception as e:
        print(f"âŒ JWT error: {e}")
        return False

def test_api_keys():
    """Test API key validation"""
    print("\nTesting API keys...")
    try:
        from utils.api_keys import validate_api_key, get_api_keys
        
        keys = get_api_keys()
        print(f"âœ… Found {len(keys)} API key(s) in environment")
        
        if keys:
            if validate_api_key(keys[0]):
                print("âœ… API key validation working")
                return True
            else:
                print("âŒ API key validation failed")
                return False
        else:
            print("âš ï¸  No API keys configured (set API_KEYS env var)")
            return True  # Not an error, just not configured
    except Exception as e:
        print(f"âŒ API key error: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\nTesting environment...")
    required = [
        "CREDIT_PASSPORT_NFT_ADDRESS",
        "BACKEND_PRIVATE_KEY",
    ]
    
    optional = [
        "JWT_SECRET_KEY",
        "API_KEYS",
        "SECRETS_ENCRYPTION_KEY",
        "FRONTEND_URL",
    ]
    
    missing_required = []
    for var in required:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"âŒ Missing required env vars: {', '.join(missing_required)}")
        return False
    
    print("âœ… Required environment variables set")
    
    missing_optional = [var for var in optional if not os.getenv(var)]
    if missing_optional:
        print(f"âš ï¸  Optional env vars not set: {', '.join(missing_optional)}")
        print("   (These are recommended for production)")
    
    return True

def main():
    print("ðŸ”’ AETHER-SCORE Security Test Suite")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Validators", test_validators()))
    results.append(("Secrets Manager", test_secrets_manager()))
    results.append(("JWT", test_jwt()))
    results.append(("API Keys", test_api_keys()))
    results.append(("Environment", test_environment()))
    
    print("\n" + "=" * 50)
    print("ðŸ“Š Test Results:")
    for name, result in results:
        status = "âœ… PASS" if result else "âŒ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\nðŸŽ‰ All security tests passed!")
        return 0
    else:
        print("\nâš ï¸  Some tests failed - check errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())


