import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test"""
    old_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def mock_prod_env():
    """Set up production environment variables"""
    return {
        "ENVIRONMENT": "production",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-key-12345678901234567890",
        "SUPABASE_KEY": "test-anon-key",
        "JWT_SECRET": "a" * 32,
        "ALLOWED_ORIGINS": "http://localhost:5173,https://example.com",
        "FRONTEND_URL": "https://example.com",
    }


@pytest.fixture
def mock_dev_env():
    """Set up development environment variables"""
    return {
        "ENVIRONMENT": "development",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
        "SUPABASE_KEY": "test-key",
        "JWT_SECRET": "a" * 32,
        "ALLOWED_ORIGINS": "http://localhost:5173",
    }