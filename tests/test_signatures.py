"""
Tests for digital signatures
"""

import pytest
import time
from src.crypto.signatures import SignatureManager


class TestSignatures:
    """Test Ed25519 digital signatures"""

    def setup_method(self):
        """Setup test fixtures"""
        self.sig_manager = SignatureManager()

    def test_keypair_generation(self):
        """Test Ed25519 keypair generation"""
        user_id = "test_user"

        private_key, public_key = self.sig_manager.generate_signing_keypair(user_id)

        # Check that keys are generated
        assert len(private_key) > 0
        assert len(public_key) > 0

        # Keys should be different
        assert private_key != public_key

    def test_message_signing(self):
        """Test message signing"""
        user_id = "test_user"
        message = b"Important message"

        # Generate keys
        self.sig_manager.generate_signing_keypair(user_id)

        # Sign message
        signature = self.sig_manager.sign_message(message, user_id)

        assert signature is not None
        assert len(signature) > 0

    def test_signature_verification(self):
        """Test signature verification"""
        user_id = "test_user"
        message = b"Important message"

        # Generate keys
        private_key, public_key = self.sig_manager.generate_signing_keypair(user_id)

        # Sign message
        signature = self.sig_manager.sign_message(message, user_id)

        # Verify signature
        is_valid = self.sig_manager.verify_signature(message, signature, public_key)

        assert is_valid is True

    def test_tampered_message_detection(self):
        """Test that tampered messages are detected"""
        user_id = "test_user"
        original_message = b"Important message"
        tampered_message = b"Tampered message"

        # Generate keys and sign
        private_key, public_key = self.sig_manager.generate_signing_keypair(user_id)
        signature = self.sig_manager.sign_message(original_message, user_id)

        # Verify with tampered message should fail
        is_valid = self.sig_manager.verify_signature(tampered_message, signature, public_key)

        assert is_valid is False

    def test_wrong_public_key_detection(self):
        """Test that wrong public key is detected"""
        user1 = "user1"
        user2 = "user2"
        message = b"Message"

        # Generate keys for both users
        _, public_key1 = self.sig_manager.generate_signing_keypair(user1)
        _, public_key2 = self.sig_manager.generate_signing_keypair(user2)

        # User1 signs message
        signature = self.sig_manager.sign_message(message, user1)

        # Verify with user2's public key should fail
        is_valid = self.sig_manager.verify_signature(message, signature, public_key2)

        assert is_valid is False

    def test_timestamped_signature(self):
        """Test signature with timestamp"""
        user_id = "test_user"
        message = b"Time-sensitive message"

        # Generate keys
        self.sig_manager.generate_signing_keypair(user_id)

        # Sign with timestamp
        signed_data = self.sig_manager.sign_with_timestamp(message, user_id)

        # Check components
        assert 'signature' in signed_data
        assert 'timestamp' in signed_data
        assert 'message' in signed_data

    def test_timestamped_signature_verification(self):
        """Test verification of timestamped signature"""
        user_id = "test_user"
        message = b"Time-sensitive message"

        # Generate keys
        _, public_key = self.sig_manager.generate_signing_keypair(user_id)

        # Sign with timestamp
        signed_data = self.sig_manager.sign_with_timestamp(message, user_id)

        # Verify (should be valid within 5 minutes)
        is_valid = self.sig_manager.verify_timestamped_signature(
            signed_data, public_key, max_age_seconds=300
        )

        assert is_valid is True

    def test_expired_timestamp_rejection(self):
        """Test that expired timestamps are rejected"""
        user_id = "test_user"
        message = b"Old message"

        # Generate keys
        _, public_key = self.sig_manager.generate_signing_keypair(user_id)

        # Sign with timestamp
        signed_data = self.sig_manager.sign_with_timestamp(message, user_id)

        # Wait 2 seconds
        time.sleep(2)

        # Verify with 1 second max age (should fail)
        is_valid = self.sig_manager.verify_timestamped_signature(
            signed_data, public_key, max_age_seconds=1
        )

        assert is_valid is False

    def test_non_repudiation(self):
        """Test non-repudiation property"""
        user_id = "alice"
        message = b"I owe Bob $100"

        # Alice generates keys and signs
        _, public_key = self.sig_manager.generate_signing_keypair(user_id)
        signature = self.sig_manager.sign_message(message, user_id)

        # Anyone can verify Alice signed this message
        is_valid = self.sig_manager.verify_signature(message, signature, public_key)

        assert is_valid is True

        # Alice cannot deny signing (non-repudiation)
        # Only Alice's private key could have created this signature


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
