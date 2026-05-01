"""
Encrypted secrets management
Uses Fernet (symmetric encryption) to encrypt sensitive values
"""
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

class SecretsManager:
    """Manages encrypted secrets"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize secrets manager
        
        Args:
            encryption_key: 32-byte key for encryption (or env var SECRETS_ENCRYPTION_KEY)
        """
        key = encryption_key or os.getenv("SECRETS_ENCRYPTION_KEY")
        
        if not key:
            # Generate a key from a passphrase (not recommended for production)
            # In production, SECRETS_ENCRYPTION_KEY should be set explicitly
            passphrase = os.getenv("SECRETS_PASSPHRASE", "default-passphrase-change-in-production")
            key = self._derive_key_from_passphrase(passphrase)
        
        # Ensure key is 32 bytes
        if len(key) < 32:
            key = key.ljust(32, '0')[:32]
        elif len(key) > 32:
            key = key[:32]
        
        # Convert to Fernet key format
        self.fernet_key = base64.urlsafe_b64encode(key.encode() if isinstance(key, str) else key)
        self.cipher = Fernet(self.fernet_key)
    
    def _derive_key_from_passphrase(self, passphrase: str) -> bytes:
        """Derive encryption key from passphrase"""
        salt = b'AETHER-SCORE_salt_2025'  # Should be random in production
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        return key
    
    def encrypt(self, value: str) -> str:
        """
        Encrypt a secret value
        
        Args:
            value: Plaintext value to encrypt
            
        Returns:
            Encrypted value (base64 encoded)
        """
        if not value:
            return ""
        
        encrypted = self.cipher.encrypt(value.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt a secret value
        
        Args:
            encrypted_value: Encrypted value (base64 encoded)
            
        Returns:
            Decrypted plaintext value
        """
        if not encrypted_value:
            return ""
        
        try:
            decrypted = self.cipher.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt value: {str(e)}")
    
    def get_secret(self, env_var: str, encrypted: bool = False) -> Optional[str]:
        """
        Get secret from environment variable, decrypting if needed
        
        Args:
            env_var: Environment variable name
            encrypted: Whether the value is encrypted
            
        Returns:
            Decrypted secret or None if not found
        """
        value = os.getenv(env_var)
        if not value:
            return None
        
        if encrypted:
            try:
                return self.decrypt(value)
            except Exception:
                # If decryption fails, assume it's plaintext (backward compatibility)
                return value
        
        return value

# Global instance
_secrets_manager: Optional[SecretsManager] = None

def get_secrets_manager() -> SecretsManager:
    """Get or create global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


