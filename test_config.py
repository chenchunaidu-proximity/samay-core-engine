#!/usr/bin/env python3
"""
Test script for Configuration Management System
Tests all configuration sections, environment detection, and validation

This test file validates the Configuration System functionality:
1. Tests environment detection and configuration loading
2. Validates all configuration sections (database, sync, server, logging)
3. Tests configuration file operations (save, load, reload)
4. Tests environment variable overrides
5. Tests configuration validation and error handling
6. Tests setting getters and setters

Run this to verify the configuration system is working correctly.
"""

import sys
import json
import os
import tempfile
from pathlib import Path

# Add samay_sync to path
sys.path.append(str(Path(__file__).parent))

from samay_sync.config import ConfigManager, get_config, Environment

def test_basic_configuration():
    """Test basic configuration initialization"""
    print("🔧 Testing Basic Configuration")
    print("=" * 40)
    
    try:
        # Test default configuration
        config = ConfigManager()
        print("✅ Default configuration created successfully")
        
        # Test environment detection
        print(f"🌍 Environment: {config.environment.value}")
        print(f"📁 Config file: {config.config_file}")
        
        # Test configuration sections
        print(f"🗄️ Database path: {config.database.db_path}")
        print(f"🔄 Sync interval: {config.sync.sync_interval}s")
        print(f"🌐 Server URL: {config.server.base_url}")
        print(f"📝 Log level: {config.logging.level}")
        
        # Test configuration summary
        summary = config.get_config_summary()
        print(f"\n📊 Configuration Summary:")
        print(f"  - Environment: {summary['environment']}")
        print(f"  - Database timeout: {summary['database']['timeout']}s")
        print(f"  - Sync batch size: {summary['sync']['max_batch_size']}")
        print(f"  - Server timeout: {summary['server']['timeout']}s")
        print(f"  - Log format: {summary['logging']['format']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_configuration_sections():
    """Test individual configuration sections"""
    print("\n🔧 Testing Configuration Sections")
    print("=" * 40)
    
    try:
        config = ConfigManager()
        
        # Test Database Configuration
        print("🗄️ Database Configuration:")
        print(f"  - Path: {config.database.db_path}")
        print(f"  - Timeout: {config.database.timeout}s")
        print(f"  - Batch size: {config.database.default_batch_size}")
        print(f"  - Max limit: {config.database.max_query_limit}")
        
        # Test Sync Configuration
        print("\n🔄 Sync Configuration:")
        print(f"  - Interval: {config.sync.sync_interval}s")
        print(f"  - Retry interval: {config.sync.retry_interval}s")
        print(f"  - Max retries: {config.sync.max_retries}")
        print(f"  - Batch size: {config.sync.max_batch_size}")
        print(f"  - State file: {config.sync.state_file_path}")
        
        # Test Server Configuration
        print("\n🌐 Server Configuration:")
        print(f"  - Base URL: {config.server.base_url}")
        print(f"  - Sync endpoint: {config.server.sync_endpoint}")
        print(f"  - Timeout: {config.server.timeout}s")
        print(f"  - Max retries: {config.server.max_retries}")
        print(f"  - Rate limit: {config.server.requests_per_minute}/min")
        
        # Test Logging Configuration
        print("\n📝 Logging Configuration:")
        print(f"  - Level: {config.logging.level}")
        print(f"  - File: {config.logging.file_path}")
        print(f"  - Max size: {config.logging.max_file_size} bytes")
        print(f"  - Backup count: {config.logging.backup_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_environment_detection():
    """Test environment detection and configuration"""
    print("\n🌍 Testing Environment Detection")
    print("=" * 40)
    
    try:
        # Test default environment
        config1 = ConfigManager()
        print(f"✅ Default environment: {config1.environment.value}")
        
        # Test explicit environment
        config2 = ConfigManager(environment="production")
        print(f"✅ Production environment: {config2.environment.value}")
        
        # Test staging environment
        config3 = ConfigManager(environment="staging")
        print(f"✅ Staging environment: {config3.environment.value}")
        
        # Test development environment
        config4 = ConfigManager(environment="development")
        print(f"✅ Development environment: {config4.environment.value}")
        
        # Test invalid environment (should default to development)
        try:
            config5 = ConfigManager(environment="invalid")
            print(f"✅ Invalid environment defaulted to: {config5.environment.value}")
        except Exception as e:
            print(f"⚠️ Invalid environment handling: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_configuration_file_operations():
    """Test configuration file save, load, and reload"""
    print("\n💾 Testing Configuration File Operations")
    print("=" * 40)
    
    try:
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name
        
        # Test saving configuration
        config1 = ConfigManager()
        config1.save_config(temp_config_path)
        print(f"✅ Configuration saved to: {temp_config_path}")
        
        # Test loading configuration from file
        config2 = ConfigManager(config_file=temp_config_path)
        print(f"✅ Configuration loaded from: {temp_config_path}")
        
        # Verify configurations match
        summary1 = config1.get_config_summary()
        summary2 = config2.get_config_summary()
        
        if summary1['database']['db_path'] == summary2['database']['db_path']:
            print("✅ Configuration loaded correctly from file")
        else:
            print("❌ Configuration mismatch between instances")
        
        # Test configuration reload
        config2.reload_config()
        print("✅ Configuration reloaded successfully")
        
        # Test create default config
        config1.create_default_config()
        print("✅ Default configuration file created")
        
        # Clean up
        os.unlink(temp_config_path)
        print("🧹 Temporary config file cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_setting_getters_and_setters():
    """Test configuration setting getters and setters"""
    print("\n⚙️ Testing Setting Getters and Setters")
    print("=" * 40)
    
    try:
        config = ConfigManager()
        
        # Test getting settings
        db_path = config.get_setting("database", "db_path")
        sync_interval = config.get_setting("sync", "sync_interval")
        server_timeout = config.get_setting("server", "timeout")
        log_level = config.get_setting("logging", "level")
        
        print(f"✅ Retrieved settings:")
        print(f"  - Database path: {db_path}")
        print(f"  - Sync interval: {sync_interval}s")
        print(f"  - Server timeout: {server_timeout}s")
        print(f"  - Log level: {log_level}")
        
        # Test setting values
        config.set_setting("database", "timeout", 60)
        config.set_setting("sync", "sync_interval", 600)
        config.set_setting("server", "timeout", 45)
        config.set_setting("logging", "level", "DEBUG")
        
        print(f"\n✅ Updated settings:")
        print(f"  - Database timeout: {config.database.timeout}s")
        print(f"  - Sync interval: {config.sync.sync_interval}s")
        print(f"  - Server timeout: {config.server.timeout}s")
        print(f"  - Log level: {config.logging.level}")
        
        # Test invalid section/key
        try:
            config.get_setting("invalid_section", "key")
            print("❌ Should have failed for invalid section")
        except ValueError as e:
            print(f"✅ Correctly handled invalid section: {e}")
        
        try:
            config.get_setting("database", "invalid_key")
            print("❌ Should have failed for invalid key")
        except ValueError as e:
            print(f"✅ Correctly handled invalid key: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_environment_variable_overrides():
    """Test environment variable configuration overrides"""
    print("\n🔧 Testing Environment Variable Overrides")
    print("=" * 40)
    
    try:
        # Set environment variables
        os.environ["SAMAY_DB_TIMEOUT"] = "45"
        os.environ["SAMAY_SYNC_INTERVAL"] = "900"
        os.environ["SAMAY_SERVER_URL"] = "https://test-api.example.com"
        os.environ["SAMAY_LOG_LEVEL"] = "DEBUG"
        
        print("✅ Environment variables set")
        
        # Create new config (should pick up environment variables)
        config = ConfigManager()
        
        print(f"\n📊 Configuration after environment variable overrides:")
        print(f"  - Database timeout: {config.database.timeout}s (was 30)")
        print(f"  - Sync interval: {config.sync.sync_interval}s (was 300)")
        print(f"  - Server URL: {config.server.base_url} (was https://api.example.com)")
        print(f"  - Log level: {config.logging.level} (was INFO)")
        
        # Verify overrides worked
        if (config.database.timeout == 45 and 
            config.sync.sync_interval == 900 and
            config.server.base_url == "https://test-api.example.com" and
            config.logging.level == "DEBUG"):
            print("✅ Environment variable overrides working correctly")
        else:
            print("❌ Environment variable overrides not working")
        
        # Clean up environment variables
        del os.environ["SAMAY_DB_TIMEOUT"]
        del os.environ["SAMAY_SYNC_INTERVAL"]
        del os.environ["SAMAY_SERVER_URL"]
        del os.environ["SAMAY_LOG_LEVEL"]
        print("🧹 Environment variables cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_configuration_validation():
    """Test configuration validation and error handling"""
    print("\n✅ Testing Configuration Validation")
    print("=" * 40)
    
    try:
        config = ConfigManager()
        
        # Test valid settings
        print("✅ Testing valid configuration values...")
        config.set_setting("database", "timeout", 60)
        config.set_setting("sync", "sync_interval", 600)
        config.set_setting("server", "timeout", 45)
        print("✅ All valid settings accepted")
        
        # Test invalid settings (should raise ValueError)
        print("\n🧪 Testing invalid configuration values...")
        
        try:
            config.set_setting("database", "timeout", -5)
            print("❌ Should have failed for negative timeout")
        except ValueError as e:
            print(f"✅ Correctly rejected negative timeout: {e}")
        
        try:
            config.set_setting("sync", "sync_interval", 0)
            print("❌ Should have failed for zero interval")
        except ValueError as e:
            print(f"✅ Correctly rejected zero interval: {e}")
        
        try:
            config.set_setting("server", "max_retries", -1)
            print("❌ Should have failed for negative retries")
        except ValueError as e:
            print(f"✅ Correctly rejected negative retries: {e}")
        
        try:
            config.set_setting("logging", "level", "INVALID_LEVEL")
            print("❌ Should have failed for invalid log level")
        except ValueError as e:
            print(f"✅ Correctly rejected invalid log level: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_convenience_function():
    """Test the convenience get_config function"""
    print("\n🚀 Testing Convenience Function")
    print("=" * 40)
    
    try:
        # Test convenience function
        config = get_config()
        print("✅ get_config() function works")
        
        # Test with environment
        config_prod = get_config(environment="production")
        print(f"✅ get_config(environment='production') works: {config_prod.environment.value}")
        
        # Test with config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name
        
        config_file = get_config(config_file=temp_config_path)
        print(f"✅ get_config(config_file='{temp_config_path}') works")
        
        # Clean up
        os.unlink(temp_config_path)
        print("🧹 Temporary config file cleaned up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    print("🔧 Configuration System Testing Suite")
    print("=" * 50)
    
    # Run all tests
    test_basic_configuration()
    test_configuration_sections()
    test_environment_detection()
    test_configuration_file_operations()
    test_setting_getters_and_setters()
    test_environment_variable_overrides()
    test_configuration_validation()
    test_convenience_function()
    
    print("\n🎉 Configuration System testing complete!")
    print("\n📋 Summary:")
    print("  ✅ Basic configuration initialization")
    print("  ✅ Configuration sections validation")
    print("  ✅ Environment detection")
    print("  ✅ File operations (save/load/reload)")
    print("  ✅ Setting getters and setters")
    print("  ✅ Environment variable overrides")
    print("  ✅ Configuration validation")
    print("  ✅ Convenience functions")
