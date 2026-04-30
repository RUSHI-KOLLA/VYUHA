import pytest
import os


def reset_config():
    """Reset config global and reload"""
    import config
    config._config = None
    return config


class TestConfigValidation:
    """Test configuration validation"""

    def test_database_config_requires_url(self):
        """Test that SUPABASE_URL is required"""
        reset_config()
        os.environ["SUPABASE_URL"] = ""
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
        os.environ["JWT_SECRET"] = "a" * 32
        os.environ["ALLOWED_ORIGINS"] = "http://localhost"
        os.environ["SMTP_FROM_EMAIL"] = "test@test.com"
        
        cfg = config.AppConfig.from_env()
        errors = cfg.database.validate()
        assert any("SUPABASE_URL" in e for e in errors)

    def test_database_config_requires_service_key(self):
        """Test that SUPABASE_SERVICE_ROLE_KEY is required"""
        reset_config()
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
        os.environ["JWT_SECRET"] = "a" * 32
        os.environ["ALLOWED_ORIGINS"] = "http://localhost"
        
        cfg = config.AppConfig.from_env()
        errors = cfg.database.validate()
        assert any("SUPABASE_SERVICE_ROLE_KEY" in e for e in errors)

    def test_jwt_config_requires_secret(self):
        """Test that JWT_SECRET is required"""
        reset_config()
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
        os.environ["JWT_SECRET"] = ""
        os.environ["ALLOWED_ORIGINS"] = "http://localhost"
        
        cfg = config.AppConfig.from_env()
        errors = cfg.jwt.validate()
        assert any("JWT_SECRET" in e for e in errors)

    def test_jwt_config_requires_min_length(self):
        """Test that JWT_SECRET must be at least 32 characters"""
        reset_config()
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
        os.environ["JWT_SECRET"] = "short"
        os.environ["ALLOWED_ORIGINS"] = "http://localhost"
        
        cfg = config.AppConfig.from_env()
        errors = cfg.jwt.validate()
        assert any("32 characters" in e for e in errors)

    def test_security_config_requires_origins(self):
        """Test that ALLOWED_ORIGINS is required"""
        reset_config()
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
        os.environ["JWT_SECRET"] = "a" * 32
        os.environ["ALLOWED_ORIGINS"] = ""
        
        cfg = config.AppConfig.from_env()
        errors = cfg.security.validate()
        assert any("ALLOWED_ORIGINS" in e for e in errors)

    def test_email_config_validates_from_email(self):
        """Test that SMTP_FROM_EMAIL must be valid"""
        reset_config()
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
        os.environ["JWT_SECRET"] = "a" * 32
        os.environ["ALLOWED_ORIGINS"] = "http://localhost"
        os.environ["SMTP_FROM_EMAIL"] = "invalid"
        
        cfg = config.AppConfig.from_env()
        errors = cfg.email.validate()
        assert any("valid email" in e.lower() for e in errors)