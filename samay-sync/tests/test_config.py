#!/usr/bin/env python3
"""
Test suite for Configuration Module
Tests all configuration functionality including environment variables and validation
"""

import os
import tempfile
import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add the config module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.sync_config import Config, DatabaseConfig, SyncConfig, OAuthConfig, ServerConfig


class TestDatabaseConfig(unittest.TestCase):
    """Test DatabaseConfig functionality"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = DatabaseConfig()
        
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.batch_size, 1000)
        self.assertTrue(config.db_path.endswith("peewee-sqlite.v2.db"))
    
    def test_path_expansion(self):
        """Test user path expansion"""
        config = DatabaseConfig()
        self.assertFalse(config.db_path.startswith("~"))
        self.assertTrue(config.db_path.startswith("/"))
    
    def test_validation(self):
        """Test configuration validation"""
        # Test positive timeout
        config = DatabaseConfig(timeout=60)
        self.assertEqual(config.timeout, 60)
        
        # Test invalid timeout
        with self.assertRaises(ValueError):
            DatabaseConfig(timeout=0)
        
        # Test invalid batch size
        with self.assertRaises(ValueError):
            DatabaseConfig(batch_size=-1)


class TestSyncConfig(unittest.TestCase):
    """Test SyncConfig functionality"""
    
    def test_default_values(self):
        """Test default sync configuration"""
        config = SyncConfig()
        
        self.assertEqual(config.sync_interval, 300)  # 5 minutes
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay, 60)
        self.assertTrue(config.state_file_path.endswith("sync_state.json"))
    
    def test_validation(self):
        """Test sync configuration validation"""
        # Test valid values
        config = SyncConfig(sync_interval=600, max_retries=5)
        self.assertEqual(config.sync_interval, 600)
        self.assertEqual(config.max_retries, 5)
        
        # Test invalid sync interval
        with self.assertRaises(ValueError):
            SyncConfig(sync_interval=0)
        
        # Test invalid max retries
        with self.assertRaises(ValueError):
            SyncConfig(max_retries=-1)


class TestOAuthConfig(unittest.TestCase):
    """Test OAuthConfig functionality"""
    
    def test_default_values(self):
        """Test default OAuth configuration"""
        config = OAuthConfig()
        
        self.assertEqual(config.client_id, "placeholder_client_id")
        self.assertEqual(config.client_secret, "placeholder_client_secret")
        self.assertEqual(config.redirect_uri, "http://127.0.0.1:54783/callback")
        self.assertTrue(config.auth_url.endswith("/oauth/authorize"))
        self.assertTrue(config.token_url.endswith("/oauth/token"))
    
    def test_path_expansion(self):
        """Test token storage path expansion"""
        config = OAuthConfig()
        self.assertFalse(config.token_storage_path.startswith("~"))
        self.assertTrue(config.token_storage_path.startswith("/"))


class TestServerConfig(unittest.TestCase):
    """Test ServerConfig functionality"""
    
    def test_default_values(self):
        """Test default server configuration"""
        config = ServerConfig()
        
        self.assertEqual(config.base_url, "https://api.example.com")
        self.assertEqual(config.sync_endpoint, "/v1/sync/events")
        self.assertEqual(config.health_endpoint, "/v1/health")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
    
    def test_validation(self):
        """Test server configuration validation"""
        # Test valid values
        config = ServerConfig(timeout=60, max_retries=5)
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 5)
        
        # Test invalid timeout
        with self.assertRaises(ValueError):
            ServerConfig(timeout=0)
        
        # Test invalid max retries
        with self.assertRaises(ValueError):
            ServerConfig(max_retries=-1)


class TestConfig(unittest.TestCase):
    """Test main Config class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear environment variables
        env_vars = [
            "SAMAY_DB_PATH", "SAMAY_DB_TIMEOUT", "SAMAY_DB_BATCH_SIZE",
            "SAMAY_SYNC_INTERVAL", "SAMAY_SYNC_RETRIES", "SAMAY_SYNC_STATE_PATH",
            "SAMAY_OAUTH_CLIENT_ID", "SAMAY_OAUTH_CLIENT_SECRET", "SAMAY_OAUTH_REDIRECT_URI",
            "SAMAY_OAUTH_AUTH_URL", "SAMAY_OAUTH_TOKEN_URL",
            "SAMAY_SERVER_URL", "SAMAY_SERVER_TIMEOUT", "SAMAY_SERVER_RETRIES"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_default_configuration(self):
        """Test default configuration loading"""
        # Set OAuth credentials for default test
        os.environ["SAMAY_OAUTH_CLIENT_ID"] = "test_client"
        os.environ["SAMAY_OAUTH_CLIENT_SECRET"] = "test_secret"
        
        config = Config()
        
        # Test that all sections are initialized
        self.assertIsInstance(config.database, DatabaseConfig)
        self.assertIsInstance(config.sync, SyncConfig)
        self.assertIsInstance(config.oauth, OAuthConfig)
        self.assertIsInstance(config.server, ServerConfig)
        
        # Test default values
        self.assertEqual(config.database.timeout, 30)
        self.assertEqual(config.sync.sync_interval, 300)
        self.assertEqual(config.server.timeout, 30)
    
    def test_environment_variable_overrides(self):
        """Test environment variable overrides"""
        # Set environment variables
        os.environ["SAMAY_DB_TIMEOUT"] = "60"
        os.environ["SAMAY_SYNC_INTERVAL"] = "600"
        os.environ["SAMAY_SERVER_TIMEOUT"] = "45"
        os.environ["SAMAY_OAUTH_CLIENT_ID"] = "test_client"
        os.environ["SAMAY_OAUTH_CLIENT_SECRET"] = "test_secret"
        
        config = Config()
        
        # Test overrides
        self.assertEqual(config.database.timeout, 60)
        self.assertEqual(config.sync.sync_interval, 600)
        self.assertEqual(config.server.timeout, 45)
        self.assertEqual(config.oauth.client_id, "test_client")
        self.assertEqual(config.oauth.client_secret, "test_secret")
    
    def test_configuration_summary(self):
        """Test configuration summary generation"""
        os.environ["SAMAY_OAUTH_CLIENT_ID"] = "test_client"
        os.environ["SAMAY_OAUTH_CLIENT_SECRET"] = "test_secret"
        
        config = Config()
        summary = config.get_summary()
        
        # Test summary structure
        self.assertIn("database", summary)
        self.assertIn("sync", summary)
        self.assertIn("oauth", summary)
        self.assertIn("server", summary)
        
        # Test database section
        self.assertIn("db_path", summary["database"])
        self.assertIn("timeout", summary["database"])
        self.assertIn("batch_size", summary["database"])
        
        # Test sync section
        self.assertIn("sync_interval", summary["sync"])
        self.assertIn("max_retries", summary["sync"])
        self.assertIn("retry_delay", summary["sync"])
        self.assertIn("state_file_path", summary["sync"])
        
        # Test oauth section
        self.assertIn("client_id", summary["oauth"])
        self.assertIn("redirect_uri", summary["oauth"])
        self.assertIn("auth_url", summary["oauth"])
        self.assertIn("token_url", summary["oauth"])
        self.assertIn("token_storage_path", summary["oauth"])
        
        # Test server section
        self.assertIn("base_url", summary["server"])
        self.assertIn("sync_endpoint", summary["server"])
        self.assertIn("health_endpoint", summary["server"])
        self.assertIn("timeout", summary["server"])
        self.assertIn("max_retries", summary["server"])
    
    def test_oauth_validation_without_credentials(self):
        """Test OAuth validation fails without credentials"""
        # Don't set OAuth credentials
        with self.assertRaises(ValueError) as context:
            Config()
        
        self.assertIn("OAuth client_id must be configured", str(context.exception))
    
    def test_oauth_validation_with_credentials(self):
        """Test OAuth validation passes with credentials"""
        os.environ["SAMAY_OAUTH_CLIENT_ID"] = "test_client"
        os.environ["SAMAY_OAUTH_CLIENT_SECRET"] = "test_secret"
        
        # Should not raise exception
        config = Config()
        self.assertEqual(config.oauth.client_id, "test_client")
        self.assertEqual(config.oauth.client_secret, "test_secret")


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for configuration system"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear environment variables
        env_vars = [
            "SAMAY_DB_PATH", "SAMAY_DB_TIMEOUT", "SAMAY_DB_BATCH_SIZE",
            "SAMAY_SYNC_INTERVAL", "SAMAY_SYNC_RETRIES", "SAMAY_SYNC_STATE_PATH",
            "SAMAY_OAUTH_CLIENT_ID", "SAMAY_OAUTH_CLIENT_SECRET", "SAMAY_OAUTH_REDIRECT_URI",
            "SAMAY_OAUTH_AUTH_URL", "SAMAY_OAUTH_TOKEN_URL",
            "SAMAY_SERVER_URL", "SAMAY_SERVER_TIMEOUT", "SAMAY_SERVER_RETRIES"
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_full_configuration_workflow(self):
        """Test complete configuration workflow"""
        # Set comprehensive environment variables
        os.environ.update({
            "SAMAY_DB_PATH": "/custom/db/path.db",
            "SAMAY_DB_TIMEOUT": "45",
            "SAMAY_DB_BATCH_SIZE": "500",
            "SAMAY_SYNC_INTERVAL": "600",
            "SAMAY_SYNC_RETRIES": "5",
            "SAMAY_SYNC_STATE_PATH": "/custom/state/path.json",
            "SAMAY_OAUTH_CLIENT_ID": "integration_test_client",
            "SAMAY_OAUTH_CLIENT_SECRET": "integration_test_secret",
            "SAMAY_OAUTH_REDIRECT_URI": "http://localhost:8080/callback",
            "SAMAY_OAUTH_AUTH_URL": "https://auth.test.com/oauth/authorize",
            "SAMAY_OAUTH_TOKEN_URL": "https://auth.test.com/oauth/token",
            "SAMAY_SERVER_URL": "https://api.test.com",
            "SAMAY_SERVER_TIMEOUT": "60",
            "SAMAY_SERVER_RETRIES": "5"
        })
        
        # Load configuration
        config = Config()
        
        # Verify all overrides
        self.assertEqual(config.database.db_path, "/custom/db/path.db")
        self.assertEqual(config.database.timeout, 45)
        self.assertEqual(config.database.batch_size, 500)
        
        self.assertEqual(config.sync.sync_interval, 600)
        self.assertEqual(config.sync.max_retries, 5)
        self.assertEqual(config.sync.state_file_path, "/custom/state/path.json")
        
        self.assertEqual(config.oauth.client_id, "integration_test_client")
        self.assertEqual(config.oauth.client_secret, "integration_test_secret")
        self.assertEqual(config.oauth.redirect_uri, "http://localhost:8080/callback")
        self.assertEqual(config.oauth.auth_url, "https://auth.test.com/oauth/authorize")
        self.assertEqual(config.oauth.token_url, "https://auth.test.com/oauth/token")
        
        self.assertEqual(config.server.base_url, "https://api.test.com")
        self.assertEqual(config.server.timeout, 60)
        self.assertEqual(config.server.max_retries, 5)
        
        # Test summary generation
        summary = config.get_summary()
        self.assertEqual(summary["database"]["db_path"], "/custom/db/path.db")
        self.assertEqual(summary["oauth"]["client_id"], "integration_test_client")
        self.assertEqual(summary["server"]["base_url"], "https://api.test.com")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
