#!/usr/bin/env python3
"""
Test script for Samay Sync tray integration (Core functionality only).

This script tests the core functionality without requiring PyQt6,
focusing on the integration logic and configuration.
"""

import os
import sys
import logging
from pathlib import Path

# Add samay-sync to path
script_dir = os.path.dirname(os.path.abspath(__file__))
samay_sync_dir = os.path.dirname(script_dir)
sys.path.insert(0, samay_sync_dir)

def test_core_imports():
    """Test that core samay-sync modules can be imported."""
    print("🧪 Testing core samay-sync imports...")
    
    try:
        # Test samay-sync core imports
        from config.sync_config import Config
        print("✅ Configuration module imported successfully")
        
        from auth.oauth_manager import OAuthManager
        print("✅ OAuth Manager imported successfully")
        
        from sync.sync_manager import SyncManager
        print("✅ Sync Manager imported successfully")
        
        from sync.database_module import DatabaseModule
        print("✅ Database Module imported successfully")
        
        from sync.state_manager import SyncStateManager
        print("✅ Sync State Manager imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_config_initialization():
    """Test that configuration can be initialized."""
    print("\n🧪 Testing configuration initialization...")
    
    try:
        from config.sync_config import Config
        
        # Set required environment variables for testing
        os.environ['SAMAY_OAUTH_CLIENT_ID'] = 'test_client'
        os.environ['SAMAY_OAUTH_CLIENT_SECRET'] = 'test_secret'
        
        config = Config()
        print(f"✅ Configuration initialized successfully")
        print(f"   - OAuth Client ID: {config.oauth.client_id}")
        print(f"   - Database Path: {config.database.db_path}")
        print(f"   - Sync Interval: {config.sync.sync_interval}s")
        print(f"   - Backend URL: {config.server.base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_tray_integration_logic():
    """Test the tray integration logic without PyQt6."""
    print("\n🧪 Testing tray integration logic...")
    
    try:
        from config.sync_config import Config
        from auth.oauth_manager import OAuthManager
        from sync.sync_manager import SyncManager
        
        # Set required environment variables
        os.environ['SAMAY_OAUTH_CLIENT_ID'] = 'test_client'
        os.environ['SAMAY_OAUTH_CLIENT_SECRET'] = 'test_secret'
        
        # Initialize components
        config = Config()
        oauth_manager = OAuthManager()
        sync_manager = SyncManager()
        
        print("✅ All components initialized successfully")
        
        # Test authentication status check
        is_authenticated = oauth_manager.is_authenticated()
        print(f"✅ Authentication status check: {is_authenticated}")
        
        # Test sync manager status
        stats = sync_manager.get_sync_stats()
        print(f"✅ Sync statistics retrieved: {type(stats).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tray integration logic error: {e}")
        return False


def test_aw_qt_integration_syntax():
    """Test that aw-qt integration code is syntactically correct."""
    print("\n🧪 Testing aw-qt integration syntax...")
    
    try:
        # Read the modified trayicon.py file and check for syntax errors
        aw_qt_path = os.path.join(samay_sync_dir, '..', 'aw-qt', 'aw_qt', 'trayicon.py')
        
        if not os.path.exists(aw_qt_path):
            print(f"❌ aw-qt trayicon.py not found at: {aw_qt_path}")
            return False
        
        # Check if our integration code is present
        with open(aw_qt_path, 'r') as f:
            content = f.read()
        
        # Check for our integration markers
        if 'SAMAY_SYNC_AVAILABLE' in content:
            print("✅ SAMAY_SYNC_AVAILABLE flag found")
        else:
            print("❌ SAMAY_SYNC_AVAILABLE flag not found")
            return False
        
        if 'samay_sync_integration' in content:
            print("✅ Samay Sync integration code found")
        else:
            print("❌ Samay Sync integration code not found")
            return False
        
        if 'create_samay_sync_integration' in content:
            print("✅ Samay Sync integration function found")
        else:
            print("❌ Samay Sync integration function not found")
            return False
        
        # Test Python syntax
        import ast
        try:
            ast.parse(content)
            print("✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"❌ Python syntax error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ aw-qt integration syntax error: {e}")
        return False


def test_tray_integration_file_structure():
    """Test that all required files exist."""
    print("\n🧪 Testing file structure...")
    
    try:
        # Check required files
        required_files = [
            'ui/__init__.py',
            'ui/tray_integration.py',
            'config/sync_config.py',
            'auth/oauth_manager.py',
            'sync/sync_manager.py',
            'sync/database_module.py',
            'sync/state_manager.py',
        ]
        
        for file_path in required_files:
            full_path = os.path.join(samay_sync_dir, file_path)
            if os.path.exists(full_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ File structure error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Samay Sync Tray Integration Tests (Core Functionality)\n")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        test_core_imports,
        test_config_initialization,
        test_tray_integration_logic,
        test_aw_qt_integration_syntax,
        test_tray_integration_file_structure,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core tests passed! Tray integration is ready.")
        print("\n📝 Note: PyQt6 integration will be tested when aw-qt is running.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
