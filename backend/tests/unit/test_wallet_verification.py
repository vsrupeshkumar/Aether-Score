"""
Unit tests for wallet verification
"""
import pytest
from eth_account import Account
from utils.wallet_verification import (
    verify_wallet_signature,
    create_verification_message,
    verify_timestamped_message
)


@pytest.mark.unit
class TestWalletVerification:
    """Test wallet signature verification"""
    
    @pytest.fixture
    def test_account(self):
        """Create test account"""
        return Account.create()
    
    def test_verify_wallet_signature_valid(self, test_account):
        """Test verifying valid signature"""
        message = "Hello, AETHER-SCORE!"
        from eth_account.messages import encode_defunct
        
        message_encoded = encode_defunct(text=message)
        signed_message = Account.sign_message(message_encoded, test_account.key)
        # Function expects signature with 0x prefix and 132 chars total
        signature = "0x" + signed_message.signature.hex()
        
        # The function validates and checksums the address internally
        result = verify_wallet_signature(test_account.address, message, signature)
        
        assert result is True
    
    def test_verify_wallet_signature_invalid_address(self, test_account):
        """Test verifying signature with wrong address"""
        message = "Hello, AETHER-SCORE!"
        from eth_account.messages import encode_defunct
        message_encoded = encode_defunct(text=message)
        signature = Account.sign_message(message_encoded, test_account.key).signature.hex()
        
        wrong_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = verify_wallet_signature(wrong_address, message, signature)
        
        assert result is False
    
    def test_verify_wallet_signature_invalid_signature(self, test_account):
        """Test verifying invalid signature"""
        message = "Hello, AETHER-SCORE!"
        invalid_signature = "0x" + "0" * 130
        
        result = verify_wallet_signature(test_account.address, message, invalid_signature)
        
        assert result is False
    
    def test_verify_wallet_signature_wrong_message(self, test_account):
        """Test verifying signature with wrong message"""
        message1 = "Hello, AETHER-SCORE!"
        message2 = "Different message"
        from eth_account.messages import encode_defunct
        message_encoded = encode_defunct(text=message1)
        signature = Account.sign_message(message_encoded, test_account.key).signature.hex()
        
        result = verify_wallet_signature(test_account.address, message2, signature)
        
        assert result is False
    
    def test_verify_wallet_signature_invalid_format(self, test_account):
        """Test verifying signature with invalid format"""
        message = "Hello, AETHER-SCORE!"
        
        # Missing 0x prefix
        result = verify_wallet_signature(test_account.address, message, "123" * 43)
        assert result is False
        
        # Wrong length
        result = verify_wallet_signature(test_account.address, message, "0x123")
        assert result is False
    
    def test_verify_wallet_signature_invalid_address_format(self):
        """Test verifying signature with invalid address format"""
        message = "Hello, AETHER-SCORE!"
        signature = "0x" + "0" * 130
        
        result = verify_wallet_signature("invalid_address", message, signature)
        assert result is False
    
    def test_create_verification_message(self):
        """Test creating verification message"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        action = "generate_score"
        
        message = create_verification_message(address, action)
        
        assert address in message
        assert action in message
        assert "Timestamp:" in message
        assert "AETHER-SCORE Authentication" in message
    
    def test_create_verification_message_with_timestamp(self):
        """Test creating verification message with custom timestamp"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        action = "generate_score"
        timestamp = 1234567890
        
        message = create_verification_message(address, action, timestamp)
        
        assert str(timestamp) in message
    
    def test_verify_timestamped_message_valid(self, test_account):
        """Test verifying valid timestamped message"""
        address = test_account.address
        action = "generate_score"
        message = create_verification_message(address, action)
        
        from eth_account.messages import encode_defunct
        message_encoded = encode_defunct(text=message)
        signed_message = Account.sign_message(message_encoded, test_account.key)
        # Function expects signature with 0x prefix and 132 chars total
        signature = "0x" + signed_message.signature.hex()
        
        # The function validates and checksums the address internally
        result = verify_timestamped_message(address, message, signature)
        
        assert result is True
    
    def test_verify_timestamped_message_expired(self, test_account):
        """Test verifying expired timestamped message"""
        import time
        address = test_account.address
        action = "generate_score"
        # Create message with old timestamp (6 minutes ago)
        old_timestamp = int(time.time()) - 360
        message = create_verification_message(address, action, old_timestamp)
        
        from eth_account.messages import encode_defunct
        message_encoded = encode_defunct(text=message)
        signature = Account.sign_message(message_encoded, test_account.key).signature.hex()
        
        result = verify_timestamped_message(address, message, signature, max_age_seconds=300)
        
        assert result is False
    
    def test_verify_timestamped_message_future(self, test_account):
        """Test verifying message with future timestamp"""
        import time
        address = test_account.address
        action = "generate_score"
        # Create message with future timestamp (2 minutes ahead)
        future_timestamp = int(time.time()) + 120
        message = create_verification_message(address, action, future_timestamp)
        
        from eth_account.messages import encode_defunct
        message_encoded = encode_defunct(text=message)
        signature = Account.sign_message(message_encoded, test_account.key).signature.hex()
        
        result = verify_timestamped_message(address, message, signature)
        
        assert result is False
    
    def test_verify_timestamped_message_no_timestamp(self, test_account):
        """Test verifying message without timestamp"""
        address = test_account.address
        message = "Hello, AETHER-SCORE!"  # No timestamp
        from eth_account.messages import encode_defunct
        message_encoded = encode_defunct(text=message)
        signature = Account.sign_message(message_encoded, test_account.key).signature.hex()
        
        result = verify_timestamped_message(address, message, signature)
        
        assert result is False
    
    def test_verify_timestamped_message_invalid_signature(self, test_account):
        """Test verifying timestamped message with invalid signature"""
        address = test_account.address
        action = "generate_score"
        message = create_verification_message(address, action)
        invalid_signature = "0x" + "0" * 130
        
        result = verify_timestamped_message(address, message, invalid_signature)
        
        assert result is False


