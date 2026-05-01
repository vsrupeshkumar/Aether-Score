#!/usr/bin/env python3
"""
Security setup script
Generates encryption keys and JWT secrets for AETHER-SCORE backend
"""
import os
import secrets
from cryptography.fernet import Fernet
from pathlib import Path

def generate_encryption_key():
    """Generate Fernet encryption key"""
    return Fernet.generate_key().decode()

def generate_jwt_secret():
    """Generate JWT secret key"""
    return secrets.token_urlsafe(32)

def generate_api_key():
    """Generate API key"""
    return secrets.token_urlsafe(32)

def main():
    print("ðŸ” AETHER-SCORE Security Setup")
    print("=" * 50)
    
    # Generate keys
    encryption_key = generate_encryption_key()
    jwt_secret = generate_jwt_secret()
    api_key = generate_api_key()
    
    print("\nâœ… Generated Security Keys:")
    print(f"\n1. SECRETS_ENCRYPTION_KEY:")
    print(f"   {encryption_key}")
    
    print(f"\n2. JWT_SECRET_KEY:")
    print(f"   {jwt_secret}")
    
    print(f"\n3. API_KEYS (example):")
    print(f"   {api_key}")
    
    print("\nðŸ“ Next Steps:")
    print("1. Add these values to your backend/.env file")
    print("2. Keep these keys secure - never commit them to git")
    print("3. Use different keys for production and development")
    print("4. Rotate keys periodically for security")
    
    # Optionally write to a secure file (not .env, user should copy manually)
    secure_file = Path(".env.security.keys")
    if not secure_file.exists():
        with open(secure_file, "w") as f:
            f.write("# Security Keys - DO NOT COMMIT TO GIT\n")
            f.write("# Copy these to your .env file\n\n")
            f.write(f"SECRETS_ENCRYPTION_KEY={encryption_key}\n")
            f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
            f.write(f"API_KEYS={api_key}\n")
        print(f"\nðŸ’¾ Keys also saved to: {secure_file}")
        print("   (This file is gitignored - safe to keep locally)")
    
    print("\nâš ï¸  IMPORTANT:")
    print("   - Add .env.security.keys to .gitignore if not already there")
    print("   - Delete this file after copying keys to .env")
    print("   - Never share these keys publicly")

if __name__ == "__main__":
    main()


