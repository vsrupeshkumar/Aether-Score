"""
Wallet test fixtures
"""
from eth_account import Account


def create_test_account():
    """Create a test account"""
    return Account.create()


def get_test_addresses():
    """Get test wallet addresses"""
    return {
        "user1": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        "user2": "0x8ba1f109551bD432803012645Hac136c22C1729",
        "user3": "0x1234567890123456789012345678901234567890",
    }


def create_test_signature(account, message):
    """Create a test signature for a message"""
    from eth_account.messages import encode_defunct
    message_encoded = encode_defunct(text=message)
    signature = Account.sign_message(message_encoded, account.key).signature.hex()
    return signature

