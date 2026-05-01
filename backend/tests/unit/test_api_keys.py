"""
Unit tests for API key management
"""
import pytest
from unittest.mock import patch, Mock
from utils.api_keys import get_api_keys, validate_api_key, get_api_key_from_header


@pytest.mark.unit
class TestAPIKeys:
    """Test API key management functions"""
    
    def test_get_api_keys_empty(self):
        """Test getting API keys when none are set"""
        with patch.dict('os.environ', {}, clear=True):
            keys = get_api_keys()
            assert keys == []
    
    def test_get_api_keys_single(self):
        """Test getting single API key"""
        with patch.dict('os.environ', {'API_KEYS': 'test-key-123'}):
            keys = get_api_keys()
            assert keys == ['test-key-123']
    
    def test_get_api_keys_multiple(self):
        """Test getting multiple API keys"""
        with patch.dict('os.environ', {'API_KEYS': 'key1,key2,key3'}):
            keys = get_api_keys()
            assert keys == ['key1', 'key2', 'key3']
    
    def test_get_api_keys_with_whitespace(self):
        """Test getting API keys with whitespace"""
        with patch.dict('os.environ', {'API_KEYS': ' key1 , key2 , key3 '}):
            keys = get_api_keys()
            assert keys == ['key1', 'key2', 'key3']
    
    def test_get_api_keys_with_empty_entries(self):
        """Test getting API keys with empty entries"""
        with patch.dict('os.environ', {'API_KEYS': 'key1,,key2, ,key3'}):
            keys = get_api_keys()
            assert keys == ['key1', 'key2', 'key3']
    
    def test_get_api_keys_encrypted(self):
        """Test getting encrypted API keys"""
        with patch.dict('os.environ', {'API_KEYS': 'encrypted-key-123'}):
            with patch('utils.api_keys.get_secrets_manager') as mock_secrets:
                mock_manager = Mock()
                mock_manager.decrypt = Mock(return_value='decrypted-key-123')
                mock_secrets.return_value = mock_manager
                
                keys = get_api_keys()
                assert keys == ['decrypted-key-123']
                mock_manager.decrypt.assert_called_once_with('encrypted-key-123')
    
    def test_get_api_keys_encryption_failure(self):
        """Test getting API keys when decryption fails (assume plaintext)"""
        with patch.dict('os.environ', {'API_KEYS': 'plaintext-key'}):
            with patch('utils.api_keys.get_secrets_manager') as mock_secrets:
                mock_manager = Mock()
                mock_manager.decrypt = Mock(side_effect=Exception("Decryption failed"))
                mock_secrets.return_value = mock_manager
                
                keys = get_api_keys()
                assert keys == ['plaintext-key']
    
    def test_validate_api_key_valid(self):
        """Test validating a valid API key"""
        with patch('utils.api_keys.get_api_keys', return_value=['key1', 'key2', 'key3']):
            assert validate_api_key('key1') is True
            assert validate_api_key('key2') is True
            assert validate_api_key('key3') is True
    
    def test_validate_api_key_invalid(self):
        """Test validating an invalid API key"""
        with patch('utils.api_keys.get_api_keys', return_value=['key1', 'key2']):
            assert validate_api_key('invalid-key') is False
            assert validate_api_key('key3') is False
    
    def test_validate_api_key_empty(self):
        """Test validating empty API key"""
        with patch('utils.api_keys.get_api_keys', return_value=['key1']):
            assert validate_api_key('') is False
            assert validate_api_key(None) is False
    
    def test_get_api_key_from_header_bearer(self):
        """Test extracting API key from Bearer header"""
        assert get_api_key_from_header('Bearer test-key-123') == 'test-key-123'
        assert get_api_key_from_header('bearer test-key-123') == 'test-key-123'
        assert get_api_key_from_header('BEARER test-key-123') == 'test-key-123'
    
    def test_get_api_key_from_header_apikey(self):
        """Test extracting API key from ApiKey header"""
        assert get_api_key_from_header('ApiKey test-key-123') == 'test-key-123'
        assert get_api_key_from_header('apikey test-key-123') == 'test-key-123'
        assert get_api_key_from_header('API-KEY test-key-123') == 'test-key-123'
    
    def test_get_api_key_from_header_no_prefix(self):
        """Test extracting API key without prefix"""
        assert get_api_key_from_header('test-key-123') == 'test-key-123'
        assert get_api_key_from_header('  test-key-123  ') == 'test-key-123'
    
    def test_get_api_key_from_header_invalid_format(self):
        """Test extracting API key from invalid format"""
        assert get_api_key_from_header('InvalidFormat') == 'InvalidFormat'
        # When only "Bearer" is provided, it returns the whole string (no space to split)
        assert get_api_key_from_header('Bearer') == 'Bearer'  # Function returns whole string if no space
        # When "Bearer key1 key2" is provided, it splits and takes parts[1] which is 'key1'
        # But the function splits by space, so "Bearer key1 key2" -> ['Bearer', 'key1', 'key2']
        # len(parts) == 3, not 2, so it falls through to return the whole string
        assert get_api_key_from_header('Bearer key1 key2') == 'Bearer key1 key2'  # Returns whole string if len != 2
    
    def test_get_api_key_from_header_none(self):
        """Test extracting API key from None"""
        assert get_api_key_from_header(None) is None
        assert get_api_key_from_header('') is None

