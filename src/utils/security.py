"""
Security utilities: rate limiting, input validation, sanitization
"""

import re
import time
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta


class RateLimiter:
    """
    Rate limiter to prevent abuse
    Implements sliding window algorithm
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if request is allowed

        Args:
            user_id: User identifier

        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        user_requests = self.requests[user_id]

        # Remove old requests outside window
        while user_requests and user_requests[0] < now - self.window_seconds:
            user_requests.popleft()

        # Check limit
        if len(user_requests) >= self.max_requests:
            return False

        # Add new request
        user_requests.append(now)
        return True

    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining requests for user

        Args:
            user_id: User identifier

        Returns:
            Number of remaining requests
        """
        now = time.time()
        user_requests = self.requests[user_id]

        # Remove old requests
        while user_requests and user_requests[0] < now - self.window_seconds:
            user_requests.popleft()

        return max(0, self.max_requests - len(user_requests))


class SecurityManager:
    """
    Comprehensive security manager
    Features:
    - Rate limiting (per minute and per hour)
    - Input sanitization
    - Security logging
    - Anomaly detection
    """

    def __init__(self, max_per_minute: int = 30, max_per_hour: int = 500):
        """
        Initialize security manager

        Args:
            max_per_minute: Max requests per minute
            max_per_hour: Max requests per hour
        """
        self.rate_limiter_minute = RateLimiter(max_per_minute, 60)
        self.rate_limiter_hour = RateLimiter(max_per_hour, 3600)
        self.suspicious_activity: Dict[str, list] = defaultdict(list)
        self.blocked_users: Dict[str, datetime] = {}

    def check_rate_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user is rate limited

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check if user is blocked
        if user_id in self.blocked_users:
            block_time = self.blocked_users[user_id]
            if datetime.now() < block_time:
                remaining = (block_time - datetime.now()).seconds
                return False, f"Blocked for {remaining} seconds due to suspicious activity"
            else:
                del self.blocked_users[user_id]

        # Check per-minute limit
        if not self.rate_limiter_minute.is_allowed(user_id):
            remaining = self.rate_limiter_minute.get_remaining(user_id)
            return False, "Rate limit exceeded: too many requests per minute"

        # Check per-hour limit
        if not self.rate_limiter_hour.is_allowed(user_id):
            return False, "Rate limit exceeded: too many requests per hour"

        return True, None

    def sanitize_input(self, text: str, max_length: int = 4096) -> str:
        """
        Sanitize user input

        Args:
            text: Input text
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Trim to max length
        text = text[:max_length]

        # Remove null bytes and control characters (except newlines and tabs)
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

        return text.strip()

    def detect_anomaly(self, user_id: str, action: str) -> bool:
        """
        Detect suspicious activity patterns

        Args:
            user_id: User identifier
            action: Action type

        Returns:
            True if anomaly detected, False otherwise
        """
        # Log action
        self.suspicious_activity[user_id].append({
            'action': action,
            'timestamp': time.time()
        })

        # Keep only recent activity (last hour)
        cutoff = time.time() - 3600
        self.suspicious_activity[user_id] = [
            a for a in self.suspicious_activity[user_id]
            if a['timestamp'] > cutoff
        ]

        # Check for anomalies
        recent_actions = self.suspicious_activity[user_id]

        # Too many failed decryption attempts
        failed_decrypts = sum(1 for a in recent_actions if a['action'] == 'failed_decrypt')
        if failed_decrypts > 10:
            self.block_user(user_id, minutes=30)
            return True

        # Rapid key generation requests
        key_gens = sum(1 for a in recent_actions if a['action'] == 'generate_keys')
        if key_gens > 20:
            self.block_user(user_id, minutes=15)
            return True

        return False

    def block_user(self, user_id: str, minutes: int) -> None:
        """
        Temporarily block user

        Args:
            user_id: User identifier
            minutes: Block duration in minutes
        """
        self.blocked_users[user_id] = datetime.now() + timedelta(minutes=minutes)

    def validate_base64(self, data: str) -> bool:
        """
        Validate base64 encoded data

        Args:
            data: Base64 string

        Returns:
            True if valid, False otherwise
        """
        try:
            import base64
            base64.b64decode(data, validate=True)
            return True
        except Exception:
            return False

    def is_safe_filename(self, filename: str) -> bool:
        """
        Check if filename is safe (no path traversal)

        Args:
            filename: Filename to check

        Returns:
            True if safe, False otherwise
        """
        # Check for path traversal patterns
        dangerous_patterns = [
            '..',
            '/',
            '\\',
            '\x00',
            '<',
            '>',
            ':',
            '"',
            '|',
            '?',
            '*'
        ]

        for pattern in dangerous_patterns:
            if pattern in filename:
                return False

        return True
