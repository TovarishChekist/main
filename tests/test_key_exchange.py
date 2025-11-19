"""
Tests for key exchange and forward secrecy
"""

import pytest
import base64
from src.crypto.key_exchange import KeyExchangeManager


class TestKeyExchange:
    """Test ECDH key exchange"""

    def setup_method(self):
        """Setup test fixtures"""
        self.key_manager = KeyExchangeManager(key_lifetime_hours=24)

    def test_keypair_generation(self):
        """Test X25519 keypair generation"""
        private_key, public_key = self.key_manager.generate_keypair()

        # Check key lengths (X25519 uses 32-byte keys)
        assert len(private_key) == 32
        assert len(public_key) == 32

        # Keys should be different
        assert private_key != public_key

    def test_shared_secret_derivation(self):
        """Test ECDH shared secret derivation"""
        # Alice generates keypair
        alice_private, alice_public = self.key_manager.generate_keypair()

        # Bob generates keypair
        bob_private, bob_public = self.key_manager.generate_keypair()

        # Alice derives shared secret with Bob's public key
        alice_shared = self.key_manager.derive_shared_secret(alice_private, bob_public)

        # Bob derives shared secret with Alice's public key
        bob_shared = self.key_manager.derive_shared_secret(bob_private, alice_public)

        # Both should derive the same shared secret
        assert alice_shared == bob_shared
        assert len(alice_shared) == 32

    def test_encryption_key_derivation(self):
        """Test HKDF key derivation"""
        shared_secret = b"X" * 32

        # Derive encryption key
        key, salt = self.key_manager.derive_encryption_key(shared_secret)

        # Check key properties
        assert len(key) == 32  # 256 bits for AES-256
        assert len(salt) == 32

        # Same secret and salt should produce same key
        key2, _ = self.key_manager.derive_encryption_key(shared_secret, salt)
        assert key == key2

    def test_session_creation(self):
        """Test E2EE session creation"""
        # Bob generates his keypair
        bob_private, bob_public = self.key_manager.generate_keypair()
        bob_public_b64 = base64.b64encode(bob_public).decode()

        # Alice creates session with Bob
        session_info = self.key_manager.create_session("alice_123", bob_public_b64)

        # Check session info
        assert 'public_key' in session_info
        assert 'salt' in session_info
        assert 'session_id' in session_info
        assert session_info['session_id'] == "alice_123"

    def test_session_key_retrieval(self):
        """Test session key retrieval"""
        # Create session
        bob_private, bob_public = self.key_manager.generate_keypair()
        bob_public_b64 = base64.b64encode(bob_public).decode()

        session_info = self.key_manager.create_session("alice_123", bob_public_b64)

        # Retrieve session key
        key = self.key_manager.get_session_key("alice_123")

        assert key is not None
        assert len(key) == 32

    def test_session_deletion(self):
        """Test secure session deletion"""
        # Create session
        bob_private, bob_public = self.key_manager.generate_keypair()
        bob_public_b64 = base64.b64encode(bob_public).decode()

        self.key_manager.create_session("alice_123", bob_public_b64)

        # Delete session
        self.key_manager.delete_session("alice_123")

        # Key should no longer be retrievable
        key = self.key_manager.get_session_key("alice_123")
        assert key is None

    def test_session_rotation(self):
        """Test session key rotation (Perfect Forward Secrecy)"""
        # Create initial session
        bob_private, bob_public = self.key_manager.generate_keypair()
        bob_public_b64 = base64.b64encode(bob_public).decode()

        session1 = self.key_manager.create_session("alice_123", bob_public_b64)
        key1 = self.key_manager.get_session_key("alice_123")

        # Rotate session
        session2 = self.key_manager.rotate_session_key("alice_123")
        key2 = self.key_manager.get_session_key("alice_123")

        # Keys should be different (Forward Secrecy)
        assert key1 != key2
        assert session1['public_key'] != session2['public_key']

    def test_multiple_sessions(self):
        """Test multiple concurrent sessions"""
        bob_private, bob_public = self.key_manager.generate_keypair()
        bob_public_b64 = base64.b64encode(bob_public).decode()

        # Create multiple sessions
        self.key_manager.create_session("user1", bob_public_b64)
        self.key_manager.create_session("user2", bob_public_b64)
        self.key_manager.create_session("user3", bob_public_b64)

        # All should have different keys
        key1 = self.key_manager.get_session_key("user1")
        key2 = self.key_manager.get_session_key("user2")
        key3 = self.key_manager.get_session_key("user3")

        assert key1 != key2
        assert key2 != key3
        assert key1 != key3

    def test_end_to_end_encryption_flow(self):
        """Test complete E2EE flow between two users"""
        from src.crypto.encryptor import AdvancedEncryptor

        encryptor = AdvancedEncryptor()

        # Alice and Bob generate keypairs
        alice_private, alice_public = self.key_manager.generate_keypair()
        bob_private, bob_public = self.key_manager.generate_keypair()

        # Exchange public keys and derive shared secrets
        alice_shared = self.key_manager.derive_shared_secret(alice_private, bob_public)
        bob_shared = self.key_manager.derive_shared_secret(bob_private, alice_public)

        # Derive encryption keys
        alice_key, salt = self.key_manager.derive_encryption_key(alice_shared)
        bob_key, _ = self.key_manager.derive_encryption_key(bob_shared, salt)

        # Keys should match
        assert alice_key == bob_key

        # Alice encrypts a message
        message = b"Secret message from Alice to Bob"
        encrypted = encryptor.encrypt(message, key=alice_key)

        # Bob decrypts the message
        decrypted = encryptor.decrypt(encrypted, key=bob_key)

        assert decrypted == message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
