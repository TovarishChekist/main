"""
Message and data validators
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, validator


class MessageValidator:
    """
    Validates messages and cryptographic data
    """

    @staticmethod
    def validate_message_length(message: str, max_length: int = 4096) -> bool:
        """
        Validate message length

        Args:
            message: Message to validate
            max_length: Maximum allowed length

        Returns:
            True if valid
        """
        return 0 < len(message) <= max_length

    @staticmethod
    def validate_key_format(key: str) -> bool:
        """
        Validate cryptographic key format (base64)

        Args:
            key: Key to validate

        Returns:
            True if valid base64
        """
        pattern = r'^[A-Za-z0-9+/]+=*$'
        return bool(re.match(pattern, key))

    @staticmethod
    def validate_cipher_type(cipher_type: str) -> bool:
        """
        Validate cipher type

        Args:
            cipher_type: Cipher algorithm name

        Returns:
            True if supported
        """
        supported = ['AES-256-GCM', 'ChaCha20-Poly1305']
        return cipher_type in supported

    @staticmethod
    def sanitize_session_id(session_id: str) -> str:
        """
        Sanitize session identifier

        Args:
            session_id: Raw session ID

        Returns:
            Sanitized session ID
        """
        # Remove non-alphanumeric characters
        return re.sub(r'[^a-zA-Z0-9_-]', '', session_id)


class EncryptionRequest(BaseModel):
    """Validation model for encryption requests"""

    message: str = Field(..., min_length=1, max_length=4096)
    cipher_type: str = Field(default="AES-256-GCM")
    use_steganography: bool = Field(default=False)

    @validator('cipher_type')
    def validate_cipher(cls, v):
        if v not in ['AES-256-GCM', 'ChaCha20-Poly1305']:
            raise ValueError('Unsupported cipher type')
        return v


class DecryptionRequest(BaseModel):
    """Validation model for decryption requests"""

    encrypted_data: str = Field(..., min_length=1)
    session_id: Optional[str] = None

    @validator('encrypted_data')
    def validate_encrypted(cls, v):
        # Basic validation - must be base64-like
        pattern = r'^[A-Za-z0-9+/=|]+$'
        if not re.match(pattern, v):
            raise ValueError('Invalid encrypted data format')
        return v
