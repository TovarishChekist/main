"""
Tests for encryption module
"""

import pytest
from src.crypto.encryptor import AdvancedEncryptor, CipherType


class TestEncryption:
    """Test encryption functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.encryptor = AdvancedEncryptor()
        self.test_message = b"This is a secret message!"

    def test_aes_gcm_encryption_decryption(self):
        """Test AES-256-GCM encryption and decryption"""
        # Encrypt
        encrypted = self.encryptor.encrypt(self.test_message, CipherType.AES_256_GCM)

        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

        # Decrypt
        decrypted = self.encryptor.decrypt(encrypted)

        assert decrypted == self.test_message

    def test_chacha20_encryption_decryption(self):
        """Test ChaCha20-Poly1305 encryption and decryption"""
        # Encrypt
        encrypted = self.encryptor.encrypt(self.test_message, CipherType.CHACHA20_POLY1305)

        assert encrypted is not None
        assert isinstance(encrypted, str)

        # Decrypt
        decrypted = self.encryptor.decrypt(encrypted)

        assert decrypted == self.test_message

    def test_encryption_with_different_keys(self):
        """Test that different keys produce different ciphertexts"""
        key1 = b"0" * 32
        key2 = b"1" * 32

        encrypted1 = self.encryptor.encrypt(self.test_message, key=key1)
        encrypted2 = self.encryptor.encrypt(self.test_message, key=key2)

        # Different keys should produce different ciphertexts
        assert encrypted1 != encrypted2

    def test_tampered_ciphertext_rejection(self):
        """Test that tampered ciphertext is rejected"""
        encrypted = self.encryptor.encrypt(self.test_message)

        # Tamper with ciphertext
        tampered = encrypted[:-10] + "XXXXXXXXXX"

        # Decryption should fail
        with pytest.raises(ValueError):
            self.encryptor.decrypt(tampered)

    def test_rsa_encryption_decryption(self):
        """Test RSA encryption and decryption"""
        # Generate keypair
        private_key, public_key = self.encryptor.generate_rsa_keypair(2048)

        # Test message (small, as RSA has size limits)
        message = b"Secret key"

        # Encrypt
        ciphertext = self.encryptor.encrypt_rsa(message, public_key)
        assert len(ciphertext) > 0

        # Decrypt
        decrypted = self.encryptor.decrypt_rsa(ciphertext, private_key)
        assert decrypted == message

    def test_key_derivation(self):
        """Test key derivation from password"""
        password = "MySecurePassword123!"

        # Derive key
        key1, salt = self.encryptor.derive_key(password)

        assert len(key1) == 32  # 256 bits
        assert len(salt) == 16

        # Same password and salt should produce same key
        key2, _ = self.encryptor.derive_key(password, salt)
        assert key1 == key2

        # Different salt should produce different key
        key3, _ = self.encryptor.derive_key(password)
        assert key1 != key3

    def test_hash_data(self):
        """Test data hashing"""
        data = b"Data to hash"

        # SHA-256
        hash1 = self.encryptor.hash_data(data, 'sha256')
        assert len(hash1) == 64  # 256 bits = 64 hex chars

        # SHA-512
        hash2 = self.encryptor.hash_data(data, 'sha512')
        assert len(hash2) == 128  # 512 bits = 128 hex chars

        # Same data should produce same hash
        hash3 = self.encryptor.hash_data(data, 'sha256')
        assert hash1 == hash3

    def test_empty_message(self):
        """Test handling of empty messages"""
        empty_message = b""

        # Should handle empty message
        encrypted = self.encryptor.encrypt(empty_message)
        decrypted = self.encryptor.decrypt(encrypted)

        assert decrypted == empty_message

    def test_large_message(self):
        """Test encryption of large messages"""
        large_message = b"X" * 10000

        encrypted = self.encryptor.encrypt(large_message)
        decrypted = self.encryptor.decrypt(encrypted)

        assert decrypted == large_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
