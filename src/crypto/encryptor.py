"""
Advanced Encryption Module with multiple cipher support
Implements: AES-256-GCM, ChaCha20-Poly1305, RSA-OAEP
"""

import os
import base64
import secrets
import hashlib
from typing import Tuple, Optional, Dict
from enum import Enum

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from Crypto.Cipher import AES
from argon2 import PasswordHasher
from argon2.low_level import hash_secret_raw, Type


class CipherType(Enum):
    """Supported cipher algorithms"""
    AES_256_GCM = "AES-256-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    AES_256_CBC = "AES-256-CBC"  # Legacy support


class AdvancedEncryptor:
    """
    Advanced encryption engine with multiple cipher support
    Features:
    - AES-256-GCM (primary)
    - ChaCha20-Poly1305 (alternative)
    - RSA-4096 for key exchange
    - Argon2 key derivation
    - Authenticated encryption
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryptor with optional master key

        Args:
            master_key: 32-byte master encryption key
        """
        self.master_key = master_key or secrets.token_bytes(32)
        self.ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16
        )

    def derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using Argon2id

        Args:
            password: User password
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)

        # Use Argon2id for key derivation (resistance to GPU attacks)
        key = hash_secret_raw(
            secret=password.encode(),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID
        )

        return key, salt

    def encrypt_aes_gcm(self, plaintext: bytes, key: Optional[bytes] = None) -> Dict[str, bytes]:
        """
        Encrypt data using AES-256-GCM (Authenticated Encryption)

        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key (uses master_key if not provided)

        Returns:
            Dictionary with ciphertext, nonce, and tag
        """
        key = key or self.master_key

        # Generate random 96-bit nonce (recommended for GCM)
        nonce = secrets.token_bytes(12)

        # Create AES-GCM cipher
        aesgcm = AESGCM(key)

        # Encrypt and authenticate
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'algorithm': CipherType.AES_256_GCM.value.encode()
        }

    def decrypt_aes_gcm(self, encrypted_data: Dict[str, bytes], key: Optional[bytes] = None) -> bytes:
        """
        Decrypt AES-256-GCM encrypted data

        Args:
            encrypted_data: Dictionary with ciphertext and nonce
            key: 32-byte encryption key

        Returns:
            Decrypted plaintext

        Raises:
            Exception: If authentication fails or data is corrupted
        """
        key = key or self.master_key

        aesgcm = AESGCM(key)

        try:
            plaintext = aesgcm.decrypt(
                encrypted_data['nonce'],
                encrypted_data['ciphertext'],
                None
            )
            return plaintext
        except Exception as e:
            raise ValueError(f"Decryption failed: authentication error or corrupted data") from e

    def encrypt_chacha20(self, plaintext: bytes, key: Optional[bytes] = None) -> Dict[str, bytes]:
        """
        Encrypt data using ChaCha20-Poly1305 (faster on mobile devices)

        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key

        Returns:
            Dictionary with ciphertext and nonce
        """
        key = key or self.master_key

        # Generate random 96-bit nonce
        nonce = secrets.token_bytes(12)

        # Create ChaCha20-Poly1305 cipher
        chacha = ChaCha20Poly1305(key)

        # Encrypt and authenticate
        ciphertext = chacha.encrypt(nonce, plaintext, None)

        return {
            'ciphertext': ciphertext,
            'nonce': nonce,
            'algorithm': CipherType.CHACHA20_POLY1305.value.encode()
        }

    def decrypt_chacha20(self, encrypted_data: Dict[str, bytes], key: Optional[bytes] = None) -> bytes:
        """
        Decrypt ChaCha20-Poly1305 encrypted data

        Args:
            encrypted_data: Dictionary with ciphertext and nonce
            key: 32-byte encryption key

        Returns:
            Decrypted plaintext
        """
        key = key or self.master_key

        chacha = ChaCha20Poly1305(key)

        try:
            plaintext = chacha.decrypt(
                encrypted_data['nonce'],
                encrypted_data['ciphertext'],
                None
            )
            return plaintext
        except Exception as e:
            raise ValueError(f"Decryption failed: authentication error") from e

    def encrypt(self, plaintext: bytes, cipher_type: CipherType = CipherType.AES_256_GCM,
                key: Optional[bytes] = None) -> str:
        """
        Universal encryption method with algorithm selection

        Args:
            plaintext: Data to encrypt
            cipher_type: Cipher algorithm to use
            key: Optional encryption key

        Returns:
            Base64-encoded encrypted data bundle
        """
        if cipher_type == CipherType.AES_256_GCM:
            encrypted = self.encrypt_aes_gcm(plaintext, key)
        elif cipher_type == CipherType.CHACHA20_POLY1305:
            encrypted = self.encrypt_chacha20(plaintext, key)
        else:
            raise ValueError(f"Unsupported cipher type: {cipher_type}")

        # Bundle all components
        bundle = (
            encrypted['algorithm'] + b'||' +
            encrypted['nonce'] + b'||' +
            encrypted['ciphertext']
        )

        return base64.b64encode(bundle).decode()

    def decrypt(self, encrypted_bundle: str, key: Optional[bytes] = None) -> bytes:
        """
        Universal decryption method with automatic algorithm detection

        Args:
            encrypted_bundle: Base64-encoded encrypted data bundle
            key: Optional encryption key

        Returns:
            Decrypted plaintext
        """
        try:
            # Decode bundle
            bundle = base64.b64decode(encrypted_bundle.encode())

            # Parse components
            parts = bundle.split(b'||')
            algorithm = parts[0].decode()
            nonce = parts[1]
            ciphertext = parts[2]

            encrypted_data = {
                'nonce': nonce,
                'ciphertext': ciphertext
            }

            # Decrypt based on algorithm
            if algorithm == CipherType.AES_256_GCM.value:
                return self.decrypt_aes_gcm(encrypted_data, key)
            elif algorithm == CipherType.CHACHA20_POLY1305.value:
                return self.decrypt_chacha20(encrypted_data, key)
            else:
                raise ValueError(f"Unknown cipher algorithm: {algorithm}")

        except Exception as e:
            raise ValueError(f"Decryption error: {str(e)}") from e

    def generate_rsa_keypair(self, key_size: int = 4096) -> Tuple[bytes, bytes]:
        """
        Generate RSA keypair for asymmetric encryption

        Args:
            key_size: RSA key size (2048, 3072, or 4096)

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        # Serialize to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    def encrypt_rsa(self, plaintext: bytes, public_key_pem: bytes) -> bytes:
        """
        Encrypt data using RSA-OAEP (for small data like keys)

        Args:
            plaintext: Data to encrypt (max ~470 bytes for 4096-bit key)
            public_key_pem: RSA public key in PEM format

        Returns:
            Encrypted ciphertext
        """
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())

        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return ciphertext

    def decrypt_rsa(self, ciphertext: bytes, private_key_pem: bytes) -> bytes:
        """
        Decrypt RSA-OAEP encrypted data

        Args:
            ciphertext: Encrypted data
            private_key_pem: RSA private key in PEM format

        Returns:
            Decrypted plaintext
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )

        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return plaintext

    @staticmethod
    def secure_delete(data: bytearray) -> None:
        """
        Securely overwrite memory before deletion

        Args:
            data: Bytearray to securely erase
        """
        if isinstance(data, bytearray):
            # Overwrite with random data
            for i in range(len(data)):
                data[i] = secrets.randbelow(256)
            # Overwrite with zeros
            for i in range(len(data)):
                data[i] = 0

    @staticmethod
    def hash_data(data: bytes, algorithm: str = 'sha256') -> str:
        """
        Hash data using specified algorithm

        Args:
            data: Data to hash
            algorithm: Hash algorithm (sha256, sha512, sha3_256)

        Returns:
            Hexadecimal hash digest
        """
        if algorithm == 'sha256':
            return hashlib.sha256(data).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data).hexdigest()
        elif algorithm == 'sha3_256':
            return hashlib.sha3_256(data).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
