import sys
from cryptography.fernet import Fernet
from app.core.config import settings

ENCRYPTION_KEY = settings.ENCRYPTION_KEY

if not ENCRYPTION_KEY:
    print("CRITICAL ERROR: ENCRYPTION_KEY is missing from environment variables or .env file.")
    sys.exit(1)

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

class TokenEncryptor:
    """Encapsulates token obfuscation logic in a single reusable component (SRP)."""
    
    @staticmethod
    def encrypt(token: str) -> str:
        if not token:
            return None
        return cipher_suite.encrypt(token.encode()).decode()

    @staticmethod
    def decrypt(encrypted_token: str) -> str:
        if not encrypted_token:
            return None
        return cipher_suite.decrypt(encrypted_token.encode()).decode()