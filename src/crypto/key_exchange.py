"""
Key Exchange Module using ECDH and X25519
Implements Perfect Forward Secrecy with ephemeral keys
"""

import secrets
import base64
from typing import Tuple, Dict, Optional
from datetime import datetime, timedelta

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


class KeyExchangeManager:
    """
    Manages cryptographic key exchange using X25519 (Curve25519)
    Features:
    - Elliptic Curve Diffie-Hellman (ECDH)
    - Perfect Forward Secrecy with ephemeral keys
    - Key derivation using HKDF
    - Automatic key rotation
    """

    def __init__(self, key_lifetime_hours: int = 24):
        """
        Initialize key exchange manager

        Args:
            key_lifetime_hours: Hours before ephemeral keys expire
        """
        self.key_lifetime = timedelta(hours=key_lifetime_hours)
        self.sessions: Dict[str, Dict] = {}

    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate X25519 keypair for ECDH

        Returns:
            Tuple of (private_key, public_key) as bytes
        """
        # Generate private key
        private_key = x25519.X25519PrivateKey.generate()

        # Derive public key
        public_key = private_key.public_key()

        # Serialize keys to bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return private_bytes, public_bytes

    def derive_shared_secret(self, private_key_bytes: bytes, peer_public_key_bytes: bytes) -> bytes:
        """
        Derive shared secret using ECDH

        Args:
            private_key_bytes: Our private key (32 bytes)
            peer_public_key_bytes: Peer's public key (32 bytes)

        Returns:
            Shared secret (32 bytes)
        """
        # Load private key
        private_key = x25519.X25519PrivateKey.from_private_bytes(private_key_bytes)

        # Load peer's public key
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key_bytes)

        # Perform ECDH to derive shared secret
        shared_secret = private_key.exchange(peer_public_key)

        return shared_secret

    def derive_encryption_key(self, shared_secret: bytes, salt: Optional[bytes] = None,
                             info: bytes = b"telegram-encryption-bot") -> Tuple[bytes, bytes]:
        """
        Derive encryption key from shared secret using HKDF

        Args:
            shared_secret: Shared secret from ECDH
            salt: Optional salt (generated if not provided)
            info: Context information for key derivation

        Returns:
            Tuple of (encryption_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        # Use HKDF (HMAC-based Key Derivation Function) with SHA-256
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            info=info,
            backend=default_backend()
        )

        encryption_key = hkdf.derive(shared_secret)

        return encryption_key, salt

    def create_session(self, session_id: str, peer_public_key: str) -> Dict[str, str]:
        """
        Create new encrypted session with Perfect Forward Secrecy

        Args:
            session_id: Unique session identifier (e.g., chat_id)
            peer_public_key: Base64-encoded peer's public key

        Returns:
            Dictionary with our public key and session info
        """
        # Generate ephemeral keypair for this session
        private_key, public_key = self.generate_keypair()

        # Decode peer's public key
        peer_public_bytes = base64.b64decode(peer_public_key)

        # Derive shared secret
        shared_secret = self.derive_shared_secret(private_key, peer_public_bytes)

        # Derive encryption key with HKDF
        encryption_key, salt = self.derive_encryption_key(shared_secret)

        # Store session
        self.sessions[session_id] = {
            'private_key': private_key,
            'public_key': public_key,
            'peer_public_key': peer_public_bytes,
            'encryption_key': encryption_key,
            'salt': salt,
            'created_at': datetime.now(),
            'shared_secret': shared_secret
        }

        return {
            'public_key': base64.b64encode(public_key).decode(),
            'salt': base64.b64encode(salt).decode(),
            'session_id': session_id,
            'created_at': self.sessions[session_id]['created_at'].isoformat()
        }

    def get_session_key(self, session_id: str) -> Optional[bytes]:
        """
        Retrieve encryption key for session

        Args:
            session_id: Session identifier

        Returns:
            Encryption key or None if session doesn't exist/expired
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # Check if session expired
        if datetime.now() - session['created_at'] > self.key_lifetime:
            self.delete_session(session_id)
            return None

        return session['encryption_key']

    def rotate_session_key(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Rotate session key (Perfect Forward Secrecy)

        Args:
            session_id: Session identifier

        Returns:
            New session info or None if session doesn't exist
        """
        if session_id not in self.sessions:
            return None

        old_session = self.sessions[session_id]
        peer_public_key = base64.b64encode(old_session['peer_public_key']).decode()

        # Delete old session
        self.delete_session(session_id)

        # Create new session with new ephemeral keys
        return self.create_session(session_id, peer_public_key)

    def delete_session(self, session_id: str) -> None:
        """
        Securely delete session and keys

        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # Securely overwrite sensitive data
            if isinstance(session['private_key'], bytes):
                # Convert to bytearray for secure deletion
                sensitive_data = bytearray(session['private_key'])
                self._secure_overwrite(sensitive_data)

            if isinstance(session['encryption_key'], bytes):
                sensitive_data = bytearray(session['encryption_key'])
                self._secure_overwrite(sensitive_data)

            if isinstance(session['shared_secret'], bytes):
                sensitive_data = bytearray(session['shared_secret'])
                self._secure_overwrite(sensitive_data)

            # Remove session
            del self.sessions[session_id]

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions

        Returns:
            Number of sessions deleted
        """
        expired = []
        now = datetime.now()

        for session_id, session in self.sessions.items():
            if now - session['created_at'] > self.key_lifetime:
                expired.append(session_id)

        for session_id in expired:
            self.delete_session(session_id)

        return len(expired)

    @staticmethod
    def _secure_overwrite(data: bytearray) -> None:
        """
        Securely overwrite memory

        Args:
            data: Bytearray to overwrite
        """
        # Multiple overwrite passes for security
        for _ in range(3):
            for i in range(len(data)):
                data[i] = secrets.randbelow(256)

        # Final zero pass
        for i in range(len(data)):
            data[i] = 0

    def export_public_key(self, session_id: str) -> Optional[str]:
        """
        Export public key for session

        Args:
            session_id: Session identifier

        Returns:
            Base64-encoded public key or None
        """
        if session_id not in self.sessions:
            return None

        return base64.b64encode(self.sessions[session_id]['public_key']).decode()

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session information (without sensitive data)

        Args:
            session_id: Session identifier

        Returns:
            Session info dictionary or None
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        age = datetime.now() - session['created_at']

        return {
            'session_id': session_id,
            'created_at': session['created_at'].isoformat(),
            'age_seconds': int(age.total_seconds()),
            'expires_in_seconds': int((self.key_lifetime - age).total_seconds()),
            'is_expired': age > self.key_lifetime
        }
