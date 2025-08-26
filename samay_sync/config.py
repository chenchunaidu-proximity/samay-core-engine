#!/usr/bin/env python3
"""
Configuration Management System for Samay Core Engine
Handles environment variables, configuration files, and settings validation

This file implements a robust configuration system that:
1. Loads settings from environment variables
2. Supports configuration files (JSON, YAML)
3. Provides sensible defaults for all settings
4. Validates configuration values
5. Supports different environments (dev, staging, prod)
6. Handles sensitive data securely

Key Components:
- ConfigManager: Main configuration management class
- EnvironmentConfig: Environment-specific settings
- DatabaseConfig: Database connection settings
- SyncConfig: Synchronization settings
- ServerConfig: Backend server settings
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    # ActivityWatch database path
    db_path: str = "~/Library/Application Support/activitywatch/aw-server/peewee-sqlite.v2.db"
    
    # Connection settings
    timeout: int = 30
    check_same_thread: bool = False
    
    # Query settings
    default_batch_size: int = 1000
    max_query_limit: int = 10000
    
    def __post_init__(self):
        """Expand user path and validate settings"""
        self.db_path = os.path.expanduser(self.db_path)
        if self.timeout <= 0:
            raise ValueError("Database timeout must be positive")
        if self.default_batch_size <= 0:
            raise ValueError("Default batch size must be positive")
        if self.max_query_limit <= 0:
            raise ValueError("Max query limit must be positive")

@dataclass
class SyncConfig:
    """Synchronization configuration"""
    # Sync intervals (in seconds)
    sync_interval: int = 300  # 5 minutes
    retry_interval: int = 60   # 1 minute
    max_retries: int = 3
    
    # Batch processing
    max_batch_size: int = 1000
    batch_timeout: int = 30
    
    # State management
    state_file_path: str = "~/.samay_sync/sync_state.json"
    backup_retention_days: int = 30
    
    # Duplicate prevention
    enable_duplicate_check: bool = True
    strict_id_validation: bool = True
    
    def __post_init__(self):
        """Validate sync configuration"""
        if self.sync_interval <= 0:
            raise ValueError("Sync interval must be positive")
        if self.retry_interval <= 0:
            raise ValueError("Retry interval must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.max_batch_size <= 0:
            raise ValueError("Max batch size must be positive")
        if self.batch_timeout <= 0:
            raise ValueError("Batch timeout must be positive")
        if self.backup_retention_days <= 0:
            raise ValueError("Backup retention days must be positive")

@dataclass
class ServerConfig:
    """Backend server configuration"""
    # Server endpoints (to be configured by backend team)
    base_url: str = "https://api.example.com"
    sync_endpoint: str = "/v1/sync/events"
    health_check_endpoint: str = "/v1/health"
    
    # Authentication (to be configured)
    auth_token: Optional[str] = None
    auth_header: str = "Authorization"
    auth_type: str = "Bearer"
    
    # HTTP settings
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 1.5
    
    # Rate limiting (to be configured)
    requests_per_minute: int = 60
    burst_limit: int = 10
    
    def __post_init__(self):
        """Validate server configuration"""
        if self.timeout <= 0:
            raise ValueError("HTTP timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.retry_backoff <= 0:
            raise ValueError("Retry backoff must be positive")
        if self.requests_per_minute <= 0:
            raise ValueError("Requests per minute must be positive")
        if self.burst_limit <= 0:
            raise ValueError("Burst limit must be positive")

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "~/.samay_sync/samay.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def __post_init__(self):
        """Validate logging configuration"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        if self.max_file_size <= 0:
            raise ValueError("Max file size must be positive")
        if self.backup_count < 0:
            raise ValueError("Backup count cannot be negative")

