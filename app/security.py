"""
Security utilities for CopyPasta using Windows DPAPI (Data Protection API).
Provides seamless, hardware/OS-backed encryption tied to the Windows user account.
"""

import sys
import os

try:
    import win32crypt
    HAS_WIN32CRYPT = True
except ImportError:
    HAS_WIN32CRYPT = False

# Fallback in case DPAPI has an issue (using cryptography library)
from cryptography.fernet import Fernet
import base64
import hashlib


def _get_fallback_key() -> bytes:
    """Generate a stable machine-bound key for fallback encryption."""
    user = os.environ.get("USERNAME", "default_user")
    computer = os.environ.get("COMPUTERNAME", "default_host")
    raw = f"CopyPastaFallbackKey:{user}@{computer}".encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest())


def encrypt_string(plaintext: str, description: str = "CopyPasta 2FA Secret") -> bytes:
    """
    Encrypt a string using Windows DPAPI (CryptProtectData).
    Returns ciphertext as bytes.
    """
    if not plaintext:
        return b""
    raw_data = plaintext.encode("utf-8")
    if HAS_WIN32CRYPT:
        try:
            return win32crypt.CryptProtectData(raw_data, description, None, None, None, 0)
        except Exception as e:
            print(f"[Security] DPAPI encryption warning: {e}. Falling back to Fernet.")
    
    # Fallback encryption
    f = Fernet(_get_fallback_key())
    return b"FALLBACK:" + f.encrypt(raw_data)


def decrypt_string(ciphertext: bytes) -> str:
    """
    Decrypt bytes encrypted by encrypt_string using Windows DPAPI (CryptUnprotectData).
    Returns decrypted string.
    """
    if not ciphertext:
        return ""
    if ciphertext.startswith(b"FALLBACK:"):
        f = Fernet(_get_fallback_key())
        return f.decrypt(ciphertext[9:]).decode("utf-8")
    
    if HAS_WIN32CRYPT:
        try:
            _, decrypted_bytes = win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            print(f"[Security] DPAPI decryption error: {e}")
            raise
    
    raise RuntimeError("Cannot decrypt: win32crypt not available and data is not fallback-encrypted")
