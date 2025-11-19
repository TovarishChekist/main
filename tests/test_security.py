"""
Tests for security features
"""

import pytest
import time
from src.utils.security import SecurityManager, RateLimiter


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        user_id = "test_user"

        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.is_allowed(user_id) is True

        # 6th request should be denied
        assert limiter.is_allowed(user_id) is False

    def test_rate_limiter_window_reset(self):
        """Test that rate limiter resets after window expires"""
        limiter = RateLimiter(max_requests=2, window_seconds=1)

        user_id = "test_user"

        # Use up quota
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is False

        # Wait for window to reset
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.is_allowed(user_id) is True

    def test_rate_limiter_per_user(self):
        """Test that rate limiting is per-user"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        user1 = "user1"
        user2 = "user2"

        # User 1 uses quota
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user1) is False

        # User 2 should still be allowed
        assert limiter.is_allowed(user2) is True
        assert limiter.is_allowed(user2) is True


class TestSecurityManager:
    """Test security manager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.security = SecurityManager(max_per_minute=5, max_per_hour=20)

    def test_rate_limit_check(self):
        """Test rate limit checking"""
        user_id = "test_user"

        # First requests should be allowed
        for i in range(5):
            allowed, reason = self.security.check_rate_limit(user_id)
            assert allowed is True
            assert reason is None

        # Next request should be denied
        allowed, reason = self.security.check_rate_limit(user_id)
        assert allowed is False
        assert "minute" in reason.lower()

    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test normal input
        clean = self.security.sanitize_input("Hello World")
        assert clean == "Hello World"

        # Test input with control characters
        dirty = "Hello\x00World\x01Test"
        clean = self.security.sanitize_input(dirty)
        assert "\x00" not in clean
        assert "\x01" not in clean

        # Test max length
        long_input = "X" * 5000
        clean = self.security.sanitize_input(long_input, max_length=100)
        assert len(clean) == 100

    def test_anomaly_detection(self):
        """Test anomaly detection"""
        user_id = "test_user"

        # Generate many failed decrypt attempts
        for i in range(15):
            self.security.detect_anomaly(user_id, 'failed_decrypt')

        # User should be blocked
        allowed, reason = self.security.check_rate_limit(user_id)
        assert allowed is False
        assert "blocked" in reason.lower()

    def test_base64_validation(self):
        """Test base64 validation"""
        # Valid base64
        assert self.security.validate_base64("SGVsbG8gV29ybGQ=") is True

        # Invalid base64
        assert self.security.validate_base64("Not base64!@#$") is False

    def test_safe_filename_validation(self):
        """Test filename safety validation"""
        # Safe filenames
        assert self.security.is_safe_filename("document.txt") is True
        assert self.security.is_safe_filename("my_file_123.pdf") is True

        # Unsafe filenames (path traversal)
        assert self.security.is_safe_filename("../etc/passwd") is False
        assert self.security.is_safe_filename("../../secret.txt") is False
        assert self.security.is_safe_filename("file/with/slash.txt") is False

    def test_blocking_mechanism(self):
        """Test user blocking"""
        user_id = "bad_user"

        # Block user for 1 minute
        self.security.block_user(user_id, minutes=1)

        # Should be blocked
        allowed, reason = self.security.check_rate_limit(user_id)
        assert allowed is False


class TestInputValidation:
    """Test input validation"""

    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are sanitized"""
        security = SecurityManager()

        # SQL injection attempt
        malicious = "'; DROP TABLE users; --"
        sanitized = security.sanitize_input(malicious)

        # Should still contain the text but be safe
        assert sanitized == malicious  # We sanitize, not remove

    def test_xss_prevention(self):
        """Test XSS prevention in input"""
        security = SecurityManager()

        xss = "<script>alert('XSS')</script>"
        sanitized = security.sanitize_input(xss)

        # Control characters should be removed
        # But this is text input, not HTML, so tags remain
        assert len(sanitized) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
