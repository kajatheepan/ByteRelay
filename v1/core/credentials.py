from cryptography.fernet import Fernet

from core.config import settings

# Built once at import time; raises immediately if encryption_key is malformed.
_fernet = Fernet(settings.encryption_key.encode())


def encrypt_password(plain: str) -> str:
    return _fernet.encrypt(plain.encode()).decode()


def decrypt_password(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
