#!/usr/bin/env python3
"""
Test suite for Sync Manager
Tests the main synchronization orchestration module
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync.sync_manager import SyncManager, SyncResult, SyncStats, APIClient
from config.sync_config import get_config


class TestAPIClient(unittest.TestCase):
    """Test API client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_client = APIClient("https://api.example.com", "test_token")
    
    def test_api_client_initialization(self):
        """Test API client initialization"""
        self.assertEqual(self.api_client.base_url, "https://api.example.com")
        self.assertEqual(self.api_client.access_token, "test_token")
        self.assertIsNone(self.api_client.session)
    
    @unittest.skip("Requires requests library")
    @patch('sync.sync_manager.requests.Session')
    def test_send_events_success(self, mock_session_class):
        """Test successful event sending"""
        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test data
        events = [
            {'id': 1, 'timestamp': '2025-01-01T00:00:00Z', 'data': {'app': 'test'}}
        ]
        
        # Send events
        success, message = self.api_client.send_events(events)
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(message, "Events sent successfully")
        mock_session.post.assert_called_once()
    
    @unittest.skip("Requires requests library")
    @patch('sync.sync_manager.requests.Session')
    def test_send_events_auth_failure(self, mock_session_class):
        """Test authentication failure"""
        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test data
        events = [{'id': 1, 'timestamp': '2025-01-01T00:00:00Z'}]
        
        # Send events
        success, message = self.api_client.send_events(events)
        
        # Verify
        self.assertFalse(success)
        self.assertEqual(message, "Authentication failed - token expired")
    
    def test_send_events_no_requests(self):
        """Test behavior when requests library is not available"""
        # Test data
        events = [{'id': 1, 'timestamp': '2025-01-01T00:00:00Z'}]
        
        # Mock ImportError
        with patch('builtins.__import__', side_effect=ImportError):
            success, message = self.api_client.send_events(events)
            
            self.assertFalse(success)
            self.assertIn("requests library required", message)


class TestSyncResult(unittest.TestCase):
    """Test SyncResult dataclass"""
    
    def test_sync_result_creation(self):
        """Test SyncResult creation"""
        result = SyncResult(
            success=True,
            events_synced=10,
            buckets_synced=2,
            errors=[],
            timestamp="2025-01-01T00:00:00Z",
            duration_seconds=5.5
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.events_synced, 10)
        self.assertEqual(result.buckets_synced, 2)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.duration_seconds, 5.5)


class TestSyncStats(unittest.TestCase):
    """Test SyncStats dataclass"""
    
    def test_sync_stats_creation(self):
        """Test SyncStats creation"""
        stats = SyncStats(
            total_syncs=5,
            successful_syncs=4,
            failed_syncs=1,
            total_events_synced=100,
            last_sync_time="2025-01-01T00:00:00Z",
            average_sync_duration=3.2
        )
        
        self.assertEqual(stats.total_syncs, 5)
        self.assertEqual(stats.successful_syncs, 4)
        self.assertEqual(stats.failed_syncs, 1)
        self.assertEqual(stats.total_events_synced, 100)
        self.assertEqual(stats.average_sync_duration, 3.2)


