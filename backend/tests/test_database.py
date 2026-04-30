import pytest
import os


class TestDatabaseConfig:
    """Test database configuration"""

    def test_database_requires_url(self):
        """Test database config fails without URL"""
        import config
        config._config = None
        
        os.environ["SUPABASE_URL"] = ""
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test"
        
        cfg = config.DatabaseConfig.from_env()
        errors = cfg.validate()
        assert "SUPABASE_URL is required" in errors

    def test_database_requires_service_key(self):
        """Test database config fails without service key"""
        import config
        config._config = None
        
        os.environ["SUPABASE_URL"] = "https://test.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
        
        cfg = config.DatabaseConfig.from_env()
        errors = cfg.validate()
        assert "SUPABASE_SERVICE_ROLE_KEY is required" in errors

    def test_database_accepts_valid_config(self):
        """Test database config accepts valid values"""
        import config
        config._config = None
        
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "valid-key"
        
        cfg = config.DatabaseConfig.from_env()
        errors = cfg.validate()
        assert len(errors) == 0


class TestPlaceholderDetection:
    """Test that placeholder values are detected"""

    def test_detects_placeholder_url(self):
        from database import _is_placeholder
        assert _is_placeholder("your-project.supabase.co") is True
        assert _is_placeholder("replace-me.supabase.co") is True
        assert _is_placeholder("example.com") is True

    def test_accepts_real_url(self):
        from database import _is_placeholder
        assert _is_placeholder("kvsatdmryrtuzzmxripw.supabase.co") is False
        assert _is_placeholder("my-project.supabase.co") is False