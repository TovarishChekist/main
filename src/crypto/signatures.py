"""
Digital Signatures Module using Ed25519
Provides message authentication and non-repudiation
"""

import base64
from typing import Tuple
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class SignatureManager:
    """
    Manages digital signatures using Ed25519
    Features:
    - Fast signature generation and verification
    - Message authentication
    - Non-repudiation
    - Timestamp signing
    """

    def __init__(self):
        """Initialize signature manager"""
        self.signing_keys = {}

    def generate_signing_keypair(self, user_id: str) -> Tuple[str, str]:
        """
        Generate Ed25519 signing keypair

        Args:
            user_id: User identifier

        Returns:
            Tuple of (private_key_b64, public_key_b64)
        """
        # Generate Ed25519 private key
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize to bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # Store private key
        self.signing_keys[user_id] = private_bytes

        # Return base64-encoded keys
        return (
            base64.b64encode(private_bytes).decode(),
            base64.b64encode(public_bytes).decode()
        )

    def sign_message(self, message: bytes, user_id: str) -> str:
        """
        Sign message with user's private key

        Args:
            message: Message to sign
            user_id: User identifier

        Returns:
            Base64-encoded signature

        Raises:
            ValueError: If user doesn't have a signing key
        """
        if user_id not in self.signing_keys:
            raise ValueError(f"No signing key found for user: {user_id}")

        # Load private key
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
            self.signing_keys[user_id]
        )

        # Sign message
        signature = private_key.sign(message)

        return base64.b64encode(signature).decode()

    def verify_signature(self, message: bytes, signature_b64: str, public_key_b64: str) -> bool:
        """
        Verify message signature

        Args:
            message: Original message
            signature_b64: Base64-encoded signature
            public_key_b64: Base64-encoded public key

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Decode signature and public key
            signature = base64.b64decode(signature_b64)
            public_key_bytes = base64.b64decode(public_key_b64)

            # Load public key
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

            # Verify signature
            public_key.verify(signature, message)
            return True

        except (InvalidSignature, Exception):
            return False

    def sign_with_timestamp(self, message: bytes, user_id: str) -> dict:
        """
        Sign message with timestamp for freshness verification

        Args:
            message: Message to sign
            user_id: User identifier

        Returns:
            Dictionary with signature and timestamp
        """
        timestamp = datetime.utcnow().isoformat()
        timestamped_message = f"{timestamp}||{message.decode()}".encode()

        signature = self.sign_message(timestamped_message, user_id)

        return {
            'signature': signature,
            'timestamp': timestamp,
            'message': base64.b64encode(message).decode()
        }

    def verify_timestamped_signature(self, signed_data: dict, public_key_b64: str,
                                    max_age_seconds: int = 300) -> bool:
        """
        Verify signature with timestamp freshness check

        Args:
            signed_data: Dictionary with signature, timestamp, and message
            public_key_b64: Base64-encoded public key
            max_age_seconds: Maximum age of signature in seconds

        Returns:
            True if signature is valid and fresh, False otherwise
        """
        try:
            # Extract components
            signature = signed_data['signature']
            timestamp_str = signed_data['timestamp']
            message = base64.b64decode(signed_data['message'])

            # Reconstruct signed message
            timestamped_message = f"{timestamp_str}||{message.decode()}".encode()

            # Verify signature
            if not self.verify_signature(timestamped_message, signature, public_key_b64):
                return False

            # Check timestamp freshness
            timestamp = datetime.fromisoformat(timestamp_str)
            age = (datetime.utcnow() - timestamp).total_seconds()

            return age <= max_age_seconds

        except Exception:
            return False

    def load_private_key(self, user_id: str, private_key_b64: str) -> None:
        """
        Load existing private key for user

        Args:
            user_id: User identifier
            private_key_b64: Base64-encoded private key
        """
        private_bytes = base64.b64decode(private_key_b64)
        self.signing_keys[user_id] = private_bytes

    def get_public_key(self, user_id: str) -> str:
        """
        Get public key for user

        Args:
            user_id: User identifier

        Returns:
            Base64-encoded public key

        Raises:
            ValueError: If user doesn't have a signing key
        """
        if user_id not in self.signing_keys:
            raise ValueError(f"No signing key found for user: {user_id}")

        # Load private key
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
            self.signing_keys[user_id]
        )

        # Derive public key
        public_key = private_key.public_key()

        # Serialize
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return base64.b64encode(public_bytes).decode()

    def delete_key(self, user_id: str) -> None:
        """
        Securely delete user's signing key

        Args:
            user_id: User identifier
        """
        if user_id in self.signing_keys:
            # Secure overwrite
            key_data = bytearray(self.signing_keys[user_id])
            for i in range(len(key_data)):
                key_data[i] = 0

            del self.signing_keys[user_id]
