"""Security utilities for encryption and decryption.

Used primarily for encrypting LLM provider API keys at rest.
Keys are encrypted before database storage and decrypted only
when needed for API calls.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_fernet() -> Fernet:
    """Create a Fernet cipher from the configured encryption key."""
    key = get_settings().encryption_key
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value (e.g., API key) for database storage.

    Args:
        plaintext: The value to encrypt.

    Returns:
        Base64-encoded encrypted string.
    """
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """Decrypt a previously encrypted value.

    Args:
        encrypted: Base64-encoded encrypted string from the database.

    Returns:
        Original plaintext value.

    Raises:
        ValueError: If decryption fails (wrong key or corrupted data).
    """
    try:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted.encode()).decode()
    except InvalidToken as exc:
        logger.error("decryption_failed", error=str(exc))
        raise ValueError("Failed to decrypt value — encryption key may have changed") from exc