class TestSyncManager(unittest.TestCase):
    """Test SyncManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Set environment variables for testing
        os.environ["SAMAY_OAUTH_CLIENT_ID"] = "test_client"
        os.environ["SAMAY_OAUTH_CLIENT_SECRET"] = "test_secret"
        
        # Mock the modules
        self.mock_db_module = Mock()
        self.mock_sync_state_manager = Mock()
        self.mock_oauth_manager = Mock()
        
        # Create SyncManager with mocked dependencies
        with patch('sync.sync_manager.DatabaseModule', return_value=self.mock_db_module), \
             patch('sync.sync_manager.SyncStateManager', return_value=self.mock_sync_state_manager), \
             patch('sync.sync_manager.OAuthManager', return_value=self.mock_oauth_manager):
            
            self.sync_manager = SyncManager()
    
    def test_sync_manager_initialization(self):
        """Test SyncManager initialization"""
        self.assertIsNotNone(self.sync_manager.config)
        self.assertIsNotNone(self.sync_manager.db_module)
        self.assertIsNotNone(self.sync_manager.sync_state_manager)
        self.assertIsNotNone(self.sync_manager.oauth_manager)
        self.assertIsNone(self.sync_manager.api_client)
    
    def test_ensure_authenticated_not_authenticated(self):
        """Test authentication check when not authenticated"""
        self.mock_oauth_manager.is_authenticated.return_value = False
        
        result = self.sync_manager._ensure_authenticated()
        
        self.assertFalse(result)
        self.mock_oauth_manager.is_authenticated.assert_called_once()
    
    def test_ensure_authenticated_success(self):
        """Test successful authentication"""
        self.mock_oauth_manager.is_authenticated.return_value = True
        self.mock_oauth_manager.token_storage.load_tokens.return_value = {
            'access_token': 'test_token'
        }
        
        result = self.sync_manager._ensure_authenticated()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.sync_manager.api_client)
    
    def test_update_sync_stats_success(self):
        """Test sync statistics update for successful sync"""
        initial_stats = self.sync_manager._sync_stats
        
        self.sync_manager._update_sync_stats(True, 10, 2.5)
        
        self.assertEqual(self.sync_manager._sync_stats.total_syncs, 1)
        self.assertEqual(self.sync_manager._sync_stats.successful_syncs, 1)
        self.assertEqual(self.sync_manager._sync_stats.total_events_synced, 10)
        self.assertEqual(self.sync_manager._sync_stats.average_sync_duration, 2.5)
    
    def test_update_sync_stats_failure(self):
        """Test sync statistics update for failed sync"""
        self.sync_manager._update_sync_stats(False, 0, 1.0)
        
        self.assertEqual(self.sync_manager._sync_stats.total_syncs, 1)
        self.assertEqual(self.sync_manager._sync_stats.successful_syncs, 0)
        self.assertEqual(self.sync_manager._sync_stats.failed_syncs, 1)
        self.assertEqual(self.sync_manager._sync_stats.total_events_synced, 0)
    
    def test_get_status(self):
        """Test status retrieval"""
        self.mock_oauth_manager.is_authenticated.return_value = True
        
        status = self.sync_manager.get_status()
        
        self.assertIn('auto_sync_running', status)
        self.assertIn('authenticated', status)
        self.assertIn('stats', status)
        self.assertIn('config', status)
        self.assertTrue(status['authenticated'])
    
    @patch('sync.sync_manager.APIClient')
    def test_sync_all_buckets_not_authenticated(self, mock_api_client):
        """Test sync when not authenticated"""
        self.mock_oauth_manager.is_authenticated.return_value = False
        
        result = self.sync_manager.sync_all_buckets()
        
        self.assertFalse(result.success)
        self.assertEqual(result.events_synced, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Authentication required", result.errors[0])
    
    @patch('sync.sync_manager.APIClient')
    def test_sync_all_buckets_success(self, mock_api_client_class):
        """Test successful sync of all buckets"""
        # Mock authentication
        self.mock_oauth_manager.is_authenticated.return_value = True
        self.mock_oauth_manager.token_storage.load_tokens.return_value = {
            'access_token': 'test_token'
        }
        
        # Mock database
        mock_buckets = [{'id': 'test-bucket'}]
        self.mock_db_module.get_buckets.return_value = mock_buckets
        
        # Mock context manager
        self.mock_db_module.__enter__ = Mock(return_value=self.mock_db_module)
        self.mock_db_module.__exit__ = Mock(return_value=None)
        
        # Mock sync state manager
        mock_events = [
            {'id': 1, 'timestamp': '2025-01-01T00:00:00Z', 'duration': 10, 'data': {'app': 'test'}}
        ]
        self.mock_sync_state_manager.get_events_since_last_sync.return_value = mock_events
        
        # Mock API client
        mock_api_client = Mock()
        mock_api_client.send_events.return_value = (True, "Success")
        mock_api_client_class.return_value = mock_api_client
        
        # Perform sync
        with self.mock_db_module:
            result = self.sync_manager.sync_all_buckets()
        
        # Verify
        self.assertTrue(result.success)
        self.assertEqual(result.events_synced, 1)
        self.assertEqual(result.buckets_synced, 1)
        self.assertEqual(len(result.errors), 0)


class TestSyncManagerIntegration(unittest.TestCase):
    """Integration tests for SyncManager"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        os.environ["SAMAY_OAUTH_CLIENT_ID"] = "test_client"
        os.environ["SAMAY_OAUTH_CLIENT_SECRET"] = "test_secret"
    
    def test_sync_manager_with_real_config(self):
        """Test SyncManager with real configuration"""
        try:
            sync_manager = SyncManager()
            
            # Test basic initialization
            self.assertIsNotNone(sync_manager.config)
            self.assertIsNotNone(sync_manager.db_module)
            self.assertIsNotNone(sync_manager.sync_state_manager)
            self.assertIsNotNone(sync_manager.oauth_manager)
            
            # Test status
            status = sync_manager.get_status()
            self.assertIn('auto_sync_running', status)
            self.assertIn('authenticated', status)
            
        except Exception as e:
            self.fail(f"SyncManager initialization failed: {e}")


if __name__ == '__main__':
    # Set up test environment
    os.environ.setdefault("SAMAY_OAUTH_CLIENT_ID", "test_client")
    os.environ.setdefault("SAMAY_OAUTH_CLIENT_SECRET", "test_secret")
    
    # Run tests
    unittest.main(verbosity=2)
