#!/usr/bin/env python3
"""
Configuration Management for Samay Sync MVP
Simplified configuration system for essential settings only

This file provides:
1. Basic configuration with sensible defaults
2. Environment variable overrides
3. Essential settings for database, sync, and OAuth
4. Simple validation for critical values
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    # ActivityWatch database path (macOS default)
    db_path: str = "~/Library/Application Support/activitywatch/aw-server/peewee-sqlite.v2.db"
    
    # Connection settings
    timeout: int = 30
    batch_size: int = 1000
    
    def __post_init__(self):
        """Expand user path and validate settings"""
        self.db_path = os.path.expanduser(self.db_path)
        if self.timeout <= 0:
            raise ValueError("Database timeout must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")


@dataclass
class SyncConfig:
    """Synchronization configuration"""
    # Sync interval in seconds (5 minutes default)
    sync_interval: int = 300
    
    # Retry settings
    max_retries: int = 3
    retry_delay: int = 60
    
    # State management
    state_file_path: str = "~/.samay_sync/sync_state.json"
    
    # Logging
    log_dir: str = "~/.samay_sync/logs"
    
    def __post_init__(self):
        """Validate sync configuration"""
        self.state_file_path = os.path.expanduser(self.state_file_path)
        self.log_dir = os.path.expanduser(self.log_dir)
        
        if self.sync_interval <= 0:
            raise ValueError("Sync interval must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.retry_delay <= 0:
            raise ValueError("Retry delay must be positive")


@dataclass
class OAuthConfig:
    """OAuth configuration"""
    # OAuth settings (placeholders for backend team)
    client_id: str = "placeholder_client_id"
    client_secret: str = "placeholder_client_secret"
    redirect_uri: str = "http://127.0.0.1:54783/callback"
    auth_url: str = "https://auth.example.com/oauth/authorize"
    token_url: str = "https://auth.example.com/oauth/token"
    
    # Token storage
    token_storage_path: str = "~/.samay_sync/tokens.json"
    
    def __post_init__(self):
        """Validate OAuth configuration"""
        self.token_storage_path = os.path.expanduser(self.token_storage_path)
        # Note: Validation of client_id and client_secret happens after environment overrides


@dataclass
class ServerConfig:
    """Backend server configuration"""
    # Server endpoints (placeholders for backend team)
    base_url: str = "https://api.example.com"
    sync_endpoint: str = "/v1/sync/events"
    health_endpoint: str = "/v1/health"
    
    # HTTP settings
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate server configuration"""
        if self.timeout <= 0:
            raise ValueError("HTTP timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


class Config:
    """Main configuration class for Samay Sync MVP"""
    
    def __init__(self):
        """Initialize configuration with defaults and environment overrides"""
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.sync = SyncConfig()
        self.oauth = OAuthConfig()
        self.server = ServerConfig()
        
        # Apply environment variable overrides
        self._apply_environment_overrides()
        
        # Validate final configuration
        self._validate_config()
    
    def _apply_environment_overrides(self):
        """Apply configuration from environment variables"""
        # Database configuration
        if os.getenv("SAMAY_DB_PATH"):
            self.database.db_path = os.getenv("SAMAY_DB_PATH")
        if os.getenv("SAMAY_DB_TIMEOUT"):
            self.database.timeout = int(os.getenv("SAMAY_DB_TIMEOUT"))
        if os.getenv("SAMAY_DB_BATCH_SIZE"):
            self.database.batch_size = int(os.getenv("SAMAY_DB_BATCH_SIZE"))
        
        # Sync configuration
        if os.getenv("SAMAY_SYNC_INTERVAL"):
            self.sync.sync_interval = int(os.getenv("SAMAY_SYNC_INTERVAL"))
        if os.getenv("SAMAY_SYNC_RETRIES"):
            self.sync.max_retries = int(os.getenv("SAMAY_SYNC_RETRIES"))
        if os.getenv("SAMAY_SYNC_STATE_PATH"):
            self.sync.state_file_path = os.getenv("SAMAY_SYNC_STATE_PATH")
        
        # OAuth configuration
        if os.getenv("SAMAY_OAUTH_CLIENT_ID"):
            self.oauth.client_id = os.getenv("SAMAY_OAUTH_CLIENT_ID")
        if os.getenv("SAMAY_OAUTH_CLIENT_SECRET"):
            self.oauth.client_secret = os.getenv("SAMAY_OAUTH_CLIENT_SECRET")
        if os.getenv("SAMAY_OAUTH_REDIRECT_URI"):
            self.oauth.redirect_uri = os.getenv("SAMAY_OAUTH_REDIRECT_URI")
        if os.getenv("SAMAY_OAUTH_AUTH_URL"):
            self.oauth.auth_url = os.getenv("SAMAY_OAUTH_AUTH_URL")
        if os.getenv("SAMAY_OAUTH_TOKEN_URL"):
            self.oauth.token_url = os.getenv("SAMAY_OAUTH_TOKEN_URL")
        
        # Server configuration
        if os.getenv("SAMAY_SERVER_URL"):
            self.server.base_url = os.getenv("SAMAY_SERVER_URL")
        if os.getenv("SAMAY_SERVER_TIMEOUT"):
            self.server.timeout = int(os.getenv("SAMAY_SERVER_TIMEOUT"))
        if os.getenv("SAMAY_SERVER_RETRIES"):
            self.server.max_retries = int(os.getenv("SAMAY_SERVER_RETRIES"))
    
    def _validate_config(self):
        """Validate final configuration"""
        try:
            # Re-validate all sections after environment overrides
            self.database.__post_init__()
            self.sync.__post_init__()
            self.oauth.__post_init__()
            self.server.__post_init__()
            
            # Additional validation for OAuth after environment overrides
            if not self.oauth.client_id or self.oauth.client_id == "placeholder_client_id":
                raise ValueError("OAuth client_id must be configured")
            if not self.oauth.client_secret or self.oauth.client_secret == "placeholder_client_secret":
                raise ValueError("OAuth client_secret must be configured")
                
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def get_summary(self) -> dict:
        """Get a summary of current configuration"""
        return {
            "database": {
                "db_path": self.database.db_path,
                "timeout": self.database.timeout,
                "batch_size": self.database.batch_size
            },
            "sync": {
                "sync_interval": self.sync.sync_interval,
                "max_retries": self.sync.max_retries,
                "retry_delay": self.sync.retry_delay,
                "state_file_path": self.sync.state_file_path
            },
            "oauth": {
                "client_id": self.oauth.client_id,
                "redirect_uri": self.oauth.redirect_uri,
                "auth_url": self.oauth.auth_url,
                "token_url": self.oauth.token_url,
                "token_storage_path": self.oauth.token_storage_path
            },
            "server": {
                "base_url": self.server.base_url,
                "sync_endpoint": self.server.sync_endpoint,
                "health_endpoint": self.server.health_endpoint,
                "timeout": self.server.timeout,
                "max_retries": self.server.max_retries
            }
        }


# Convenience function for quick configuration access
def get_config() -> Config:
    """Get a configuration instance"""
    return Config()


# Example usage and testing
if __name__ == "__main__":
    try:
        config = get_config()
        print("✅ Configuration loaded successfully!")
        print("\n📊 Configuration Summary:")
        
        summary = config.get_summary()
        for section, settings in summary.items():
            print(f"\n{section.upper()}:")
            for key, value in settings.items():
                print(f"  {key}: {value}")
        
        print("\n🔧 Environment Variables Available:")
        env_vars = [
            "SAMAY_DB_PATH", "SAMAY_DB_TIMEOUT", "SAMAY_DB_BATCH_SIZE",
            "SAMAY_SYNC_INTERVAL", "SAMAY_SYNC_RETRIES", "SAMAY_SYNC_STATE_PATH",
            "SAMAY_OAUTH_CLIENT_ID", "SAMAY_OAUTH_CLIENT_SECRET", "SAMAY_OAUTH_REDIRECT_URI",
            "SAMAY_OAUTH_AUTH_URL", "SAMAY_OAUTH_TOKEN_URL",
            "SAMAY_SERVER_URL", "SAMAY_SERVER_TIMEOUT", "SAMAY_SERVER_RETRIES"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                print(f"  {var}: {value}")
            else:
                print(f"  {var}: (not set)")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Make sure to set required environment variables:")
        print("   SAMAY_OAUTH_CLIENT_ID=your_client_id")
        print("   SAMAY_OAUTH_CLIENT_SECRET=your_client_secret")
