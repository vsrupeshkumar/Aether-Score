"""
Unit tests for validators
"""
import pytest
from utils.validators import (
    validate_ethereum_address,
    validate_score,
    validate_risk_band,
    validate_message_length
)


@pytest.mark.unit
class TestValidators:
    """Test input validators"""
    
    def test_validate_ethereum_address_valid(self):
        """Test valid Ethereum address"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = validate_ethereum_address(address)
        # Checksumming may change case, so check it's valid and same length
        assert result.startswith("0x")
        assert len(result) == 42
        assert result.lower() == address.lower()
    
    def test_validate_ethereum_address_checksum(self):
        """Test address checksumming"""
        address = "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"
        result = validate_ethereum_address(address)
        assert result.startswith("0x")
        assert len(result) == 42
    
    def test_validate_ethereum_address_empty(self):
        """Test empty address"""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_ethereum_address("")
    
    def test_validate_ethereum_address_invalid_length(self):
        """Test invalid address length"""
        with pytest.raises(ValueError, match="Invalid address length"):
            validate_ethereum_address("0x123")
    
    def test_validate_ethereum_address_no_prefix(self):
        """Test address without 0x prefix"""
        # Address validation checks length first, so it will fail on length check
        with pytest.raises(ValueError):
            validate_ethereum_address("742d35Cc6634C0532925a3b844Bc9e7595f0bEb0")
    
    def test_validate_ethereum_address_invalid_chars(self):
        """Test address with invalid characters"""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_ethereum_address("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEbG")
    
    def test_validate_ethereum_address_not_string(self):
        """Test non-string address"""
        with pytest.raises(ValueError, match="must be a string"):
            validate_ethereum_address(12345)
    
    def test_validate_score_valid(self):
        """Test valid score"""
        assert validate_score(500) == 500
        assert validate_score(0) == 0
        assert validate_score(1000) == 1000
    
    def test_validate_score_too_low(self):
        """Test score below minimum"""
        with pytest.raises(ValueError, match="must be between 0 and 1000"):
            validate_score(-1)
    
    def test_validate_score_too_high(self):
        """Test score above maximum"""
        with pytest.raises(ValueError, match="must be between 0 and 1000"):
            validate_score(1001)
    
    def test_validate_score_not_int(self):
        """Test non-integer score"""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_score("500")
    
    def test_validate_risk_band_valid(self):
        """Test valid risk band"""
        assert validate_risk_band(0) == 0
        assert validate_risk_band(1) == 1
        assert validate_risk_band(2) == 2
        assert validate_risk_band(3) == 3
    
    def test_validate_risk_band_too_low(self):
        """Test risk band below minimum"""
        with pytest.raises(ValueError, match="must be between 0 and 3"):
            validate_risk_band(-1)
    
    def test_validate_risk_band_too_high(self):
        """Test risk band above maximum"""
        with pytest.raises(ValueError, match="must be between 0 and 3"):
            validate_risk_band(4)
    
    def test_validate_risk_band_not_int(self):
        """Test non-integer risk band"""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_risk_band("2")
    
    def test_validate_message_length_valid(self):
        """Test valid message length"""
        message = "Hello, world!"
        assert validate_message_length(message) == "Hello, world!"
    
    def test_validate_message_length_max(self):
        """Test message at maximum length"""
        message = "a" * 1000
        assert len(validate_message_length(message)) == 1000
    
    def test_validate_message_length_too_long(self):
        """Test message exceeding maximum length"""
        message = "a" * 1001
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_message_length(message)
    
    def test_validate_message_length_custom_max(self):
        """Test message with custom max length"""
        message = "a" * 100
        assert len(validate_message_length(message, max_length=200)) == 100
    
    def test_validate_message_length_empty(self):
        """Test empty message"""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_message_length("")
    
    def test_validate_message_length_whitespace_only(self):
        """Test whitespace-only message"""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_message_length("   ")
    
    def test_validate_message_length_not_string(self):
        """Test non-string message"""
        with pytest.raises(ValueError, match="must be a string"):
            validate_message_length(12345)