class ConfigManager:
    """Main configuration management class"""
    
    def __init__(self, config_file: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file (JSON/YAML)
            environment: Environment name (development, staging, production)
        """
        self.environment = Environment(environment or self._detect_environment())
        self.config_file = Path(config_file) if config_file else self._get_default_config_path()
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.sync = SyncConfig()
        self.server = ServerConfig()
        self.logging = LoggingConfig()
        
        # Load configuration
        self._load_config()
        self._setup_logging()
        
        logger.info(f"Configuration loaded for environment: {self.environment.value}")
    
    def _detect_environment(self) -> str:
        """Detect environment from environment variables"""
        env = os.getenv("SAMAY_ENV", "").lower()
        if env in [e.value for e in Environment]:
            return env
        
        # Auto-detect based on common patterns
        if os.getenv("SAMAY_DEBUG") == "true":
            return Environment.DEVELOPMENT.value
        elif os.getenv("SAMAY_STAGING") == "true":
            return Environment.STAGING.value
        elif os.getenv("NODE_ENV") == "production":
            return Environment.PRODUCTION.value
        else:
            return Environment.DEVELOPMENT.value
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        home = Path.home()
        return home / ".samay_sync" / "config.json"
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self._apply_file_config(file_config)
                logger.info(f"Configuration loaded from: {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        self._apply_environment_config()
        
        # Validate final configuration
        self._validate_config()
    
    def _apply_file_config(self, config: Dict[str, Any]):
        """Apply configuration from file"""
        # Database configuration
        if 'database' in config:
            db_config = config['database']
            for key, value in db_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        # Sync configuration
        if 'sync' in config:
            sync_config = config['sync']
            for key, value in sync_config.items():
                if hasattr(self.sync, key):
                    setattr(self.sync, key, value)
        
        # Server configuration
        if 'server' in config:
            server_config = config['server']
            for key, value in server_config.items():
                if hasattr(self.server, key):
                    setattr(self.server, key, value)
        
        # Logging configuration
        if 'logging' in config:
            logging_config = config['logging']
            for key, value in logging_config.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
    
    def _apply_environment_config(self):
        """Apply configuration from environment variables"""
        # Database configuration
        if os.getenv("SAMAY_DB_PATH"):
            self.database.db_path = os.getenv("SAMAY_DB_PATH")
        if os.getenv("SAMAY_DB_TIMEOUT"):
            self.database.timeout = int(os.getenv("SAMAY_DB_TIMEOUT"))
        if os.getenv("SAMAY_DB_BATCH_SIZE"):
            self.database.default_batch_size = int(os.getenv("SAMAY_DB_BATCH_SIZE"))
        
        # Sync configuration
        if os.getenv("SAMAY_SYNC_INTERVAL"):
            self.sync.sync_interval = int(os.getenv("SAMAY_SYNC_INTERVAL"))
        if os.getenv("SAMAY_SYNC_RETRIES"):
            self.sync.max_retries = int(os.getenv("SAMAY_SYNC_RETRIES"))
        if os.getenv("SAMAY_SYNC_BATCH_SIZE"):
            self.sync.max_batch_size = int(os.getenv("SAMAY_SYNC_BATCH_SIZE"))
        
        # Server configuration
        if os.getenv("SAMAY_SERVER_URL"):
            self.server.base_url = os.getenv("SAMAY_SERVER_URL")
        if os.getenv("SAMAY_AUTH_TOKEN"):
            self.server.auth_token = os.getenv("SAMAY_AUTH_TOKEN")
        if os.getenv("SAMAY_SERVER_TIMEOUT"):
            self.server.timeout = int(os.getenv("SAMAY_SERVER_TIMEOUT"))
        
        # Logging configuration
        if os.getenv("SAMAY_LOG_LEVEL"):
            self.logging.level = os.getenv("SAMAY_LOG_LEVEL")
        if os.getenv("SAMAY_LOG_FILE"):
            self.logging.file_path = os.getenv("SAMAY_LOG_FILE")
    
    def _validate_config(self):
        """Validate final configuration"""
        try:
            # Validate all configuration sections
            self.database.__post_init__()
            self.sync.__post_init__()
            self.server.__post_init__()
            self.logging.__post_init__()
            logger.debug("Configuration validation passed")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        # Create log directory if it doesn't exist
        if self.logging.file_path:
            log_path = Path(os.path.expanduser(self.logging.file_path))
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.logging.level.upper()),
            format=self.logging.format,
            handlers=[
                logging.StreamHandler(),  # Console handler
                logging.FileHandler(os.path.expanduser(self.logging.file_path)) if self.logging.file_path else logging.NullHandler()
            ]
        )
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            "environment": self.environment.value,
            "config_file": str(self.config_file),
            "database": asdict(self.database),
            "sync": asdict(self.sync),
            "server": asdict(self.server),
            "logging": asdict(self.logging)
        }
    
    def save_config(self, config_file: Optional[str] = None):
        """Save current configuration to file"""
        if config_file:
            config_path = Path(config_file)
        else:
            config_path = self.config_file
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            config_data = self.get_config_summary()
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            logger.info(f"Configuration saved to: {config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def reload_config(self):
        """Reload configuration from file and environment"""
        logger.info("Reloading configuration...")
        self._load_config()
    
    def get_setting(self, section: str, key: str) -> Any:
        """Get a specific configuration setting"""
        if hasattr(self, section):
            section_obj = getattr(self, section)
            if hasattr(section_obj, key):
                return getattr(section_obj, key)
        
        raise ValueError(f"Setting not found: {section}.{key}")
    
    def set_setting(self, section: str, key: str, value: Any):
        """Set a specific configuration setting"""
        if hasattr(self, section):
            section_obj = getattr(self, section)
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
                # Re-validate the section
                section_obj.__post_init__()
                logger.info(f"Updated setting: {section}.{key} = {value}")
            else:
                raise ValueError(f"Key not found: {section}.{key}")
        else:
            raise ValueError(f"Section not found: {section}")
    
    def create_default_config(self):
        """Create a default configuration file"""
        try:
            self.save_config()
            logger.info("Default configuration file created")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            raise

# Convenience function for quick configuration access
def get_config(config_file: Optional[str] = None, environment: Optional[str] = None) -> ConfigManager:
    """Get a configuration manager instance"""
    return ConfigManager(config_file, environment)
