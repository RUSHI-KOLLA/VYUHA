import pytest
from unittest.mock import MagicMock, Mock
from rate_limiter import RateLimiter, login_rate_limiter


class TestRateLimiter:
    """Test rate limiter functionality"""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed"""
        limiter = RateLimiter(requests_per_minute=10, burst_limit=15)
        
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock(host="127.0.0.1")
        mock_request.url = Mock(path="/api/test")
        
        for _ in range(10):
            allowed, _ = limiter.check_rate_limit(mock_request)
            assert allowed is True

    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over the limit are blocked"""
        limiter = RateLimiter(requests_per_minute=5, burst_limit=5)
        
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock(host="127.0.0.1")
        mock_request.url = Mock(path="/api/test")
        
        for _ in range(5):
            limiter.check_rate_limit(mock_request)
        
        allowed, headers = limiter.check_rate_limit(mock_request)
        assert allowed is False
        assert headers["X-RateLimit-Remaining"] == "0"

    def test_rate_limiter_separate_clients(self):
        """Test that different clients have separate limits"""
        limiter = RateLimiter(requests_per_minute=5, burst_limit=5)
        
        mock_request1 = Mock()
        mock_request1.headers = {}
        mock_request1.client = Mock(host="127.0.0.1")
        mock_request1.url = Mock(path="/api/test")
        
        mock_request2 = Mock()
        mock_request2.headers = {}
        mock_request2.client = Mock(host="192.168.1.1")
        mock_request2.url = Mock(path="/api/test")
        
        for _ in range(5):
            limiter.check_rate_limit(mock_request1)
        
        allowed1, _ = limiter.check_rate_limit(mock_request1)
        allowed2, _ = limiter.check_rate_limit(mock_request2)
        
        assert allowed1 is False
        assert allowed2 is True

    def test_login_rate_limiter_is_stricter(self):
        """Test that login rate limiter has stricter limits"""
        assert login_rate_limiter.requests_per_minute < 100
        assert login_rate_limiter.burst_limit < 150

    def test_rate_limiter_token_refill(self):
        """Test that tokens are refilled over time"""
        import time
        limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
        
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock(host="127.0.0.1")
        mock_request.url = Mock(path="/api/test")
        
        for _ in range(10):
            limiter.check_rate_limit(mock_request)
        
        allowed, _ = limiter.check_rate_limit(mock_request)
        assert allowed is False
        
        limiter.buckets["127.0.0.1"]["last_update"] = time.time() - 70
        
        allowed, _ = limiter.check_rate_limit(mock_request)
        assert allowed is True