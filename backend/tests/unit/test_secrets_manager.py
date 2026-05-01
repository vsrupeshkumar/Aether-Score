"""
Unit tests for secrets manager
"""
import pytest
import os
from unittest.mock import patch
from utils.secrets_manager import SecretsManager, get_secrets_manager


@pytest.mark.unit
class TestSecretsManager:
    """Test secrets manager"""
    
    @pytest.fixture
    def encryption_key(self):
        """Generate test encryption key"""
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    
    @pytest.fixture
    def secrets_manager(self, encryption_key):
        """Create SecretsManager instance"""
        return SecretsManager(encryption_key=encryption_key)
    
    def test_encrypt_decrypt(self, secrets_manager):
        """Test encryption and decryption"""
        plaintext = "my_secret_value_123"
        
        encrypted = secrets_manager.encrypt(plaintext)
        decrypted = secrets_manager.decrypt(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
        assert isinstance(encrypted, str)
        assert isinstance(decrypted, str)
    
    def test_encrypt_empty(self, secrets_manager):
        """Test encrypting empty string"""
        encrypted = secrets_manager.encrypt("")
        assert encrypted == ""
    
    def test_decrypt_empty(self, secrets_manager):
        """Test decrypting empty string"""
        decrypted = secrets_manager.decrypt("")
        assert decrypted == ""
    
    def test_decrypt_invalid(self, secrets_manager):
        """Test decrypting invalid encrypted value"""
        with pytest.raises(ValueError, match="Failed to decrypt"):
            secrets_manager.decrypt("invalid_encrypted_value")
    
    def test_decrypt_wrong_key(self, encryption_key):
        """Test decrypting with wrong key"""
        from cryptography.fernet import Fernet
        wrong_key = Fernet.generate_key().decode()
        
        manager1 = SecretsManager(encryption_key=encryption_key)
        manager2 = SecretsManager(encryption_key=wrong_key)
        
        plaintext = "my_secret_value_123"
        encrypted = manager1.encrypt(plaintext)
        
        # Should fail with wrong key
        with pytest.raises(ValueError):
            manager2.decrypt(encrypted)
    
    def test_get_secret_plaintext(self, secrets_manager):
        """Test getting plaintext secret from env"""
        with patch.dict(os.environ, {'TEST_SECRET': 'plaintext_value'}):
            value = secrets_manager.get_secret('TEST_SECRET', encrypted=False)
            assert value == 'plaintext_value'
    
    def test_get_secret_encrypted(self, secrets_manager):
        """Test getting encrypted secret from env"""
        plaintext = "my_secret_value_123"
        encrypted = secrets_manager.encrypt(plaintext)
        
        with patch.dict(os.environ, {'TEST_SECRET_ENCRYPTED': encrypted}):
            value = secrets_manager.get_secret('TEST_SECRET_ENCRYPTED', encrypted=True)
            assert value == plaintext
    
    def test_get_secret_not_found(self, secrets_manager):
        """Test getting secret that doesn't exist"""
        value = secrets_manager.get_secret('NONEXISTENT_SECRET')
        assert value is None
    
    def test_get_secret_decrypt_failure_fallback(self, secrets_manager):
        """Test fallback when decryption fails (assumes plaintext)"""
        # Set an encrypted value but try to decrypt with wrong assumption
        with patch.dict(os.environ, {'TEST_SECRET': 'not_encrypted_value'}):
            # If encrypted=True but value is plaintext, should return plaintext
            value = secrets_manager.get_secret('TEST_SECRET', encrypted=True)
            # Should return the value (fallback behavior)
            assert value is not None
    
    def test_get_secrets_manager_singleton(self):
        """Test that get_secrets_manager returns singleton"""
        manager1 = get_secrets_manager()
        manager2 = get_secrets_manager()
        
        assert manager1 is manager2
    
    def test_encrypt_different_values(self, secrets_manager):
        """Test that different values produce different encrypted outputs"""
        value1 = "secret1"
        value2 = "secret2"
        
        encrypted1 = secrets_manager.encrypt(value1)
        encrypted2 = secrets_manager.encrypt(value2)
        
        assert encrypted1 != encrypted2
    
    def test_encrypt_same_value_consistency(self, secrets_manager):
        """Test that same value can be encrypted and decrypted consistently"""
        value = "same_secret"
        
        encrypted1 = secrets_manager.encrypt(value)
        encrypted2 = secrets_manager.encrypt(value)
        
        # Fernet may or may not produce same output (depends on implementation)
        # What matters is that both can be decrypted correctly
        assert secrets_manager.decrypt(encrypted1) == value
        assert secrets_manager.decrypt(encrypted2) == value
        # Both should decrypt to the same value
        assert secrets_manager.decrypt(encrypted1) == secrets_manager.decrypt(encrypted2)
    
    def test_manager_with_env_key(self):
        """Test manager initialization with env key"""
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()
        
        with patch.dict(os.environ, {'SECRETS_ENCRYPTION_KEY': test_key}, clear=False):
            manager = SecretsManager()
            # Should use env key
            plaintext = "test_value"
            encrypted = manager.encrypt(plaintext)
            decrypted = manager.decrypt(encrypted)
            assert decrypted == plaintext

